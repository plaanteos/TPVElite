import fs from 'node:fs';
import path from 'node:path';
import { execSync } from 'node:child_process';

const root = process.cwd();
const bumpScriptPath = path.join(root, 'scripts', 'bump-version.mjs');
const validateScriptPath = path.join(root, 'scripts', 'validate-version-sync.mjs');
const appMainPath = path.join(root, 'app', 'main.py');
const landingVersionPath = path.join(root, 'landing', 'version.json');
const changelogPath = path.join(root, 'CHANGELOG.md');
const appConfigPath = path.join(root, 'app', 'config.json');

function run(command) {
  execSync(command, { stdio: 'inherit' });
}

function runAndRead(command, fallback = '', trim = true) {
  try {
    const output = execSync(command, { stdio: ['ignore', 'pipe', 'ignore'] }).toString();
    const value = trim ? output.trim() : output;
    return value || fallback;
  } catch {
    return fallback;
  }
}

function ensureFile(filePath) {
  if (!fs.existsSync(filePath)) {
    throw new Error(`No existe el archivo requerido: ${filePath}`);
  }
}

function parseArgs(argv) {
  const args = {
    bump: 'patch',
    set: null,
    changelog: null,
    noTag: false,
  };

  for (let i = 2; i < argv.length; i += 1) {
    const arg = argv[i];

    if (arg === '--changelog') {
      args.changelog = argv[i + 1] || '';
      i += 1;
      continue;
    }

    if (arg === '--set') {
      args.set = argv[i + 1] || '';
      i += 1;
      continue;
    }

    if (arg === '--no-tag') {
      args.noTag = true;
      continue;
    }

    if (['major', 'minor', 'patch'].includes(arg)) {
      args.bump = arg;
    }
  }

  return args;
}

function escapeArg(value) {
  const normalized = String(value ?? '');
  if (normalized.includes('"')) {
    return `'${normalized.replace(/'/g, "'\\''")}'`;
  }
  return `"${normalized}"`;
}

function getNewVersion() {
  const raw = fs.readFileSync(landingVersionPath, 'utf8');
  const parsed = JSON.parse(raw);
  const version = String(parsed.version || '').trim();
  if (!version) {
    throw new Error('No se pudo leer la version nueva en landing/version.json');
  }
  return version;
}

function ensureCleanStagingArea() {
  const status = runAndRead('git status --porcelain', '', false);
  if (!status) {
    return;
  }

  const lines = status.split('\n').filter(Boolean);
  const staged = lines.filter((line) => line[0] !== ' ' && line[0] !== '?');
  if (!staged.length) {
    return;
  }

  throw new Error(
    'Hay cambios ya staged antes del release. Limpia el staging (commit/reset) y vuelve a ejecutar.'
  );
}

function isTrackedByGit(relPath) {
  try {
    execSync(`git ls-files --error-unmatch -- ${escapeArg(relPath)}`, { stdio: 'ignore' });
    return true;
  } catch {
    return false;
  }
}

function isIgnoredByGit(relPath) {
  try {
    execSync(`git check-ignore --quiet -- ${escapeArg(relPath)}`, { stdio: 'ignore' });
    return true;
  } catch {
    return false;
  }
}

function stageReleaseFiles() {
  const files = [appMainPath, landingVersionPath, changelogPath];
  if (fs.existsSync(appConfigPath)) {
    files.push(appConfigPath);
  }

  const stageable = files
    .map((filePath) => path.relative(root, filePath))
    .filter((relPath) => isTrackedByGit(relPath) || !isIgnoredByGit(relPath));

  if (!stageable.length) {
    throw new Error('No hay archivos stageables para el release.');
  }

  const addArgs = stageable.map((relPath) => escapeArg(relPath)).join(' ');
  run(`git add ${addArgs}`);

  return stageable;
}

function hasStagedChangesIn(paths) {
  const args = paths.map((filePath) => escapeArg(filePath)).join(' ');
  try {
    execSync(`git diff --cached --quiet -- ${args}`, { stdio: 'ignore' });
    return false;
  } catch {
    return true;
  }
}

function createTag(version) {
  const tagName = `v${version}`;
  const alreadyExists = Boolean(runAndRead(`git rev-parse ${tagName}`));
  if (alreadyExists) {
    throw new Error(`El tag ${tagName} ya existe. Usa otra version o borra el tag existente.`);
  }

  run(`git tag -a ${tagName} -m ${escapeArg(`Release ${version}`)}`);
  return tagName;
}

function buildBumpCommand(args) {
  const parts = ['node', 'scripts/bump-version.mjs'];

  if (args.set) {
    parts.push('--set', escapeArg(args.set));
  } else {
    parts.push(args.bump);
  }

  if (typeof args.changelog === 'string') {
    parts.push('--changelog', escapeArg(args.changelog));
  }

  return parts.join(' ');
}

function main() {
  ensureFile(bumpScriptPath);
  ensureFile(validateScriptPath);
  ensureFile(appMainPath);
  ensureFile(landingVersionPath);

  const args = parseArgs(process.argv);

  ensureCleanStagingArea();

  run(buildBumpCommand(args));
  run('node scripts/validate-version-sync.mjs');

  const version = getNewVersion();
  const stagedFiles = stageReleaseFiles();

  if (!hasStagedChangesIn(stagedFiles)) {
    throw new Error('No hay cambios para commitear en los archivos de release.');
  }

  const commitMessage = `chore(release): v${version}`;
  run(`git commit -m ${escapeArg(commitMessage)}`);

  let createdTag = null;
  if (!args.noTag) {
    createdTag = createTag(version);
  }

  const branch = runAndRead('git rev-parse --abbrev-ref HEAD', 'main');

  console.log('');
  console.log('Release generado correctamente.');
  console.log(`- version: ${version}`);
  console.log(`- branch: ${branch}`);
  console.log(`- commit: ${runAndRead('git rev-parse --short HEAD', 'desconocido')}`);
  if (createdTag) {
    console.log(`- tag: ${createdTag}`);
  } else {
    console.log('- tag: omitido (--no-tag)');
  }
  console.log('');
  console.log('Siguientes comandos sugeridos:');
  console.log(`- git push origin ${branch}`);
  if (createdTag) {
    console.log('- git push origin --tags');
  }
}

main();
