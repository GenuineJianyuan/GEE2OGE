#!/usr/bin/env node
import dotenv from 'dotenv';
import fs from 'node:fs';
import net from 'node:net';
import http from 'node:http';
import https from 'node:https';
import { execSync } from 'node:child_process';
import { HttpsProxyAgent } from 'https-proxy-agent';
process.env.EE_PYTHON_API_WARNING = '0';

// 加载 .env 但不覆盖已有环境变量
dotenv.config({ override: false });

function usage() {
  console.log(`gee-runner <script.js> [options]

Options:
  --auth service-account        Authentication method (default: service-account)
  --key <file>                 Service-account JSON key file
  --wait                       Poll submitted export tasks until finished
  --help                       Show this help`);
}

const args = process.argv.slice(2);
if (args.includes('--help')) {
  usage();
  process.exit(0);
}

const script = args.find((value) => !value.startsWith('--'));
const valueAfter = (flag) => {
  const index = args.indexOf(flag);
  return index === -1 ? undefined : args[index + 1];
};

/** 检测 Windows 系统代理设置 */
function detectWindowsProxy() {
  if (process.platform !== 'win32') return null;
  try {
    const cmd = "powershell -NoProfile -Command \"$p=Get-ItemProperty -Path 'HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\Internet Settings' -ErrorAction SilentlyContinue; if ($p.ProxyEnable -eq 1 -and $p.ProxyServer) { $p.ProxyServer }\"";
    const output = execSync(cmd, { encoding: 'utf8', timeout: 3000 }).trim();
    if (output && output !== 'None' && output !== '') {
      return output.startsWith('http') ? output : `http://${output}`;
    }
  } catch {}
  return null;
}

/** 获取当前代理 URL */
function getProxyUrl() {
  return process.env.HTTPS_PROXY || process.env.https_proxy ||
    process.env.HTTP_PROXY || process.env.http_proxy || null;
}

/** 检查代理是否可达 */
function checkProxyReachable(host, port) {
  return new Promise((resolve) => {
    const socket = net.connect({ host, port, timeout: 3000 });
    let done = false;
    const finish = (ok) => {
      if (done) return;
      done = true;
      try { socket.destroy(); } catch {}
      resolve(ok);
    };
    socket.on('connect', () => finish(true));
    socket.on('error', () => finish(false));
    socket.on('timeout', () => finish(false));
  });
}

/** 设置全局代理：patch http/https 模块使其默认走代理 */
function setupGlobalProxy(proxyUrl) {
  const agent = new HttpsProxyAgent(proxyUrl);
  const origHttpsRequest = https.request.bind(https);
  const origHttpsGet = https.get.bind(https);
  const origHttpRequest = http.request.bind(http);
  const origHttpGet = http.get.bind(http);
  let callCount = 0;

  /** 处理 https.request/https.get 的多种调用形式，统一添加代理 */
  function wrapRequest(origFn) {
    return function(arg1, arg2, arg3) {
      let url, options, callback;

      if (typeof arg1 === 'function') {
        callback = arg1;
      } else if (typeof arg2 === 'function') {
        url = arg1;
        callback = arg2;
      } else {
        url = arg1;
        options = arg2;
        callback = arg3;
      }

      // 确定 options 对象并添加 agent
      if (options && typeof options === 'object') {
        if (!options.agent) options.agent = agent;
      } else if (url && typeof url === 'object' && !(url instanceof URL) && typeof url !== 'string') {
        if (!url.agent) url.agent = agent;
      } else if (url && (typeof url === 'string' || url instanceof URL) && !options && callback) {
        options = { agent };
        return origFn(url, options, callback);
      }

      const args = [];
      if (url !== undefined) args.push(url);
      if (options !== undefined) args.push(options);
      if (callback !== undefined) args.push(callback);
      callCount++;
      if (callCount <= 5) {
        const host = url?.hostname || url?.host || '?';
        const path = url?.path || url?.pathname || '/';
        const method = options?.method || url?.method || 'GET';
        console.log(`[PROXY] #${callCount}: ${method} https://${host}${path}`);
      }
      return origFn(...args);
    };
  }

  https.request = wrapRequest(origHttpsRequest);
  https.get = wrapRequest(origHttpsGet);
  http.request = wrapRequest(origHttpRequest);
  http.get = wrapRequest(origHttpGet);
  console.log(`[PROXY] Global proxy agent installed: ${proxyUrl}`);
}

/** 诊断并配置代理 */
async function setupProxy() {
  let proxyUrl = getProxyUrl();
  if (!proxyUrl) {
    const detected = detectWindowsProxy();
    if (detected) {
      proxyUrl = detected;
      process.env.HTTPS_PROXY = proxyUrl;
      process.env.HTTP_PROXY = proxyUrl;
      console.log(`[PROXY] Auto-detected Windows system proxy: ${proxyUrl}`);
    } else {
      console.log('[PROXY] No proxy configured.');
      return;
    }
  }
  let parsed;
  try { parsed = new URL(proxyUrl); } catch { return; }
  const host = parsed.hostname;
  const port = parseInt(parsed.port || (parsed.protocol === 'https:' ? 443 : 80), 10);
  const reachable = await checkProxyReachable(host, port);
  if (reachable) {
    console.log(`[PROXY] Proxy ${proxyUrl} is reachable.`);
  } else {
    const detected = detectWindowsProxy();
    if (detected && detected !== proxyUrl) {
      console.log(`[PROXY] Configured proxy ${proxyUrl} unreachable, trying Windows system proxy ${detected}`);
      process.env.HTTPS_PROXY = detected;
      process.env.HTTP_PROXY = detected;
      proxyUrl = detected;
      const p2 = new URL(proxyUrl);
      const ok2 = await checkProxyReachable(p2.hostname, parseInt(p2.port || '80', 10));
      if (!ok2) {
        console.log(`[PROXY] WARNING: Both proxies appear unreachable.`);
      }
    } else {
      console.log(`[PROXY] WARNING: Proxy ${proxyUrl} appears unreachable.`);
    }
  }
  setupGlobalProxy(proxyUrl);
}

await setupProxy();

const { runScript, runSource, waitForTasks } = await import('../src/runner.js');

let result;
let inputSource = '';
try {
  if (script) {
    result = await runScript(script, { auth: valueAfter('--auth') || process.env.GEE_AUTH || 'service-account', keyFile: valueAfter('--key') || process.env.GEE_PRIVATE_KEY_FILE });
  } else {
    inputSource = fs.readFileSync(0, 'utf8');
    result = await runSource(inputSource, '<editor.js>', { auth: process.env.GEE_AUTH || 'service-account', keyFile: process.env.GEE_PRIVATE_KEY_FILE });
  }
  const tasks = result.tasks;
  const processedSource = result.processedSource;
  if (tasks.length) {
    console.log(`Submitted ${tasks.length} export task(s).`);
    if (args.includes('--wait')) await waitForTasks(tasks);
  }
  console.log('FINAL_CODE_BEGIN');
  console.log(processedSource);
  console.log('FINAL_CODE_END');
  console.log('SUCCESS');
} catch (error) {
  console.error(`FAILED: ${error.stack || error.message}`);
  process.exitCode = 1;
}
