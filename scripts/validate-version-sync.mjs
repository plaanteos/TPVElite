import fs from 'node:fs';
import path from 'node:path';

const root = process.cwd();
const appMainPath = path.join(root, 'app', 'main.py');
const landingVersionPath = path.join(root, 'landing', 'version.json');

function readAppVersion() {
  const content = fs.readFileSync(appMainPath, 'utf8');
  const match = content.match(/APP_VERSION\s*=\s*"([^"]+)"/);
  if (!match) {
    throw new Error('No se encontro APP_VERSION en app/main.py');
  }
  return match[1];
}

function readLandingVersion() {
  const raw = fs.readFileSync(landingVersionPath, 'utf8');
  const json = JSON.parse(raw);
  if (!json.version) {
    throw new Error('landing/version.json no contiene version');
  }
  return String(json.version).trim();
}

function main() {
  const appVersion = readAppVersion();
  const landingVersion = readLandingVersion();

  if (appVersion !== landingVersion) {
    console.error(`Desincronizacion de versiones: app=${appVersion}, landing=${landingVersion}`);
    process.exit(1);
  }

  console.log(`Version sincronizada OK: ${appVersion}`);
}

main();
