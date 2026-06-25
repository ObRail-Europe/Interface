## Description

<!-- Que fait cette PR et pourquoi ? Lien vers le besoin / la tâche concernée. -->

## Type de changement

- [ ] `feat` - nouvelle fonctionnalité
- [ ] `fix` - correction de bug
- [ ] `ci` / `build` - pipeline, conteneurisation, outillage
- [ ] `docs` - documentation
- [ ] `refactor` / `test` - refactoring ou tests

## Checklist

- [ ] `uv run ruff check` et `uv run ruff format --check` passent (api et dashboard concernés)
- [ ] `uv run pytest` passe localement
- [ ] La CI est verte
- [ ] Aucun secret ni donnée volumineuse n'est commité (`.env`, CSV de `data/`)
- [ ] Documentation mise à jour si nécessaire (README, docstrings)
