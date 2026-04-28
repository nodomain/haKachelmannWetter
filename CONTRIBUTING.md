# Contributing to KachelmannWetter for Home Assistant

Thanks for your interest in contributing!

## Getting started

1. Fork the repository
2. Clone your fork
3. Create a virtual environment:
   ```bash
   python3 -m venv .venv
   .venv/bin/pip install homeassistant ruff mypy
   ```
4. Create a feature branch: `git checkout -b feat/my-feature`

## Code style

- Run `ruff check custom_components/kachelmannwetter/` before committing
- Run `mypy custom_components/kachelmannwetter/ --ignore-missing-imports` for type checking
- Follow [Home Assistant developer docs](https://developers.home-assistant.io/) patterns
- Use `translation_key` for entity names, `icons.json` for icons — no hardcoded strings

## Testing

- Use `scripts/audit_api_coverage.py` to verify all API fields are mapped
- Use `scripts/deploy.sh` to deploy to a local HA instance for manual testing

## Pull requests

- One logical change per PR
- Update `CHANGELOG.md` under `[Unreleased]`
- Update translations (`translations/en.json`, `translations/de.json`) if adding entities
- Update `icons.json` if adding entities
- Ensure `ruff` and `mypy` pass with zero errors

## Commit messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):
- `feat:` new feature
- `fix:` bug fix
- `docs:` documentation only
- `chore:` build/tooling

## Reporting issues

Please use [GitHub Issues](https://github.com/nodomain/haKachelmannWetter/issues) with the provided templates.
