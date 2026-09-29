# Magic Sorter X 0.3.0

## Added

- Godot `.gd` text extraction to an editable `.msx.txt` format.
- Safe merge of edited text back into a new `.gd` file while preserving non-text source code.
- Byte-for-byte round-trip preservation when no text is changed, including original line endings.
- Godot package file listing, script recovery/decompilation, and PCK/EXE patch integration through optional GDRE Tools.
- Optional `.gd` to `.gdc` compilation during patching when the bytecode/Godot version is supplied.
- A dedicated Godot submenu in the guided wizard.
- Thonny-friendly startup: running `msx.py` with no command always opens the wizard.
- Tests for Godot extraction, merge behavior, round-trip behavior, and CLI parsing.

## Safety behavior

- The original `.gd` file is never overwritten by the Godot merge command.
- The original PCK/EXE is never overwritten by the Godot patch command.
- Existing outputs are rejected unless an explicit overwrite option is available and selected.

## Preserved

- Structured-data viewing and summary tools.
- Translation support and optional translation backends.
- Type-aware emoji filename plans.
- Category-based folder organization.
- Existing dry-run and collision protections.
- Built-in test runner and direct project launch scripts.
