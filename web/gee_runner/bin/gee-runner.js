#!/usr/bin/env node
import dotenv from 'dotenv';

// Earth Engine reads proxy variables while its dependency tree is imported.
dotenv.config();

function usage() {
  console.log(`gee-runner <script.js> [options]

Options:
  --auth service-account        Authentication method (default: service-account)
  --key <file>                  Service-account JSON key file
  --wait                        Poll submitted export tasks until finished
  --help                        Show this help`);
}

const args = process.argv.slice(2);
if (args.includes('--help') || args.length === 0) {
  usage();
  process.exit(args.length === 0 ? 1 : 0);
}

const script = args.find((value) => !value.startsWith('--'));
const valueAfter = (flag) => {
  const index = args.indexOf(flag);
  return index === -1 ? undefined : args[index + 1];
};

if (!script) {
  console.error('Missing script path.');
  process.exit(1);
}

try {
  const { runScript, waitForTasks } = await import('../src/runner.js');
  const tasks = await runScript(script, {
    auth: valueAfter('--auth') || process.env.GEE_AUTH || 'service-account',
    keyFile: valueAfter('--key') || process.env.GEE_PRIVATE_KEY_FILE,
  });
  if (tasks.length) {
    console.log(`Submitted ${tasks.length} export task(s).`);
    if (args.includes('--wait')) await waitForTasks(tasks);
  }
} catch (error) {
  console.error(`Failed: ${error.message}`);
  if (error.cause?.code || error.code) {
    console.error(`Network detail: ${error.cause?.code || error.code} ${error.cause?.message || ''}`);
  }
  process.exitCode = 1;
}
