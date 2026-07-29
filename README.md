# ✨ Magic Sorter X

A clean-room upgrade inspired by three useful terminal ideas:

- **Magic Sorter:** friendly format detection, pretty output, and file organization.
- **fx:** an interactive terminal tree for JSON-like data, search, expansion, and compact previews.
- **Translate Shell:** automatic source-language detection with translation to English.

Magic Sorter X does not copy source code from those projects. It combines the product ideas in a new Python implementation.

## Features

- 🌳 Dependency-light full-screen TUI for JSON, JSONL/NDJSON, YAML, TOML, XML, CSV, and text.
- 🔎 Search keys and values; expand or collapse the entire tree.
- 🧠 Relaxed JSON support for comments and trailing commas.
- 🌐 Translate plain text or every string in structured data to English.
- 🔌 Translation backend chain: Translate Shell, `deep-translator`, or LibreTranslate.
- ✨ Type-aware emoji filenames such as `🐍 app.py` and `🧩 data.json`.
- 🧹 Safe organizer with **dry-run by default**, optional copy mode, and category folders.
- 📦 Installable command: `msx`.

## Install

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -e .
```

For the Python translation fallback:

```bash
pip install -e '.[translate]'
```

Translate Shell can also be used directly when the `trans` executable is installed. The program runs:

```bash
trans -brief :en "text"
```

For a self-hosted LibreTranslate instance:

```bash
export LIBRETRANSLATE_URL="http://localhost:5000"
export LIBRETRANSLATE_API_KEY="optional-key"
```

## Use

```bash
# fx-like interactive viewer
msx view examples/sample.json

# non-interactive pretty preview and summary
msx view examples/sample.json --no-tui --summary

# stdin also works
cat examples/sample.json | msx view

# translate all string values to English
msx translate foreign.json -o english.json

# optionally translate keys too
msx translate foreign.yaml --keys -o english.yaml

# preview emoji renames (safe dry-run)
msx emojify ./downloads --recursive

# perform the rename
msx emojify ./downloads --recursive --apply

# preview folder organization
msx organize ./downloads

# perform it; use --copy for non-destructive copies
msx organize ./downloads --apply --copy

# check translation backends
msx doctor
```

## TUI keys

| Key | Action |
|---|---|
| `/` | Search keys and values |
| `e` | Expand all nodes |
| `c` | Collapse all nodes |
| `Enter` / `Space` | Toggle selected node |
| `↑` / `↓` or `k` / `j` | Navigate |
| `q` | Quit |

## Safety

Renaming and organization are dry runs unless `--apply` is supplied. Existing destination files are never overwritten.

## Notes on the supplied archive

The DropMeFiles page identifies one password-protected ZIP (password `123`). This package was not executed or trusted automatically. Apply this source upgrade to the original program only after extracting and reviewing its source files locally.
