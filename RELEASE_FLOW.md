# Flujo Pro de Versionado y Deploy

Este flujo mantiene estable la funcion de actualizacion en la app.

## Regla principal

- `app/main.py` y `landing/version.json` siempre deben tener la misma version.
- `APP_BUILD` y `landing/version.json.build` siempre deben quedar sincronizados.
- Cada deploy de release incrementa al menos el patch (`x.y.z` -> `x.y.z+1`).
- Cada bump agrega una entrada en `CHANGELOG.md` con fecha/hora, autor y commit base.

## Comandos

Desde la raiz del proyecto:

Flujo completo (recomendado):

```bash
node scripts/release.mjs patch --changelog "Texto breve de cambios"

# release + deploy a Surge en una sola corrida
node scripts/release.mjs patch --deploy --force-update
```

Este comando hace en una sola corrida:

- bump de version
- bump de build (timestamp automático)
- validacion de sincronia
- commit automatico (`chore(release): vX.Y.Z`)
- tag anotado (`vX.Y.Z`)

Publicación automática a Surge (incluye copia de instalador):

```bash
node scripts/deploy-update.mjs
```

`deploy-update` ahora compila `dist/TPVElite_Setup.exe` automáticamente antes de publicar.

Opciones de deploy:

```bash
# Publicar en otro dominio
node scripts/deploy-update.mjs --domain mi-dominio.surge.sh

# Usar un Python específico para compilar el instalador
node scripts/deploy-update.mjs --python "C:/ruta/python.exe"

# Solo copiar EXE y validar (sin publicar)
node scripts/deploy-update.mjs --no-surge

# Publicar sin copiar EXE (si ya está sincronizado)
node scripts/deploy-update.mjs --skip-copy-exe

# Omitir compilación del instalador (avanzado)
node scripts/deploy-update.mjs --skip-build-exe
```

```bash
node scripts/bump-version.mjs patch --changelog "Texto breve de cambios"
```

Opciones de bump:

```bash
node scripts/bump-version.mjs patch
node scripts/bump-version.mjs minor
node scripts/bump-version.mjs major
```

Set manual:

```bash
node scripts/bump-version.mjs --set 3.1.0 --changelog "Release 3.1.0"
node scripts/release.mjs --set 3.1.0 --changelog "Release 3.1.0"
```

Validacion:

```bash
node scripts/validate-version-sync.mjs
```

Sin tag (si lo necesitas):

```bash
node scripts/release.mjs patch --changelog "Texto breve de cambios" --no-tag
```

## Checklist de release

1. Ejecutar bump de version con changelog.
2. Generar nuevo instalador `TPVElite_Setup.exe`.
3. Publicar instalador en destino de descarga.
4. Confirmar que `landing/version.json` apunte a la URL final del instalador.
5. Revisar `CHANGELOG.md` para validar la entrada de release.
6. Ejecutar push de rama y tags:

```bash
git push origin <rama>
git push origin --tags
```

7. El workflow valida sincronia y despliega landing a Surge.
8. Probar en una instalacion vieja que aparece el cartel de actualizacion y descarga la nueva version.

## Nota sobre updater

La app compara `APP_VERSION`, `APP_BUILD`, `version.json.build` y `force_update`.

Dispara actualización cuando:

- `version` remota es mayor
- misma `version` pero `build` distinto
- `force_update=true`
