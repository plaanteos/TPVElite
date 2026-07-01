import fs from 'node:fs';
import path from 'node:path';
import { execSync, spawnSync } from 'node:child_process';

const root = process.cwd();
const distExe = path.join(root, 'dist', 'TPVElite_Setup.exe');
const landingExe = path.join(root, 'landing', 'TPVElite_Setup.exe');
const landingVersion = path.join(root, 'landing', 'version.json');

function run(command) {
  execSync(command, { stdio: 'inherit' });
}

function parseArgs(argv) {
  return {
    skipSurge: argv.includes('--no-surge'),
    skipBuildExe: argv.includes('--skip-build-exe'),
    skipCopyExe: argv.includes('--skip-copy-exe'),
    python: (() => {
      const idx = argv.indexOf('--python');
      return idx >= 0 ? (argv[idx + 1] || '').trim() : '';
    })(),
    domain: (() => {
      const idx = argv.indexOf('--domain');
      return idx >= 0 ? (argv[idx + 1] || '').trim() : 'tpvelite.surge.sh';
    })(),
  };
}

function resolvePython(pythonArg) {
  if (pythonArg) {
    return pythonArg;
  }

  const candidates = [
    path.join(root, '.venv-1', 'Scripts', 'python.exe'),
    path.join(root, '.venv', 'Scripts', 'python.exe'),
  ];

  for (const candidate of candidates) {
    if (fs.existsSync(candidate)) {
      return candidate;
    }
  }

  return 'python';
}

function buildInstaller(args) {
  if (args.skipBuildExe) {
    console.log('Se omitió build de instalador (--skip-build-exe)');
    return;
  }

  const python = resolvePython(args.python);
  console.log(`Compilando instalador con: ${python}`);

  const result = spawnSync(
    python,
    [
      '-m', 'PyInstaller',
      '--onefile',
      '--noconsole',
      '--name', 'TPVElite_Setup',
      '--icon', 'app/tpvelite.ico',
      '--add-data', 'app;app',
      'setup.pyw',
    ],
    {
      cwd: root,
      stdio: 'inherit',
      shell: false,
    }
  );

  if (result.error) {
    throw result.error;
  }

  if (result.status !== 0) {
    throw new Error(`PyInstaller finalizó con código ${result.status}`);
  }
}

function ensureExists(filePath, label) {
  if (!fs.existsSync(filePath)) {
    throw new Error(`${label} no encontrado: ${filePath}`);
  }
}

function main() {
  const args = parseArgs(process.argv);

  ensureExists(landingVersion, 'version.json');

  run('node scripts/validate-version-sync.mjs');

  buildInstaller(args);

  if (!args.skipCopyExe) {
    ensureExists(distExe, 'Instalador en dist');
    fs.copyFileSync(distExe, landingExe);
    console.log(`EXE sincronizado: ${landingExe}`);
  } else {
    console.log('Se omitió copia de EXE (--skip-copy-exe)');
  }

  if (args.skipSurge) {
    console.log('Se omitió publicación en Surge (--no-surge)');
    return;
  }

  run(`npx surge landing ${args.domain}`);
}

main();
