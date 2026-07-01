import fs from 'node:fs';
import path from 'node:path';
import { execSync } from 'node:child_process';

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
    skipCopyExe: argv.includes('--skip-copy-exe'),
    domain: (() => {
      const idx = argv.indexOf('--domain');
      return idx >= 0 ? (argv[idx + 1] || '').trim() : 'tpvelite.surge.sh';
    })(),
  };
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
