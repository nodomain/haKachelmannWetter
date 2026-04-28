# Release Process

## Versioning

This project uses **Semantic Versioning** (major.minor.patch) because it's a public HACS integration with consumers who need version constraints.

| Bump | When |
|------|------|
| **patch** (2.3.1 → 2.3.2) | Bug fix, no new entities or config changes |
| **minor** (2.3.x → 2.4.0) | New sensors, features, non-breaking additions |
| **major** (2.x → 3.0.0) | Breaking changes (device ID change, removed entities, config migration) |

## Release Checklist

1. **Branch** — create `fix/description` or `feat/description` from `main`
2. **Implement** — code changes in `custom_components/kachelmannwetter/`
3. **Test** — ensure `.venv/bin/pytest tests/ -v` passes
4. **Version bump** — update `"version"` in `manifest.json`
5. **Changelog** — add entry to `CHANGELOG.md` (see format below)
6. **Commit** — conventional commit message (see below)
7. **Push** — `git push -u origin <branch>`
8. **PR** — `gh pr create --title "<conventional commit title>" --base main`
9. **Merge** — `gh pr merge <number> --squash --admin`
10. **Tag** — `git tag -a v<version> -m "v<version>: <short description>"` then `git push origin v<version>`
11. **Cleanup** — `git branch -d <branch>`

## Changelog Format

Entry goes at the top of `CHANGELOG.md`, above the previous release:

```markdown
## [X.Y.Z] - YYYY-MM-DD - Short description

### Fixed
- Description of what was fixed and why

### Added
- Description of new feature

### Changed
- Description of what changed (use for breaking changes too)
```

Categories: Added, Changed, Deprecated, Removed, Fixed, Security.
Write for users — focus on impact, not implementation details.

## Commit Message Format

```
<type>(<scope>): <description>

[optional body explaining why]
```

Types: `fix`, `feat`, `docs`, `refactor`, `test`, `chore`, `ci`
Scope: `weather`, `sensor`, `config`, `client`, `coordinator`, `helpers`

Examples:
- `fix(weather): prevent clear-night leaking into daily forecast`
- `feat(sensor): add UV index sensor from hourly forecast`
- `chore: bump ruff to v0.12`

## Files to Update Per Release

| File | What to change |
|------|----------------|
| `custom_components/kachelmannwetter/manifest.json` | `"version": "X.Y.Z"` |
| `CHANGELOG.md` | New section at top |

Note: `pyproject.toml` version is NOT authoritative — `manifest.json` is the source of truth for HACS.

## GitHub Release

The git tag `vX.Y.Z` is what HACS uses to detect new versions. Always create a GitHub Release too for visibility and user notifications:

```bash
gh release create vX.Y.Z --title "vX.Y.Z" --notes "<changelog entry in markdown>"
```

Use the changelog entry content (### Fixed / ### Added etc.) as release notes.

## Branch Protection

- `main` has branch protection (requires admin flag to merge)
- Always use `--admin` with `gh pr merge` or wait for CI
- Never push directly to `main`
