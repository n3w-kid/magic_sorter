# Magic Sorter X 0.1.0

## Added

- Interactive, dependency-light terminal tree viewer inspired by `fx`.
- Search, expand/collapse controls, JSON paths, and rich non-interactive previews.
- JSON, JSONC, JSONL/NDJSON, YAML, TOML, XML, CSV, and plain-text parsing.
- Automatic translation to English through Translate Shell, `deep-translator`, or LibreTranslate.
- Recursive structured-data translation with duplicate caching and long-text chunking.
- XML round-tripping that preserves element names and attributes while translating text nodes.
- Type-aware emoji filename plans and emoji category folders.
- Safe dry-run defaults, collision checks, optional copy mode, and no overwrites.
- `msx doctor` diagnostics, Windows and Unix launchers, examples, tests, and installable wheel.

## Validation

- 12 automated tests pass.
- The built wheel was installed into a clean target directory and smoke-tested with `view`, `emojify`, `organize`, and `doctor`.
