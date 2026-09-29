# Godot text workflow — quick start

## In Thonny

1. Open `msx.py`.
2. Press **F5** / **Run current script**.
3. Choose **3. Godot text/game tools**.

## Edit an existing `.gd` text file

1. Choose **Extract text from a .gd file**.
2. Select your original file, for example `questtext.gd`.
3. Edit the generated `questtext.msx.txt`.
   - Keep every `@@MSX:...` marker unchanged.
   - Keep the first `|` on each editable text line.
4. Run Sorter again and choose **Paste edited text back into a new .gd file**.
5. Select the original `.gd`, then the edited `.msx.txt`.
6. Sorter creates `questtext_patched.gd` by default and leaves the original unchanged.

## Recover a `.gd` from a released Godot game

Package-level recovery needs the optional **GDRE Tools** executable.

Put `gdre_tools.exe`:

- next to `msx.py`, or
- inside a `tools` folder next to `msx.py`, or
- somewhere on `PATH`.

Then choose **Recover/decompile scripts from a game package** and select the game's `.pck`, `.exe`, or `.apk`.

If you know the original script path/name, an include glob can reduce the recovery scope, for example:

```text
res://**/questtext.gdc
```

After recovery, use the normal extract/edit/import workflow on the recovered `.gd`.

## Put an edited script back into a package

Choose **Patch an edited script into a new PCK/EXE**.

You need the exact original resource path, such as:

```text
res://scripts/questtext.gd
```

If the original resource is compiled (`.gdc`) and your edited file is `.gd`, enter the engine/bytecode version reported during recovery. Sorter will ask GDRE Tools to compile it before patching.

Sorter always writes a new patched package and does not overwrite the original.
