from __future__ import annotations

import json
import base64
import csv
import io
import os
import signal
import subprocess
import sys
import threading
import time
import uuid
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse
from flask import Blueprint, request, jsonify

ROOT = Path(__file__).resolve().parent
RUNS_DIR = ROOT / "runs"
RUNS_DIR.mkdir(exist_ok=True)
JOBS = {}
BATCHES = {}
LOCK = threading.Lock()


def persist_batch(batch_id):
    """Write a batch snapshot so progress survives process restarts."""
    with LOCK:
        snapshot = dict(BATCHES.get(batch_id, {}))
        snapshot.pop("process", None)
    target = RUNS_DIR / f"{batch_id}.json"
    temp = target.with_suffix(".tmp")
    temp.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2), encoding="utf-8")
    temp.replace(target)


def load_batches():
    for path in RUNS_DIR.glob("*.json"):
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
            if path.stem and isinstance(value, dict):
                if value.get("running"):
                    value["running"] = False
                    value["success"] = False
                    value["output"] = (value.get("output", "") + "\n[BATCH] 服务重启，未完成的批次已标记为中断。\n")
                value["success_count"] = sum(1 for item in value.get("results", []) if item.get("success"))
                value["failed_count"] = sum(1 for item in value.get("results", []) if not item.get("success"))
                BATCHES[path.stem] = value
        except (OSError, ValueError):
            continue


load_batches()


def safe_path(name):
    target = (ROOT / name).resolve()
    allowed = [(ROOT / "examples").resolve(), (ROOT / "scripts").resolve()]
    if target.suffix != ".js" or not any(folder == target.parent or folder in target.parents for folder in allowed):
        raise ValueError("Only GEE JavaScript files in examples/ or scripts/ are allowed.")
    return target


def files():
    result = []
    for folder_name in ("examples", "scripts"):
        folder = ROOT / folder_name
        if folder.exists():
            result += [str(p.relative_to(ROOT)).replace(chr(92), "/") for p in folder.rglob("*.js")]
    return sorted(result)


def _decode_file(encoded):
    return base64.b64decode(encoded).decode("utf-8-sig")


def analyze_file(filename, encoded):
    """Return selectable CSV columns or JSON paths containing GEE code."""
    raw = _decode_file(encoded)
    if filename.lower().endswith(".csv"):
        reader = csv.DictReader(io.StringIO(raw))
        headers = reader.fieldnames or []
        rows = list(reader)
        candidates = []
        for header in headers:
            values = [str(row.get(header) or "") for row in rows]
            candidates.append({"id": header, "label": header, "hasCode": any("ee." in value for value in values), "samples": [v[:120] for v in values if v.strip()][:2]})
        return {"kind": "csv", "identifiers": candidates, "columns": headers, "rows": len(rows)}
    if filename.lower().endswith(".json"):
        data = json.loads(raw)
        found = {}
        def walk(value, path=""):
            if isinstance(value, dict):
                for key, child in value.items():
                    child_path = f"{path}.{key}" if path else key
                    if isinstance(child, str) and "ee." in child:
                        found.setdefault(child_path, []).append(child[:120])
                    else:
                        walk(child, child_path)
            elif isinstance(value, list):
                for index, child in enumerate(value):
                    walk(child, f"{path}[{index}]" if path else f"[{index}]")
        walk(data)
        normalized = {}
        for key, values in found.items():
            wildcard = __import__("re").sub(r"\[\d+\]", "[]", key)
            normalized.setdefault(wildcard, []).extend(values)
        identifiers = [{"id": key, "label": key, "samples": values[:2]} for key, values in normalized.items()]
        return {"kind": "json", "identifiers": identifiers}
    raise ValueError("仅支持 .json 和 .csv 文件。")


def extract_codes(filename, encoded, identifier, mode="rows"):
    if not identifier.strip():
        raise ValueError("请选择标识符（先分析文件）。")
    raw = _decode_file(encoded)
    is_csv = filename.lower().endswith(".csv")
    if is_csv:
        # CSV 是扁平表格：identifier 必须是精确的列名，每一行代表一个实例。
        reader = csv.DictReader(io.StringIO(raw))
        headers = reader.fieldnames or []
        if identifier not in headers:
            raise ValueError(f"CSV 中不存在列 '{identifier}'。可用列：{', '.join(headers) or '（无表头）'}")
        records = list(reader)
        if mode == "columns":
            value = "\n".join(str(row.get(identifier) or "") for row in records).strip()
            records = [{identifier: value}]
    elif filename.lower().endswith(".json"):
        data = json.loads(raw)
        records = [data]
    else:
        raise ValueError("仅支持 .json 和 .csv 文件。")

    def field(row):
        if is_csv:
            return row.get(identifier) if isinstance(row, dict) else None
        def resolve(value, parts):
            if not parts:
                return [value]
            part, rest = parts[0], parts[1:]
            if part == "[]":
                if not isinstance(value, list):
                    return []
                result = []
                for item in value:
                    result.extend(resolve(item, rest))
                return result
            if not isinstance(value, dict) or part not in value:
                return []
            return resolve(value[part], rest)
        parts = [part for segment in identifier.split(".") for part in ((["[]"] if segment == "[]" else [segment[:-2], "[]"] if segment.endswith("[]") else [segment]))]
        values = resolve(row, parts)
        return values if len(values) != 1 else values[0]

    codes = []
    skipped_empty = 0
    skipped_non_gee = 0
    for index, row in enumerate(records, 1):
        value = field(row)
        values = value if isinstance(value, list) else [value]
        for offset, item in enumerate(values):
            if not isinstance(item, str) or not item.strip():
                skipped_empty += 1
            elif "ee." in item:
                codes.append({"row": index if len(values) == 1 else f"{index}.{offset + 1}", "source": item})
            else:
                skipped_non_gee += 1
    if not codes:
        raise ValueError(f"未找到标识符 '{identifier}' 中的 GEE 代码（代码必须包含 ee.）。")
    return codes, {"skippedEmpty": skipped_empty, "skippedNonGee": skipped_non_gee, "total": len(records)}


def batch_worker(batch_id, codes, fixes, start_index=0, reset_results=False):
    results = []
    if reset_results:
        stop_after_failure = False
        with LOCK:
            BATCHES[batch_id]["results"] = []
            BATCHES[batch_id]["completed"] = 0
            BATCHES[batch_id]["success_count"] = 0
            BATCHES[batch_id]["failed_count"] = 0
        persist_batch(batch_id)
    for index in range(start_index, len(codes)):
        number, item = index + 1, codes[index]
        with LOCK:
            batch = BATCHES[batch_id]
            prior = next((entry for entry in batch.get("results", []) if entry.get("row") == item["row"]), None)
            if prior and prior.get("success"):
                batch["completed"] = number
                batch["success_count"] = sum(1 for entry in batch.get("results", []) if entry.get("success"))
                batch["failed_count"] = sum(1 for entry in batch.get("results", []) if not entry.get("success"))
                continue
        started = time.strftime("%Y-%m-%d %H:%M:%S")
        with LOCK:
            batch = BATCHES[batch_id]
            if batch.get("stopped"):
                break
            batch["output"] += f"\n[BATCH] {number}/{len(codes)}：开始处理源记录 {item['row']}（{started}）\n"
            batch["current"] = {"number": number, "row": item["row"], "started": started}
        persist_batch(batch_id)
        job_id = uuid.uuid4().hex
        with LOCK:
            JOBS[job_id] = {"running": True, "success": False, "output": "", "code": "", "stopped": False, "process": None}
            BATCHES[batch_id]["currentJob"] = job_id
        persist_batch(batch_id)
        stop_after_failure = False
        worker(job_id, ROOT / "examples" / "gee_script.js", item["source"], fixes, "js")
        with LOCK:
            job = JOBS[job_id]
            finished = time.strftime("%Y-%m-%d %H:%M:%S")
            result = {"row": item["row"], "success": job["success"], "code": job["code"], "output": job["output"], "started": started, "finished": finished}
            results.append(result)
            batch = BATCHES[batch_id]
            outcome = '成功' if job['success'] else '失败'
            batch["output"] += f"[BATCH] {number}/{len(codes)}：{outcome}（源记录 {item['row']}，结束于 {finished}）\n"
            detail = job["output"].strip()
            if detail:
                batch["output"] += f"[BATCH] 源记录 {item['row']} 详细日志：\n{detail[-4000:]}\n"
            if not job["success"] and not job.get("stopped"):
                tail = job["output"].strip().splitlines()[-1:]
                batch["output"] += f"[BATCH] 失败摘要：{' '.join(tail)[:500]}\n"
                batch["stopped"] = True
                batch["output"] += "[BATCH] 当前记录修复失败，已停止批次；请修正代码后重新运行。\n"
                stop_after_failure = True
            existing = [entry for entry in batch.setdefault("results", []) if entry.get("row") != item["row"]]
            existing.append(result)
            batch["results"] = existing
            batch["success_count"] = sum(1 for entry in existing if entry.get("success"))
            batch["failed_count"] = sum(1 for entry in existing if not entry.get("success"))
            # A task stopped by the user was not fully processed; resume it next time.
            if not job.get("stopped"):
                batch["completed"] = number
            batch["current"] = None
            batch["currentJob"] = None
        persist_batch(batch_id)
        if stop_after_failure:
            break
    with LOCK:
        batch = BATCHES[batch_id]
        all_results = batch.get("results", results)
        batch.update(running=False, results=all_results, success=bool(all_results) and len(all_results) == len(codes) and all(item["success"] for item in all_results), finished=time.strftime("%Y-%m-%d %H:%M:%S"), current=None)
    persist_batch(batch_id)


def worker(job_id, script, source, fixes, engine):
    """启动子进程调用 runner.py，实时收集输出并更新任务状态。支持通过 JOBS[job_id]['process'] 终止。"""
    command = [sys.executable, "-u", str(ROOT / "runner.py"), str(script), "--code-stdin", "--wait", "--engine", "js", "--max-fixes", str(fixes)]
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONUTF8"] = "1"
    process = subprocess.Popen(
        command, cwd=ROOT,
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        text=True, encoding="utf-8", errors="replace",
        env=env,
    )
    with LOCK:
        JOBS[job_id]["process"] = process
        JOBS[job_id]["output"] += f"[WORKER] Started PID={process.pid} engine={engine}\n"
    try:
        process.stdin.write(source)
        process.stdin.close()
    except Exception:
        pass
    raw_lines = []
    in_final_code = False
    try:
        for line in process.stdout:
            raw_lines.append(line)
            marker = line.strip()
            if marker == "FINAL_CODE_BEGIN":
                in_final_code = True
                continue
            if marker == "FINAL_CODE_END":
                in_final_code = False
                continue
            if in_final_code:
                continue
            with LOCK:
                JOBS[job_id]["output"] += line
    except (ValueError, OSError, UnicodeDecodeError):
        pass
    code = process.wait()
    with LOCK:
        output = JOBS[job_id]["output"]
        raw_output = "".join(raw_lines)
        begin = raw_output.find("FINAL_CODE_BEGIN")
        end = raw_output.find("FINAL_CODE_END", begin + 1) if begin >= 0 else -1
        final = raw_output[begin + len("FINAL_CODE_BEGIN"):end].lstrip("\r\n") if begin >= 0 and end >= 0 else source
        stopped = JOBS[job_id].get("stopped", False)
        JOBS[job_id].update(
            running=False,
            success=(code == 0 and "SUCCESS" in output) and not stopped,
            code=final,
        )


def stop_job(job_id):
    """终止指定 job 的子进程（包括子进程树中的 node.js 等后代进程）。"""
    with LOCK:
        job = JOBS.get(job_id)
        if not job:
            raise KeyError(f"Job {job_id} not found")
        job["stopped"] = True
        job["output"] += "\n[STOPPED by user]\n"
        process = job.get("process")
    if process and process.poll() is None:
        try:
            if sys.platform == "win32":
                subprocess.run(
                    ["taskkill", "/F", "/T", "/PID", str(process.pid)],
                    capture_output=True, timeout=5,
                )
            else:
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
        except (OSError, subprocess.TimeoutExpired):
            pass


class Handler(SimpleHTTPRequestHandler):
    def json(self, value, status=200):
        data = json.dumps(value, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def body(self):
        return json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))).decode("utf-8"))

    def do_GET(self):
        try:
            query = urlparse(self.path)
            if query.path == "/api/scripts":
                self.json({"scripts": files()})
            elif query.path == "/api/script":
                name = parse_qs(query.query)["path"][0]
                self.json({"code": safe_path(name).read_text(encoding="utf-8")})
            elif query.path == "/api/job":
                job_id = parse_qs(query.query)["id"][0]
                with LOCK:
                    if job_id in JOBS:
                        job = JOBS[job_id]
                        self.json({k: v for k, v in job.items() if k != "process"})
                    else:
                        self.json({"running": False, "success": False, "output": "", "code": "", "engine": "js", "error": "job not found"})
            elif query.path == "/api/batch":
                batch_id = parse_qs(query.query)["id"][0]
                with LOCK:
                    self.json(BATCHES.get(batch_id, {"running": False, "error": "batch not found"}))
            elif query.path == "/api/batch-history":
                with LOCK:
                    history = [{"id": key, "running": value.get("running", False), "success": value.get("success", False), "completed": value.get("completed", 0), "total": value.get("total", 0), "success_count": value.get("success_count", sum(1 for item in value.get("results", []) if item.get("success"))), "failed_count": value.get("failed_count", sum(1 for item in value.get("results", []) if not item.get("success"))), "finished": value.get("finished", "")} for key, value in BATCHES.items()]
                self.json({"batches": sorted(history, key=lambda item: item.get("finished", ""), reverse=True)})
            elif query.path in ("/", "/index.html"):
                self.path = "/web/index.html"
                super().do_GET()
            else:
                super().do_GET()
        except Exception as error:
            self.json({"error": str(error)}, 400)

    def do_POST(self):
        try:
            parsed = urlparse(self.path)
            path = parsed.path
            body = self.body()
            if path == "/api/save":
                safe_path(body["path"]).write_text(body["code"], encoding="utf-8")
                self.json({"ok": True})
                return
            if path == "/api/extract":
                codes, stats = extract_codes(body["filename"], body["content"], body["identifier"], body.get("mode", "rows"))
                self.json({"count": len(codes), "rows": [item["row"] for item in codes[:20]], **stats})
                return
            if path == "/api/analyze":
                self.json(analyze_file(body["filename"], body["content"]))
                return
            if path == "/api/batch":
                codes, stats = extract_codes(body["filename"], body["content"], body["identifier"], body.get("mode", "rows"))
                batch_id = uuid.uuid4().hex
                with LOCK:
                    skipped = stats["skippedEmpty"] + stats["skippedNonGee"]
                    note = f"跳过 {skipped} 行" if skipped else "无跳过行"
                    BATCHES[batch_id] = {"running": True, "success": False, "output": f"[BATCH] 已提取 {len(codes)} 条 GEE 代码（{note}），准备执行。\n", "completed": 0, "success_count": 0, "failed_count": 0, "total": len(codes), "results": [], "items": codes, "stopped": False}
                persist_batch(batch_id)
                threading.Thread(target=batch_worker, args=(batch_id, codes, int(body.get("maxFixes", -1))), daemon=True).start()
                self.json({"batchId": batch_id, "count": len(codes)})
                return
            if path == "/api/batch-rerun":
                batch_id = body["batchId"]
                mode = body.get("mode", "continue")
                with LOCK:
                    batch = BATCHES.get(batch_id)
                    if not batch:
                        raise ValueError("批次不存在")
                    if batch.get("running"):
                        raise ValueError("该批次仍在运行中")
                    codes = batch.get("items", [])
                    if not codes:
                        raise ValueError("该历史批次没有保存源代码，无法重新运行")
                    # Resume always scans from the first source record. Successful
                    # records are skipped; failed and unfinished records are retried.
                    requested_start = body.get("start")
                    if mode == "restart":
                        start = 0
                    elif requested_start is not None:
                        start = max(0, min(int(requested_start) - 1, len(codes)))
                    else:
                        start = 0
                    batch.update(running=True, stopped=False, success=False, output=batch.get("output", "") + f"\n[BATCH] {'从头' if mode == 'restart' else '从前往后扫描，重试失败项'}重新运行。\n")
                persist_batch(batch_id)
                threading.Thread(target=batch_worker, args=(batch_id, codes, int(body.get("maxFixes", -1)), start, mode == "restart"), daemon=True).start()
                self.json({"batchId": batch_id, "start": start + 1})
                return
            if path == "/api/batch-stop":
                batch_id = body["batchId"]
                with LOCK:
                    batch = BATCHES.get(batch_id)
                    if not batch:
                        raise ValueError("批次不存在")
                    batch["stopped"] = True
                    batch["output"] = batch.get("output", "") + "\n[BATCH] 用户请求停止。\n"
                    current_job = batch.get("currentJob")
                persist_batch(batch_id)
                if current_job:
                    stop_job(current_job)
                self.json({"ok": True})
                return
            if path == "/api/run":
                script = safe_path(body["path"])
                source = body.get("code", "")
                engine = body.get("engine", "js")
                if engine not in ("js", "py"):
                    raise ValueError("Engine must be 'js' or 'py'")
                job_id = uuid.uuid4().hex
                fixes = int(body.get("maxFixes", -1))
                with LOCK:
                    JOBS[job_id] = {
                        "running": True,
                        "success": False,
                        "output": "",
                        "code": "",
                        "engine": engine,
                        "stopped": False,
                        "process": None,
                    }
                threading.Thread(
                    target=worker,
                    args=(job_id, script, source, fixes, engine),
                    daemon=True,
                ).start()
                self.json({"jobId": job_id})
                return
            if path == "/api/stop":
                job_id = parse_qs(parsed.query)["id"][0]
                stop_job(job_id)
                self.json({"ok": True})
                return
            raise ValueError("Unknown endpoint")
        except Exception as error:
            self.json({"error": str(error)}, 400)


bp = Blueprint("gee_runner", __name__, url_prefix="/api/gee-runner")


@bp.get("/scripts")
def api_scripts():
    return jsonify({"scripts": files()})


@bp.get("/script")
def api_script():
    try:
        return jsonify({"code": safe_path(request.args["path"]).read_text(encoding="utf-8")})
    except Exception as error:
        return jsonify({"error": str(error)}), 400


@bp.post("/save")
def api_save():
    try:
        data = request.get_json() or {}
        safe_path(data["path"]).write_text(data["code"], encoding="utf-8")
        return jsonify({"ok": True})
    except Exception as error:
        return jsonify({"error": str(error)}), 400


@bp.get("/job")
def api_job():
    with LOCK:
        job = JOBS.get(request.args.get("id"))
        if not job:
            return jsonify({"running": False, "success": False, "output": "", "code": "", "error": "job not found"}), 404
        return jsonify({key: value for key, value in job.items() if key != "process"})


@bp.post("/run")
def api_run():
    try:
        data = request.get_json() or {}
        script = safe_path(data["path"])
        job_id = uuid.uuid4().hex
        with LOCK:
            JOBS[job_id] = {"running": True, "success": False, "output": "", "code": "", "engine": "js", "stopped": False, "process": None}
        threading.Thread(target=worker, args=(job_id, script, data.get("code", ""), int(data.get("maxFixes", -1)), "js"), daemon=True).start()
        return jsonify({"jobId": job_id})
    except Exception as error:
        return jsonify({"error": str(error)}), 400


@bp.post("/stop")
def api_stop():
    try:
        stop_job(request.args["id"])
        return jsonify({"ok": True})
    except Exception as error:
        return jsonify({"error": str(error)}), 400


@bp.post("/analyze")
def api_analyze():
    try:
        data = request.get_json() or {}
        return jsonify(analyze_file(data["filename"], data["content"]))
    except Exception as error:
        return jsonify({"error": str(error)}), 400


@bp.post("/extract")
def api_extract():
    try:
        data = request.get_json() or {}
        codes, stats = extract_codes(data["filename"], data["content"], data["identifier"], data.get("mode", "rows"))
        return jsonify({"count": len(codes), "rows": [item["row"] for item in codes[:20]], "items": codes, **stats})
    except Exception as error:
        return jsonify({"error": str(error)}), 400


@bp.get("/batch")
def api_batch_get():
    with LOCK:
        batch = BATCHES.get(request.args.get("id"))
        if not batch:
            return jsonify({"error": "batch not found"}), 404
        return jsonify(batch)


@bp.post("/batch")
def api_batch_create():
    try:
        data = request.get_json() or {}
        codes, stats = extract_codes(data["filename"], data["content"], data["identifier"], data.get("mode", "rows"))
        batch_id = uuid.uuid4().hex
        with LOCK:
            skipped = stats["skippedEmpty"] + stats["skippedNonGee"]
            BATCHES[batch_id] = {"running": True, "success": False, "output": f"[BATCH] 已提取 {len(codes)} 条 GEE 代码（跳过 {skipped} 行），准备执行。\n", "completed": 0, "success_count": 0, "failed_count": 0, "total": len(codes), "results": [], "items": codes, "stopped": False}
        persist_batch(batch_id)
        threading.Thread(target=batch_worker, args=(batch_id, codes, int(data.get("maxFixes", -1))), daemon=True).start()
        return jsonify({"batchId": batch_id, "count": len(codes)})
    except Exception as error:
        return jsonify({"error": str(error)}), 400


@bp.get("/batch-history")
def api_batch_history():
    with LOCK:
        history = [{"id": key, "running": value.get("running", False), "success": value.get("success", False), "completed": value.get("completed", 0), "total": value.get("total", 0), "success_count": value.get("success_count", sum(1 for item in value.get("results", []) if item.get("success"))), "failed_count": value.get("failed_count", sum(1 for item in value.get("results", []) if not item.get("success"))), "finished": value.get("finished", "")} for key, value in BATCHES.items()]
    return jsonify({"batches": sorted(history, key=lambda item: item.get("finished", ""), reverse=True)})


@bp.post("/batch-rerun")
def api_batch_rerun():
    try:
        data = request.get_json() or {}
        batch_id, mode = data["batchId"], data.get("mode", "continue")
        with LOCK:
            batch = BATCHES.get(batch_id)
            if not batch or batch.get("running"):
                raise ValueError("批次不存在或仍在运行")
            codes = batch.get("items", [])
            if not codes:
                raise ValueError("该历史批次没有保存源代码，无法重新运行")
            start = 0 if mode == "restart" else max(0, min(int(data["start"]) - 1, len(codes))) if data.get("start") else 0
            label = "从头重新运行" if mode == "restart" else "从前往后扫描，重试失败项"
            batch.update(running=True, stopped=False, success=False, output=batch.get("output", "") + f"\n[BATCH] {label}，起点第 {start + 1} 条。\n")
        persist_batch(batch_id)
        threading.Thread(target=batch_worker, args=(batch_id, codes, int(data.get("maxFixes", -1)), start, mode == "restart"), daemon=True).start()
        return jsonify({"batchId": batch_id, "start": start + 1})
    except Exception as error:
        return jsonify({"error": str(error)}), 400


@bp.post("/batch-stop")
def api_batch_stop():
    try:
        data = request.get_json() or {}
        with LOCK:
            batch = BATCHES[data["batchId"]]
            batch["stopped"] = True
            batch["output"] += "\n[BATCH] 用户请求停止。\n"
            job_id = batch.get("currentJob")
        persist_batch(data["batchId"])
        if job_id:
            stop_job(job_id)
        return jsonify({"ok": True})
    except Exception as error:
        return jsonify({"error": str(error)}), 400
