# Magic Sorter X 0.2.0

## Added

- Guided wizard mode when the program starts with no command.
- Explicit `wizard` command and `--wizard` option.
- Direct project launch through `msx.py` on every platform.
- Windows batch and PowerShell launchers plus the Unix launcher.
- Built-in terminal rendering without a required third-party UI package.
- Built-in YAML fallback reader and writer.
- Built-in TOML writer for translated TOML output.
- Built-in test runner.

## Preserved

- Full-screen structured-data tree viewer with search and expand/collapse controls.
- JSON, relaxed JSON, JSONL/NDJSON, YAML, TOML, XML, CSV, and text parsing.
- Translation to English with recursive structured-data handling and duplicate caching.
- XML translation that preserves element names and attributes.
- Type-aware emoji filename plans.
- Category-based folder organization.
- Dry-run defaults, collision checks, copy mode, and no-overwrite behavior.
- Diagnostics and example files.

## Changed

- The project now runs directly from its folder without a package setup step.
- Core viewing, parsing, serialization, organizing, and wizard features use the Python standard library.
- Translation integrations remain optional and are detected automatically when already available.
