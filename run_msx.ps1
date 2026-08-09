$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Python = Get-Command py -ErrorAction SilentlyContinue
if ($Python) {
    & py "$Root\msx.py" @args
} else {
    & python "$Root\msx.py" @args
}
exit $LASTEXITCODE
