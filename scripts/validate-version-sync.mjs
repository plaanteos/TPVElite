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

function readAppBuild() {
  const content = fs.readFileSync(appMainPath, 'utf8');
  const match = content.match(/APP_BUILD\s*=\s*"([^"]+)"/);
  if (!match) {
    throw new Error('No se encontro APP_BUILD en app/main.py');
  }
  return match[1];
}

function readLandingVersion() {
  const raw = fs.readFileSync(landingVersionPath, 'utf8');
  const json = JSON.parse(raw);
  if (!json.version) {
    throw new Error('landing/version.json no contiene version');
  }
  if (!json.build) {
    throw new Error('landing/version.json no contiene build');
  }
  return {
    version: String(json.version).trim(),
    build: String(json.build).trim(),
  };
}

function main() {
  const appVersion = readAppVersion();
  const appBuild = readAppBuild();
  const landing = readLandingVersion();

  if (appVersion !== landing.version) {
    console.error(`Desincronizacion de versiones: app=${appVersion}, landing=${landing.version}`);
    process.exit(1);
  }

  if (appBuild !== landing.build) {
    console.error(`Desincronizacion de build: app=${appBuild}, landing=${landing.build}`);
    process.exit(1);
  }

  console.log(`Version/build sincronizados OK: v${appVersion} build ${appBuild}`);
}

main();
