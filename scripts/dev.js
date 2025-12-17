// Cross-platform dev launcher: builds infra, ensures venv, installs deps, migrates DB, runs API/workers concurrently
const { spawn } = require('child_process');
const { join } = require('path');
const { existsSync } = require('fs');
const concurrently = require('concurrently');
const waitOn = require('wait-on');

// --- Helper Functions ---

function run(cmd, args, opts = {}) {
  return new Promise((resolve, reject) => {
    const cp = spawn(cmd, args, { stdio: 'inherit', shell: process.platform === 'win32', ...opts });
    cp.on('exit', code => code === 0 ? resolve() : reject(new Error(`${cmd} exited with ${code}`)));
  });
}

// No healthchecks configured in compose; wait on open ports instead
async function waitForPorts() {
  console.log('[dev] waiting for temporal and postgres ports...');
  await waitOn({ resources: ['tcp:127.0.0.1:7233', 'tcp:127.0.0.1:5432'], timeout: 60000 });
}


// --- Main Execution ---

async function main() {
  const isWin = process.platform === 'win32';
  const venvDir = '.venv';
  const venvBin = isWin ? join(venvDir, 'Scripts') : join(venvDir, 'bin');
  const python = process.env.PY || 'python';
  const pyExe = isWin ? join(venvBin, 'python.exe') : join(venvBin, 'python');
  const pipModuleArgs = ['-m', 'pip'];

  // 1) Bring up Docker and wait for services to be HEALTHY
  console.log('[dev] bringing up docker infra...');
  await run('docker', ['compose', 'up', '--build', '-d']);

  await waitForPorts();

  // 2) Ensure venv and install Python deps
  console.log('[dev] ensuring python venv and installing requirements...');
  if (!existsSync(venvBin)) {
    await run(python, ['-m', 'venv', venvDir]);
  }
  await run(pyExe, [...pipModuleArgs, 'install', '-r', 'requirements.txt']);

  // 3) DB migrate with Drizzle
  console.log('[dev] installing drizzle deps and running migrations...');
  await run('npm', ['--prefix', 'migrations/drizzle', 'install']);
  const dbUrl = process.env.DATABASE_URL || 'postgresql://temporal:temporal@172.31.11.185:5434/temporal';
  try {
    await run('npm', ['--prefix', 'migrations/drizzle', 'run', 'migrate'], {
      env: { ...process.env, DATABASE_URL: dbUrl },
    });
  } catch (e) {
    console.error('[dev] migrations failed. If password auth failed, reset volume: "docker compose down -v" or set DATABASE_URL to match your DB creds.');
    throw e;
  }

  // 4) Run API and workers concurrently using venv python
  const pyPath = process.cwd();
  const envCommon = {
    ...process.env,
    PYTHONPATH: isWin
      ? `${pyPath};${join(pyPath, 'packages', 'common')}`
      : `${pyPath}:${join(pyPath, 'packages', 'common')}`,
    TEMPORAL_SERVER: '127.0.0.1:7233',
    DATABASE_URL: dbUrl,
  };

  const apiCmd = {
    command: `${pyExe} -m uvicorn services.api.app.main:app --host 0.0.0.0 --port 8000`,
    name: 'api',
    env: envCommon,
  };
  const orderCmd = {
    command: `${pyExe} services/order_worker/worker.py`,
    name: 'order',
    env: envCommon,
  };
  const shipCmd = {
    command: `${pyExe} services/shipping_worker/worker.py`,
    name: 'ship',
    env: envCommon,
  };

  console.log('[dev] starting API and workers...');
  const { result } = concurrently([apiCmd, orderCmd, shipCmd], {
    killOthers: ['failure', 'success'],
    prefix: 'name',
  });
  await result;
}

main().catch(err => {
  // We don't need to log the error again as it's handled in the calling blocks
  process.exit(1);
});