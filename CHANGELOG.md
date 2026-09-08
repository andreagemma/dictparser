# Changelog

All notable changes to this project will be documented in this file.

## 0.1.1 - 2026-09-08

### CI/CD

- Aligned GitHub Actions workflows with the configreader flow and analogous file names:
	- `all.yml`
	- `ci.yml`
	- `fast_ci.yml`
	- `quality.yml`
	- `create-release.yml`
	- `create-release-whl.yml`
	- `release.yml`

### Versioning

- Bumped package/build version from `0.1.0` to `0.1.1`.

## 0.1.0

### Added

- Added `DictParser.get_all()` to resolve and return the full dictionary.
- Added `DictParser.to_json()` and `DictParser.to_yaml()` for serialization.
- Added `DictParser.save()` with output format inference from filename and json default fallback.
- Added CLI entry point behavior for:
	- full output via `get_all` when no key is provided
	- single key output via `-k/--key`
	- file output via `-o/--output`
	- forced output format via `-f/--format json|yaml`

## Unreleased

### Documentation

- Added focused inline comments in `src/dictparser/dictparser.py` to explain path/type dispatch and recursive placeholder resolution.
- Added a complete `README.md` with installation, quick usage, and behavior notes.
- Added project documentation index and library/CLI pages in `docs/`.

### Compliance

- Added third-party license archive under `licenses/third_party/packages/`.
- Added `licenses/third_party/summary.tsv` with package, version, license path, and source URL.
- Added `THIRD_PARTY_NOTICES.md` with dependency notice details.

