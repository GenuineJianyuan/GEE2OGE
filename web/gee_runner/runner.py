"""Run Google Earth Engine Python scripts with service-account credentials."""

from __future__ import annotations

import argparse
import json
import os
import runpy
import sys
import time
import traceback
import urllib.request
import urllib.error
import socket
import http.client
import random
from pathlib import Path


def load_env(env_file: Path) -> None:
    if not env_file.exists():
        return
    for line in env_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip())


def load_codex_config() -> None:
    """Read the user's Codex-compatible provider config without importing TOML dependencies."""
    config_file = Path(os.environ.get("CODEX_CONFIG_FILE", Path.home() / ".codex" / "config.toml"))
    if config_file.exists():
        section = None
        for raw in config_file.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            if line.startswith("[") and line.endswith("]"):
                section = line[1:-1].strip()
                continue
            if "=" not in line:
                continue
            key, value = (part.strip() for part in line.split("=", 1))
            if value.startswith('"') and value.endswith('"'):
                value = value[1:-1]
            if section == "model_providers.llmapi":
                if key == "base_url":
                    os.environ.setdefault("OPENAI_BASE_URL", value)
                elif key == "model":
                    os.environ.setdefault("OPENAI_MODEL", value)
    auth_file = Path(os.environ.get("CODEX_AUTH_FILE", Path.home() / ".codex" / "auth.json"))
    if auth_file.exists() and not os.environ.get("OPENAI_API_KEY"):
        data = json.loads(auth_file.read_text(encoding="utf-8"))
        key = data.get("OPENAI_API_KEY") or data.get("api_key") or data.get("key")
        if key:
            os.environ["OPENAI_API_KEY"] = key


def initialize(key_file: str):
    import ee

    key_path = Path(key_file).resolve()
    if not key_path.is_file():
        raise FileNotFoundError(f"Service-account key not found: {key_path}")
    key = json.loads(key_path.read_text(encoding="utf-8"))
    service_account = key.get("client_email")
    if not service_account:
        raise ValueError("The key file does not contain client_email.")
    project = os.environ.get("GEE_PROJECT") or key.get("project_id")
    print("Authenticating with Google Earth Engine...")
    ee.Initialize(ee.ServiceAccountCredentials(service_account, str(key_path)), project=project)
    print("Authentication complete. Running script...")
    return ee


def wait_for_tasks(tasks, interval: int) -> None:
    pending = set(tasks)
    terminal = {"COMPLETED", "FAILED", "CANCELLED", "CANCEL_REQUESTED"}
    while pending:
        for task in list(pending):
            status = task.status()
            state = status.get("state", "UNKNOWN")
            detail = status.get("error_message", "")
            print(f"{status.get('id', 'unknown')}: {state}{f' ({detail})' if detail else ''}")
            if state == "FAILED":
                raise RuntimeError(detail or f"Earth Engine task {status.get('id')} failed")
            if state in terminal:
                pending.remove(task)
        if pending:
            time.sleep(interval)


def call_fix_api(source: str, error: str, output_format: str = "py") -> str:
    """调用 AI API 修复/转换 GEE 代码。output_format: 'js' 返回 JavaScript, 'py' 返回 Python。"""
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("Run failed and OPENAI_API_KEY is not configured; cannot auto-fix.")
    model = os.environ.get("OPENAI_MODEL", "gpt-5.4")
    if output_format == "js":
        prompt = (
            "You are preparing a Google Earth Engine JavaScript script for server execution. Return ONLY complete corrected GEE JavaScript code (the same API style as the Earth Engine Code Editor), with no Markdown fences or explanation. Fix bugs and preserve the user's intent and export configuration.\n\n"
            f"Error:\n{error}\n\nCurrent script:\n{source}"
        )
    else:
        prompt = (
            "You are preparing a Google Earth Engine script for server execution. Return ONLY complete corrected Python Earth Engine API source code, with no Markdown fences or explanation. The input may be JavaScript from the Earth Engine Code Editor; if it is JavaScript, convert it to equivalent Python API code. Preserve the user's intent and export configuration.\n\n"
            f"Error:\n{error}\n\nCurrent script:\n{source}"
        )
    base_url = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com").rstrip("/")
    if not base_url.endswith("/v1"):
        base_url += "/v1"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json", "User-Agent": "gee-runner/1.0", "Connection": "close"}
    attempts = [("responses", {"model": model, "input": prompt, "max_output_tokens": 12000}), ("chat/completions", {"model": model, "messages": [{"role": "user", "content": prompt}], "max_tokens": 12000})]
    failures = []
    result = None
    transient_retries = max(1, int(os.environ.get("OPENAI_RETRIES", "3")))
    for endpoint, body in attempts:
        for retry in range(transient_retries):
            request = urllib.request.Request(base_url + "/" + endpoint, data=json.dumps(body).encode("utf-8"), headers=headers, method="POST")
            try:
                with urllib.request.urlopen(request, timeout=180) as response:
                    result = json.loads(response.read().decode("utf-8"))
                break
            except urllib.error.HTTPError as error:
                detail = error.read().decode('utf-8', errors='replace')
                transient = error.code in (408, 409, 425, 429, 500, 502, 503, 504) or "stream disconnected" in detail.lower() or "stream closed" in detail.lower()
                failures.append(f"{endpoint}: HTTP {error.code}: {detail}")
                if transient and retry + 1 < transient_retries:
                    delay = min(20, 2 ** retry + random.random())
                    print(f"AI API temporary failure ({error.code}), retrying {retry + 1}/{transient_retries - 1} in {delay:.1f}s...", flush=True)
                    time.sleep(delay)
                    continue
            except (urllib.error.URLError, ConnectionError, TimeoutError, socket.timeout, http.client.HTTPException) as error:
                failures.append(f"{endpoint}: connection error: {error}")
                if retry + 1 < transient_retries:
                    delay = min(20, 2 ** retry + random.random())
                    print(f"AI API connection failure, retrying {retry + 1}/{transient_retries - 1} in {delay:.1f}s...", flush=True)
                    time.sleep(delay)
                    continue
            break
        if result is not None:
            break
    if result is None:
        raise RuntimeError("OpenAI API failed. " + " | ".join(failures))
    text = result.get("output_text") or ""
    if not text and result.get("choices"):
        text = result["choices"][0].get("message", {}).get("content", "")
    if not text:
        for item in result.get("output", []):
            for content in item.get("content", []):
                if content.get("type") == "output_text":
                    text += content.get("text", "")
    if not text:
        raise RuntimeError("OpenAI API returned no corrected source code.")
    if text.startswith("```"):
        text = text.split("\n", 1)[1] if "\n" in text else text
        text = text.rsplit("```", 1)[0]
    return text.strip() + "\n"


def run_once(source: str, filename: str, key_file: str, wait: bool, poll_seconds: int) -> None:
    ee = initialize(key_file)
    submitted = []
    original_start = ee.batch.Task.start

    def start_and_track(task):
        original_start(task)
        submitted.append(task)
        print(f"Export started: {task.status().get('id', 'unknown')}")

    ee.batch.Task.start = start_and_track
    namespace = {"ee": ee, "Export": ee.batch.Export}
    exec(compile(source, filename, "exec"), namespace, namespace)
    if submitted and wait:
        wait_for_tasks(submitted, poll_seconds)


def is_javascript(source: str) -> bool:
    markers = ("//", "var ", "let ", "const ", "function ", "Map.")
    return any(line.lstrip().startswith(markers) for line in source.splitlines() if line.strip())


def _run_js_once(source: str, key_file: str, wait: bool) -> tuple[str, bool, str]:
    """通过子进程执行 JS runner，返回 (最终代码, 是否成功, 输出日志)。"""
    import subprocess as _sp
    root = Path(__file__).resolve().parent
    command = ["node", str(root / "bin" / "gee-js-runner.js")]
    if wait:
        command.append("--wait")
    env = os.environ.copy()
    env["NODE_OPTIONS"] = env.get("NODE_OPTIONS", "")
    env["GEE_PRIVATE_KEY_FILE"] = key_file
    _fix_proxy_env(env)
    process = _sp.Popen(command, cwd=root, stdin=_sp.PIPE, stdout=_sp.PIPE, stderr=_sp.STDOUT, text=True, encoding="utf-8", errors="replace", env=env)
    process.stdin.write(source)
    process.stdin.close()
    all_lines = []
    skip_block = False
    for line in process.stdout:
        stripped = line.strip()
        if stripped == "FINAL_CODE_BEGIN":
            skip_block = True
            all_lines.append(line)
            continue
        if stripped == "FINAL_CODE_END":
            skip_block = False
            all_lines.append(line)
            continue
        all_lines.append(line)
        if not skip_block:
            sys.stdout.write(line)
            sys.stdout.flush()
    code = process.wait()
    raw_output = "".join(all_lines)
    final = raw_output.split("FINAL_CODE_BEGIN\n", 1)[-1].split("\nFINAL_CODE_END", 1)[0] if "FINAL_CODE_BEGIN" in raw_output else source
    log_output = "".join(line for line in all_lines if line.strip() not in ("FINAL_CODE_BEGIN", "FINAL_CODE_END"))
    success = code == 0 and "SUCCESS" in raw_output
    return final, success, log_output


NETWORK_ERROR_PATTERNS = [
    "socket hang up",
    "aborted",
    "ECONNREFUSED",
    "ECONNRESET",
    "ENOTFOUND",
    "network is unreachable",
    "ETIMEDOUT",
    "connection reset",
    "getaddrinfo ENOTFOUND",
    "Invalid JSON: Error:",
    "SELF_SIGNED_CERT",
    "CERT_HAS_EXPIRED",
    "unable to get local issuer certificate",
    "403 Forbidden",
    "502 Bad Gateway",
    "503 Service Unavailable",
    "504 Gateway Timeout",
    "ETIMEDOUT",
    "ESOCKETTIMEDOUT",
    "EPIPE",
    "EAI_AGAIN",
    "ENETUNREACH",
    "WinError 10013",
    "access permissions",
    "request to https://oauth2.googleapis.com failed",
    "request to https://www.googleapis.com failed",
    "google oauth 认证失败",
]


def _is_network_error(output: str) -> bool:
    """判断错误是否为网络连接问题（非代码逻辑错误）。"""
    lower = output.lower()
    return any(p.lower() in lower for p in NETWORK_ERROR_PATTERNS)


def _detect_windows_proxy() -> str | None:
    """检测 Windows 系统代理设置，返回代理 URL 或 None。"""
    if sys.platform != "win32":
        return None
    try:
        import winreg
        key_path = r"Software\Microsoft\Windows\CurrentVersion\Internet Settings"
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path) as key:
            enabled, _ = winreg.QueryValueEx(key, "ProxyEnable")
            if not enabled:
                return None
            server, _ = winreg.QueryValueEx(key, "ProxyServer")
            if server:
                if not server.startswith(("http://", "https://", "socks://", "socks5://")):
                    server = f"http://{server}"
                return server
    except Exception:
        pass
    return None


def _fix_proxy_env(env: dict) -> None:
    """检查并修复代理环境变量：优先使用用户配置，其次自动检测 Windows 系统代理。"""
    proxy_keys = [k for k in ("HTTPS_PROXY", "HTTP_PROXY", "ALL_PROXY", "http_proxy", "https_proxy", "all_proxy") if k in env]
    proxy_url = None
    if proxy_keys:
        proxy_url = env.get("HTTPS_PROXY") or env.get("https_proxy") or env.get("HTTP_PROXY") or env.get("http_proxy", "")
    if not proxy_url:
        detected = _detect_windows_proxy()
        if detected:
            proxy_url = detected
            env["HTTPS_PROXY"] = proxy_url
            env["HTTP_PROXY"] = proxy_url
            print(f"[PROXY] Auto-detected Windows system proxy: {proxy_url}", flush=True)
    if not proxy_url:
        print("[PROXY] No proxy configured.", flush=True)
        return
    try:
        from urllib.parse import urlparse as _urlparse
        parsed = _urlparse(proxy_url)
        host = parsed.hostname
        port = parsed.port or (443 if parsed.scheme == "https" else 80)
        if host and port:
            import socket as _socket
            sock = _socket.create_connection((host, port), timeout=2)
            sock.close()
            print(f"[PROXY] Proxy {proxy_url} is reachable.", flush=True)
            return
    except Exception:
        pass
    print(f"[PROXY] WARNING: Proxy {proxy_url} appears unreachable, but keeping proxy settings as configured.", flush=True)
    print(f"[PROXY] If GEE requests fail, ensure your proxy is running or update {proxy_url} in .env", flush=True)


def run_js_engine(source: str, key_file: str, wait: bool, max_fixes: int) -> str:
    """通过 Node.js @google/earthengine JS SDK 运行 GEE JavaScript 代码，支持自动修复。"""
    attempt = 0
    seen_sources = {source}
    unlimited_fix_limit = 12
    while True:
        attempt += 1
        limit_label = "until success or stopped" if max_fixes < 0 else str(max_fixes + 1)
        print(f"\n=== JS engine attempt {attempt}/{limit_label} ===", flush=True)
        final, success, output_text = _run_js_once(source, key_file, wait)
        if success:
            print("SUCCESS")
            return final
        error_msg = f"JS engine failed:\n{output_text}"
        print(f"\nRUN FAILED (attempt {attempt}/{limit_label})", flush=True)
        if _is_network_error(output_text):
            print("NETWORK ERROR DETECTED: 这是网络连接问题，不是代码错误。", flush=True)
            print("建议：1) 检查网络连接  2) 尝试切换到 PY 引擎（Python SDK 通常更稳定）", flush=True)
            raise RuntimeError(
                f"网络连接错误，auto-fix 无效。请检查网络或切换到 PY 引擎。\n\n{error_msg}"
            )
        if max_fixes >= 0 and attempt > max_fixes:
            raise RuntimeError(f"FAILED after {max_fixes} auto-fix attempt(s): {error_msg}")
        if max_fixes < 0 and attempt > unlimited_fix_limit:
            raise RuntimeError(f"FAILED after {unlimited_fix_limit} auto-fix attempts; unable to repair this record:\n{error_msg}")
        print(f"AUTO-FIX: sending the failure to OpenAI (repair #{attempt})...", flush=True)
        corrected = call_fix_api(source, error_msg, output_format="js")
        if not corrected.strip() or corrected in seen_sources:
            raise RuntimeError(f"FAILED: 自动修复未产生新的代码，已停止当前记录。\n{error_msg}")
        seen_sources.add(corrected)
        source = corrected
        print("AUTO-FIX: corrected JavaScript received; restarting...", flush=True)


def run_py_engine(source: str, filename: str, key_file: str, wait: bool, poll_seconds: int, max_fixes: int) -> str:
    """通过 Python earthengine-api 运行 GEE 代码（JS 输入时先自动转换为 Python）。"""
    if is_javascript(source):
        print("Detected JavaScript source. Converting to Python Earth Engine API...", flush=True)
        source = call_fix_api(source, "JavaScript detected; converting to Python Earth Engine API equivalent.", output_format="py")
        compile(source, str(filename), "exec")
        print("JavaScript converted to Python successfully.", flush=True)
    for attempt in range(max_fixes + 1):
        try:
            run_once(source, str(filename), key_file, wait, poll_seconds)
            print("SUCCESS")
            return source
        except Exception as error:
            details = traceback.format_exc()
            print(f"\nRUN FAILED (attempt {attempt + 1}/{max_fixes + 1})", flush=True)
            print(details, end="", flush=True)
            if _is_network_error(details):
                print("NETWORK ERROR DETECTED: 这是网络连接问题，不是代码错误。", flush=True)
                raise RuntimeError(
                    f"网络连接错误，auto-fix 无效。请检查网络连接后重试。\n\n{details}"
                ) from error
            if attempt >= max_fixes:
                raise RuntimeError(f"FAILED after {max_fixes} auto-fix attempt(s): {error}") from error
            print(f"AUTO-FIX: sending the failure to OpenAI (attempt {attempt + 1}/{max_fixes})...", flush=True)
            corrected = call_fix_api(source, details, output_format="py")
            compile(corrected, str(filename), "exec")
            source = corrected
            print("AUTO-FIX: corrected script saved; restarting...", flush=True)
    return source


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a Google Earth Engine script.")
    parser.add_argument("script", help="Path to a .js/.py Earth Engine script")
    parser.add_argument("--engine", choices=["js", "py"], default="js", help="Execution engine: js (default) or py")
    parser.add_argument("--key", help="Service-account JSON key path")
    parser.add_argument("--wait", action="store_true", help="Wait for submitted export tasks")
    parser.add_argument("--poll-seconds", type=int, default=10)
    parser.add_argument("--max-fixes", type=int, default=3)
    parser.add_argument("--code-stdin", action="store_true", help="Read script directly from stdin")
    args = parser.parse_args()

    load_env(Path(__file__).with_name(".env"))
    load_codex_config()
    _fix_proxy_env(os.environ)
    script_path = Path(args.script).resolve() if args.script else Path("<editor>")
    key_file = args.key or os.environ.get("GEE_PRIVATE_KEY_FILE", "service-account.json")
    source = sys.stdin.read() if args.code_stdin else script_path.read_text(encoding="utf-8")
    if "\ufffd" in source:
        raise ValueError("The submitted script contains replacement characters (U+FFFD), which indicates text was corrupted before execution. Paste the original source again using UTF-8.")

    if args.engine == "js":
        print(f"=== Using JS engine ({script_path.name}) ===", flush=True)
        result = run_js_engine(source, key_file, args.wait, args.max_fixes)
    else:
        print(f"=== Using PY engine ({script_path.name}) ===", flush=True)
        result = run_py_engine(source, script_path, key_file, args.wait, args.poll_seconds, args.max_fixes)

    print("FINAL_CODE_BEGIN")
    print(result, end="" if result.endswith("\n") else "\n")
    print("FINAL_CODE_END")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:
        print(f"Failed: {error}", file=sys.stderr)
        raise SystemExit(1)
