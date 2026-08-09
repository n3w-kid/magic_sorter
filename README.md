# ✨ Magic Sorter X

Magic Sorter X is a terminal tool for viewing structured data, translating text to English, adding type-aware emoji to filenames, and organizing folders safely.

This edition adds a guided wizard and runs directly from the project folder. No package setup step is required.

## Requirements

- Python 3.11 or newer
- An interactive terminal for the full-screen tree viewer
- A translation backend only when using translation

Everything else needed for viewing, parsing, formatting, emoji renaming, organizing, and the wizard is included in the project.

## Start the wizard

### Windows

Double-click `run_msx.bat`, or run:

```text
run_msx.bat
```

PowerShell users can also run:

```text
.\run_msx.ps1
```

### macOS or Linux

```text
./run_msx.sh
```

### Any platform

```text
python msx.py
```

Running the program with no command opens the wizard automatically.

You can also open it explicitly:

```text
python msx.py wizard
python msx.py --wizard
```

## Wizard features

The wizard puts all main actions in one menu:

1. View a file
2. Translate a file to English
3. Add emoji to filenames
4. Organize a folder
5. Run system checks
6. Exit

Each action asks only for the options it needs. Rename and organize actions still default to a safe preview unless you choose to apply the changes.

## Command mode

The original command-style interface is still available.

```text
python msx.py view examples/sample.json
python msx.py view examples/sample.json --no-tui --summary
python msx.py translate examples/foreign.yaml -o english.yaml
python msx.py translate examples/foreign.yaml --keys -o english.yaml
python msx.py emojify ./downloads --recursive
python msx.py emojify ./downloads --recursive --apply
python msx.py organize ./downloads
python msx.py organize ./downloads --apply --copy
python msx.py doctor
```

The launcher scripts accept the same options:

```text
run_msx.bat view examples\sample.json --summary
./run_msx.sh organize ./downloads
```

## Supported data

Magic Sorter X detects and reads:

- JSON
- relaxed JSON with comments and trailing commas
- JSONL and NDJSON
- YAML
- TOML
- XML
- CSV and TSV
- plain text

The project includes a built-in YAML reader/writer for normal mappings, lists, and scalar values. If a compatible YAML module already exists on the system, Magic Sorter X can use it automatically.

## Viewer

The full-screen tree viewer supports:

| Key | Action |
|---|---|
| `/` | Search keys and values |
| `e` | Expand all nodes |
| `c` | Collapse the tree |
| `Enter` or `Space` | Toggle the selected node |
| `↑` / `↓` or `k` / `j` | Move |
| `←` / `→` or `h` / `l` | Collapse or expand |
| `Page Up` / `Page Down` | Move by a page |
| `q` or `Esc` | Quit |

If the full-screen mode is unavailable, the program automatically falls back to a normal terminal preview.

## Translation

Translation preserves non-string values and can optionally translate object keys. XML element names and attributes stay unchanged while XML text nodes are translated.

The automatic backend order is:

1. Translate Shell when the `trans` executable already exists
2. `deep-translator` when it already exists in the current Python environment
3. LibreTranslate when `LIBRETRANSLATE_URL` is configured

For LibreTranslate:

```text
LIBRETRANSLATE_URL=http://localhost:5000
LIBRETRANSLATE_API_KEY=optional-key
```

On macOS or Linux these can be exported in the shell. On Windows they can be set as normal environment variables.

## Emoji filenames

Magic Sorter X recognizes many common extensions and prefixes files with matching emoji, including data, documents, source code, images, audio, video, and archives.

It does not add a second emoji prefix when a filename is already prefixed.

## Folder organization

Loose files can be grouped into:

- 🧩 Data
- 📚 Documents
- 💻 Code
- 🖼️ Images
- 🎵 Audio
- 🎬 Video
- 📦 Archives
- 🗂️ Other

Organization is a dry run unless `--apply` is used or you approve the action in the wizard. Existing destination files are never overwritten. Copy mode is available for non-destructive organization.

## Project layout

```text
magic_sorter/
├── examples/
│   ├── foreign.yaml
│   └── sample.json
├── src/
│   └── magic_sorter_x/
│       ├── __init__.py
│       ├── cli.py
│       ├── emojify.py
│       ├── models.py
│       ├── organize.py
│       ├── parsers.py
│       ├── render.py
│       ├── serialize.py
│       ├── terminal.py
│       ├── translation.py
│       ├── tui.py
│       ├── wizard.py
│       └── yaml_codec.py
├── tests/
├── msx.py
├── run_msx.bat
├── run_msx.ps1
├── run_msx.sh
├── run_tests.py
├── README.md
├── RELEASE_NOTES.md
└── THIRD_PARTY_NOTICES.md
```

## Running tests

```text
python run_tests.py
```

The tests use Python's built-in test runner and do not require a separate test framework.

## Replacing the old project

Use this ZIP as the complete project, not as a single-file patch. Back up your current repository, then replace its contents with the contents of this project folder.

Keep the `src`, `tests`, and `examples` folders exactly where they are. The launcher scripts and `msx.py` belong in the project root next to this README.

## Safety

File renaming and folder organization are previews by default. Changes happen only when `--apply` is used or when the wizard explicitly asks and you choose yes. Existing destination files are not overwritten.
