@echo off
set "ROOT=%~dp0"
where py >nul 2>nul
if %errorlevel%==0 (
    py "%ROOT%msx.py" %*
) else (
    python "%ROOT%msx.py" %*
)
