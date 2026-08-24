import fs from 'node:fs/promises';
import path from 'node:path';
import vm from 'node:vm';
import ee from '@google/earthengine';
import { google } from 'googleapis';

const TASK_COMPLETE = new Set(['COMPLETED', 'FAILED', 'CANCELLED']);

/** 检查资产的实际类型 */
function checkAssetType(assetId) {
  return new Promise((resolve, reject) => {
    ee.data.getAsset(assetId, (result) => {
      if (result && result.type) {
        resolve(result.type);
      } else {
        reject(new Error(`Asset '${assetId}' was not found or the service account has no access.`));
      }
    }, (error) => {
      reject(new Error(`Asset '${assetId}' was not found or the service account has no access: ${error?.message || error}`));
    });
  });
}

/** ImageCollection 专有方法（在 Image 上不可用） */
const IMAGE_COLLECTION_METHODS = [
  'filterDate', 'filterBounds', 'filter', 'sort', 'limit',
  'mosaic', 'composite', 'reduceColumns', 'getRegion',
  'mean', 'median', 'min', 'max', 'sum', 'count',
  'select', 'aggregate_array', 'aggregate_total'
];

/** 预处理源代码，验证资产类型并自动修复不匹配的类型 */
async function preprocessSource(source) {
  const fixes = [];
  const assetChecks = [];

  // 查找所有 ee.ImageCollection('asset_id') 调用（包括链式调用）
  // 同时捕获赋值给的变量名
  const imageCollectionAssignRegex = /(?:var|let|const)?\s*(\w+)\s*=\s*ee\.ImageCollection\s*\(\s*['"]([^'"]+)['"]\s*\)/g;
  let match;
  const imageCollectionVars = {};  // 变量名 -> 资产ID
  
  while ((match = imageCollectionAssignRegex.exec(source)) !== null) {
    const varName = match[1];
    const assetId = match[2];
    imageCollectionVars[varName] = assetId;
    assetChecks.push({ assetId, currentType: 'ImageCollection', fullMatch: match[0] });
  }

  // 也查找直接调用（不带变量赋值）
  const imageCollectionRegex = /ee\.ImageCollection\s*\(\s*['"]([^'"]+)['"]\s*\)/g;
  while ((match = imageCollectionRegex.exec(source)) !== null) {
    const assetId = match[1];
    if (!assetChecks.find(c => c.assetId === assetId)) {
      assetChecks.push({ assetId, currentType: 'ImageCollection', fullMatch: match[0] });
    }
  }

  // 查找所有 ee.Image('asset_id') 调用
  const imageRegex = /ee\.Image\s*\(\s*['"]([^'"]+)['"]\s*\)/g;
  while ((match = imageRegex.exec(source)) !== null) {
    const assetId = match[1];
    if (!assetChecks.find(c => c.assetId === assetId)) {
      assetChecks.push({ assetId, currentType: 'Image', fullMatch: match[0] });
    }
  }

  if (assetChecks.length === 0) {
    return { source, fixes };
  }

  // 批量检查资产类型
  console.log(`[ASSET] 检测到 ${assetChecks.length} 个资产引用，正在验证类型...`);
  const checkedTypes = await Promise.all(
    assetChecks.map(async ({ assetId }) => ({
      assetId,
      actualType: await checkAssetType(assetId)
    }))
  );

  // 构建资产类型映射
  const typeMap = {};
  checkedTypes.forEach(({ assetId, actualType }) => {
    if (actualType) {
      typeMap[assetId] = actualType;
    }
  });

  // 应用修复
  let fixedSource = source;
  const varsToFix = {};  // 需要修复的变量名 -> 资产ID

  assetChecks.forEach(({ assetId, currentType, fullMatch }) => {
    const actualType = typeMap[assetId];
    if (!actualType) return;

    // 如果当前是 ImageCollection 但实际是 Image
    if (currentType === 'ImageCollection' && actualType === 'Image') {
      // 找到完整的链式调用
      const chainRegex = new RegExp(
        `ee\\.ImageCollection\\s*\\(\\s*['"]${assetId.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}['"]\\s*\\)(\\s*\\.\\s*[\\w.]+\\s*\\([^)]*\\))*`,
        'g'
      );
      
      fixedSource = fixedSource.replace(chainRegex, (fullChain) => {
        let newCall = `ee.Image('${assetId}')`;
        
        // 找到所有链式方法调用
        const escapedId = assetId.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
        const baseCallRegex = new RegExp(`ee\\.ImageCollection\\s*\\(\\s*['"]${escapedId}['"]\\s*\\)`);
        const methodChain = fullChain
          .replace(baseCallRegex, '')
          .match(/\.(\w+)\s*\([^)]*\)/g) || [];
        
        let clipArgs = null;
        
        // 处理每个方法
        methodChain.forEach((methodCall) => {
          const methodName = methodCall.match(/\.(\w+)/)[1];
          
          if (methodName === 'filterBounds') {
            const argsMatch = methodCall.match(/filterBounds\s*\(([^)]*)\)/);
            if (argsMatch) {
              clipArgs = argsMatch[1];
            }
          }
          // 移除所有 ImageCollection 专有方法和 mosaic/composite
          // 保留可能在 Image 上也可用的方法（如 clip, select 等）
          if (!IMAGE_COLLECTION_METHODS.includes(methodName) && methodName !== 'mosaic' && methodName !== 'composite') {
            newCall += methodCall;
          }
        });
        
        if (clipArgs) {
          newCall += `.clip(${clipArgs})`;
        }
        
        return newCall;
      });

      // 记录需要修复后续使用的变量
      Object.entries(imageCollectionVars).forEach(([varName, varAssetId]) => {
        if (varAssetId === assetId) {
          varsToFix[varName] = assetId;
        }
      });

      fixes.push({
        assetId,
        original: fullMatch,
        fixed: `ee.Image('${assetId}')`,
        reason: `资产 '${assetId}' 实际是 Image 类型，不是 ImageCollection。已自动转换为 Image 并移除不兼容的方法链。`
      });
      console.log(`[ASSET] 修复: ${assetId} (ImageCollection -> Image)`);
    }
    // 如果当前是 Image 但实际是 ImageCollection
    else if (currentType === 'Image' && actualType === 'ImageCollection') {
      const newCall = `ee.ImageCollection('${assetId}')`;
      fixedSource = fixedSource.replace(fullMatch, newCall);
      fixes.push({
        assetId,
        original: fullMatch,
        fixed: newCall,
        reason: `资产 '${assetId}' 实际是 ImageCollection 类型，不是 Image`
      });
      console.log(`[ASSET] 修复: ${assetId} (Image -> ImageCollection)`);
    }
  });

  // 修复变量后续使用中的 ImageCollection 专有方法
  Object.entries(varsToFix).forEach(([varName, assetId]) => {
    // 找到所有对该变量的 ImageCollection 方法调用并移除
    // 例如: varName.mosaic() -> varName
    IMAGE_COLLECTION_METHODS.forEach(method => {
      const methodRegex = new RegExp(`\\b${varName.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}\\s*\\.\\s*${method}\\s*\\([^)]*\\)\\s*\\.\\s*`, 'g');
      fixedSource = fixedSource.replace(methodRegex, `${varName}.`);
      
      // 也处理链式末端的情况
      const endRegex = new RegExp(`\\b${varName.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}\\s*\\.\\s*${method}\\s*\\([^)]*\\)\\s*;`, 'g');
      fixedSource = fixedSource.replace(endRegex, `${varName};`);
      
      // 处理变量直接赋值给另一个变量的情况
      const assignRegex = new RegExp(`\\b${varName.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}\\s*\\.\\s*${method}\\s*\\([^)]*\\)`, 'g');
      fixedSource = fixedSource.replace(assignRegex, varName);
    });
    
    // 处理 mosaic/composite
    ['mosaic', 'composite'].forEach(method => {
      const regex = new RegExp(`\\b${varName.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}\\s*\\.\\s*${method}\\s*\\([^)]*\\)`, 'g');
      fixedSource = fixedSource.replace(regex, varName);
    });
  });

  return { source: fixedSource, fixes };
}

function authenticate({ auth, keyFile }) {
  return new Promise((resolve, reject) => {
    const timeout = setTimeout(() => {
      reject(new Error('Authentication timed out after 60 seconds. Check HTTPS_PROXY and network access to Google.'));
    }, 60000);
    const finish = (callback) => (...args) => {
      clearTimeout(timeout);
      callback(...args);
    };
    const initialized = () => ee.initialize(null, null, finish(resolve), finish(reject));
    if (auth === 'service-account') {
      if (!keyFile) return finish(reject)(new Error('Service-account mode requires --key or GEE_PRIVATE_KEY_FILE.'));
      fs.readFile(path.resolve(keyFile), 'utf8')
        .then(async (contents) => {
          const privateKey = JSON.parse(contents);
          const scopes = [
            'https://www.googleapis.com/auth/earthengine',
            'https://www.googleapis.com/auth/cloud-platform',
            'https://www.googleapis.com/auth/devstorage.full_control',
          ];
          const client = new google.auth.JWT(
            privateKey.client_email, null, privateKey.private_key, scopes
          );
          const refresh = async () => {
            const token = await client.authorize();
            console.log('Service-account token acquired.');
            return {
              access_token: token.access_token,
              token_type: token.token_type || 'Bearer',
              expires_in: (token.expiry_date - Date.now()) / 1000,
            };
          };
          const token = await refresh();
          console.log('Initializing Earth Engine API...');
          ee.data.setAuthTokenRefresher((_, callback) => {
            refresh().then(callback).catch((error) => callback({ error }));
          });
          ee.data.setAuthToken(
            privateKey.client_email, token.token_type, token.access_token, token.expires_in,
            scopes, initialized, false
          );
        })
        .catch((error) => {
          const code = error?.code || error?.cause?.code || 'unknown';
          const proxy = process.env.HTTPS_PROXY || process.env.HTTP_PROXY || '未配置';
          finish(reject)(new Error(`Google OAuth 认证失败（${code}）：${error?.message || error}。Token 地址：https://oauth2.googleapis.com/token；当前代理：${proxy}。请检查网络或在 web/gee_runner/.env 配置 HTTPS_PROXY。`));
        });
      return;
    }
    finish(reject)(new Error(
      'OAuth is not supported by the Earth Engine Node.js SDK. Use a service account: set GEE_AUTH=service-account and GEE_PRIVATE_KEY_FILE=./service-account.json.'
    ));
  });
}

function makeExport(tasks) {
  const submit = (factory) => (config) => {
    const task = factory(config);
    task.start();
    tasks.push(task);
    console.log(`Export started: ${config.description || task.id}`);
    return task;
  };
  return {
    image: { toDrive: submit(ee.batch.Export.image.toDrive), toAsset: submit(ee.batch.Export.image.toAsset), toCloudStorage: submit(ee.batch.Export.image.toCloudStorage) },
    table: { toDrive: submit(ee.batch.Export.table.toDrive), toAsset: submit(ee.batch.Export.table.toAsset), toCloudStorage: submit(ee.batch.Export.table.toCloudStorage) },
  };
}

export async function runScript(scriptPath, options) {
  console.log('Authenticating with Google Earth Engine...');
  await authenticate(options);
  console.log('Authentication complete. Running script...');
  const absolutePath = path.resolve(scriptPath);
  const rawSource = await fs.readFile(absolutePath, 'utf8');
  
  // 预处理代码，验证并修复资产类型
  const { source: processedSource, fixes } = await preprocessSource(rawSource);
  if (fixes.length > 0) {
    console.log(`[ASSET] 自动修复了 ${fixes.length} 个资产类型问题:`);
    fixes.forEach((fix, i) => {
      console.log(`  ${i + 1}. ${fix.reason}`);
    });
    console.log('[ASSET] 已应用资产类型修复；最终代码仅显示在成功结果面板。');
  }
  
  const tasks = [];
  const context = vm.createContext({
    ee,
    Export: makeExport(tasks),
    console,
    print: (...values) => console.log(...values),
    Map: { addLayer: (...values) => console.log('Map.addLayer:', ...values), centerObject: () => {}, setCenter: () => {} },
  });
  new vm.Script(processedSource, { filename: absolutePath }).runInContext(context);
  return { tasks, processedSource };
}

export async function runSource(source, filename, options) {
  console.log('Authenticating with Google Earth Engine...');
  await authenticate(options);
  console.log('Authentication complete. Running JavaScript...');
  
  // 预处理代码，验证并修复资产类型
  const { source: processedSource, fixes } = await preprocessSource(source);
  if (fixes.length > 0) {
    console.log(`[ASSET] 自动修复了 ${fixes.length} 个资产类型问题:`);
    fixes.forEach((fix, i) => {
      console.log(`  ${i + 1}. ${fix.reason}`);
    });
    console.log('[ASSET] 已应用资产类型修复；最终代码仅显示在成功结果面板。');
  }
  
  const tasks = [];
  const layerChecks = [];
  const verifyLayer = (image, name) => new Promise((resolve, reject) => {
    image.getMap({ min: 0, max: 1 }, (map, error) => {
      if (error) reject(new Error(`Layer '${name || 'unnamed'}' failed validation: ${error}`));
      else resolve(map);
    });
  });
  const context = vm.createContext({
    ee, Export: makeExport(tasks), console,
    print: (...values) => console.log('GEE_RESULT:', ...values),
    Map: {
      addLayer: (image, vis, name) => {
        console.log('GEE_RESULT: Map.addLayer:', name || 'unnamed');
        layerChecks.push(verifyLayer(image, name));
      },
      centerObject: () => {}, setCenter: () => {},
    },
  });
  new vm.Script(processedSource, { filename }).runInContext(context);
  await Promise.all(layerChecks);
  return { tasks, processedSource };
}

export async function waitForTasks(tasks, intervalMs = 10000) {
  const pending = new Set(tasks.map((task) => task.id));
  while (pending.size) {
    const states = await Promise.all([...pending].map((id) => new Promise((resolve, reject) => ee.data.getTaskStatus([id], (result) => resolve(result[0]), reject))));
    for (const state of states) {
      console.log(`${state.id}: ${state.state}${state.error_message ? ` (${state.error_message})` : ''}`);
      if (TASK_COMPLETE.has(state.state)) pending.delete(state.id);
    }
    if (pending.size) await new Promise((resolve) => setTimeout(resolve, intervalMs));
  }
}
