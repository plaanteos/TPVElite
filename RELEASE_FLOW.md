# Flujo Pro de Versionado y Deploy

Este flujo mantiene estable la funcion de actualizacion en la app.

## Regla principal

- `app/main.py` y `landing/version.json` siempre deben tener la misma version.
- Cada deploy de release incrementa al menos el patch (`x.y.z` -> `x.y.z+1`).
- Cada bump agrega una entrada en `CHANGELOG.md` con fecha/hora, autor y commit base.

## Comandos

Desde la raiz del proyecto:

Flujo completo (recomendado):

```bash
node scripts/release.mjs patch --changelog "Texto breve de cambios"
```

Este comando hace en una sola corrida:

- bump de version
- validacion de sincronia
- commit automatico (`chore(release): vX.Y.Z`)
- tag anotado (`vX.Y.Z`)

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

La app compara `APP_VERSION` contra `landing/version.json`.
Si no subes version en cada release, el cartel no se mostrara en clientes existentes.
