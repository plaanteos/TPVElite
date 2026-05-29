import fs from 'node:fs';
import path from 'node:path';
import { execSync } from 'node:child_process';

const root = process.cwd();
const appMainPath = path.join(root, 'app', 'main.py');
const landingVersionPath = path.join(root, 'landing', 'version.json');
const appConfigPath = path.join(root, 'app', 'config.json');
const changelogPath = path.join(root, 'CHANGELOG.md');

function parseArgs(argv) {
  const args = { bump: 'patch', changelog: null, set: null };
  for (let i = 2; i < argv.length; i += 1) {
    const arg = argv[i];
    if (arg === '--changelog') {
      args.changelog = argv[i + 1] || '';
      i += 1;
    } else if (arg === '--set') {
      args.set = argv[i + 1] || '';
      i += 1;
    } else if (['major', 'minor', 'patch'].includes(arg)) {
      args.bump = arg;
    }
  }
  return args;
}

function bumpSemver(version, bump) {
  const parts = version.split('.').map((x) => Number(x));
  if (parts.length !== 3 || parts.some(Number.isNaN)) {
    throw new Error(`Version invalida: ${version}`);
  }
  const [major, minor, patch] = parts;
  if (bump === 'major') return `${major + 1}.0.0`;
  if (bump === 'minor') return `${major}.${minor + 1}.0`;
  return `${major}.${minor}.${patch + 1}`;
}

function updateAppMainVersion(content, newVersion) {
  const appVersionPattern = /APP_VERSION\s*=\s*"([^"]+)"/;
  if (!appVersionPattern.test(content)) {
    throw new Error('No se encontro APP_VERSION en app/main.py');
  }

  let updated = content.replace(appVersionPattern, `APP_VERSION = "${newVersion}"`);

  // Mantiene sincronizada la cabecera descriptiva del archivo.
  const headerVersionPattern = /(Versi[oó]n:\s*)(\d+\.\d+\.\d+)/i;
  if (headerVersionPattern.test(updated)) {
    updated = updated.replace(headerVersionPattern, `$1${newVersion}`);
  }

  return updated;
}

function ensureFile(filePath) {
  if (!fs.existsSync(filePath)) {
    throw new Error(`No existe el archivo requerido: ${filePath}`);
  }
}

function getGitValue(command, fallback = 'desconocido') {
  try {
    return execSync(command, { stdio: ['ignore', 'pipe', 'ignore'] }).toString().trim() || fallback;
  } catch {
    return fallback;
  }
}

function nowStamp() {
  const date = new Date();
  const yyyy = date.getFullYear();
  const mm = String(date.getMonth() + 1).padStart(2, '0');
  const dd = String(date.getDate()).padStart(2, '0');
  const hh = String(date.getHours()).padStart(2, '0');
  const mi = String(date.getMinutes()).padStart(2, '0');
  const ss = String(date.getSeconds()).padStart(2, '0');
  return `${yyyy}-${mm}-${dd} ${hh}:${mi}:${ss}`;
}

function ensureChangelogFile() {
  if (!fs.existsSync(changelogPath)) {
    fs.writeFileSync(changelogPath, '# Changelog\n\n', 'utf8');
  }
}

function appendReleaseToChangelog({ newVersion, releaseNote }) {
  ensureChangelogFile();

  const authorName = getGitValue('git config user.name', 'sin-autor');
  const authorEmail = getGitValue('git config user.email', 'sin-email');
  const branch = getGitValue('git rev-parse --abbrev-ref HEAD', 'sin-branch');
  const head = getGitValue('git rev-parse --short HEAD', 'sin-commit');
  const stampedAt = nowStamp();

  const entry = [
    `## ${newVersion} - ${stampedAt}`,
    `- resumen: ${releaseNote}`,
    `- autor: ${authorName} <${authorEmail}>`,
    `- branch: ${branch}`,
    `- commit_base: ${head}`,
    '',
  ].join('\n');

  const duplicateSignature = [
    `## ${newVersion} - `,
    `- resumen: ${releaseNote}`,
    `- commit_base: ${head}`,
  ];

  const current = fs.readFileSync(changelogPath, 'utf8');
  const hasHeader = current.startsWith('# Changelog');
  if (!hasHeader) {
    fs.writeFileSync(changelogPath, `# Changelog\n\n${entry}${current}`, 'utf8');
    return;
  }

  const headerEnd = current.indexOf('\n\n');
  if (headerEnd === -1) {
    fs.writeFileSync(changelogPath, `# Changelog\n\n${entry}`, 'utf8');
    return;
  }

  const header = current.slice(0, headerEnd + 2);
  const body = current.slice(headerEnd + 2);

  const firstEntryEnd = body.indexOf('\n## ');
  const firstEntry = firstEntryEnd === -1 ? body : body.slice(0, firstEntryEnd + 1);
  const isDuplicateFirstEntry = duplicateSignature.every((marker) => firstEntry.includes(marker));
  if (isDuplicateFirstEntry) {
    return;
  }

  fs.writeFileSync(changelogPath, `${header}${entry}${body}`, 'utf8');
}

function main() {
  const args = parseArgs(process.argv);

  ensureFile(appMainPath);
  ensureFile(landingVersionPath);

  const landingVersionRaw = fs.readFileSync(landingVersionPath, 'utf8');
  const landingVersion = JSON.parse(landingVersionRaw);
  const currentVersion = String(landingVersion.version || '').trim();

  if (!currentVersion) {
    throw new Error('landing/version.json no tiene version valida');
  }

  const newVersion = args.set ? args.set : bumpSemver(currentVersion, args.bump);
  const releaseNote = (typeof args.changelog === 'string' && args.changelog.trim())
    ? args.changelog.trim()
    : `Release ${newVersion}`;

  landingVersion.version = newVersion;
  landingVersion.changelog = releaseNote;
  fs.writeFileSync(landingVersionPath, `${JSON.stringify(landingVersion, null, 2)}\n`, 'utf8');

  const appMainRaw = fs.readFileSync(appMainPath, 'utf8');
  const appMainUpdated = updateAppMainVersion(appMainRaw, newVersion);
  fs.writeFileSync(appMainPath, appMainUpdated, 'utf8');

  if (fs.existsSync(appConfigPath)) {
    const appConfigRaw = fs.readFileSync(appConfigPath, 'utf8');
    const appConfig = JSON.parse(appConfigRaw);
    appConfig.app = appConfig.app || {};
    appConfig.app.version = newVersion;
    fs.writeFileSync(appConfigPath, `${JSON.stringify(appConfig, null, 4)}\n`, 'utf8');
  }

  appendReleaseToChangelog({ newVersion, releaseNote });

  console.log(`Version actual: ${currentVersion}`);
  console.log(`Version nueva : ${newVersion}`);
  console.log('Archivos actualizados:');
  console.log('- app/main.py');
  console.log('- landing/version.json');
  console.log('- CHANGELOG.md');
  if (fs.existsSync(appConfigPath)) {
    console.log('- app/config.json');
  }
}

main();
