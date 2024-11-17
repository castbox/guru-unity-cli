@echo off

:: Run as Aministrator
set "params=%*"
cd /d "%~dp0" && ( if exist "%temp%\getadmin.vbs" del "%temp%\getadmin.vbs" ) && fsutil dirty query %systemdrive% 1>nul 2>nul || (  echo Set UAC = CreateObject^("Shell.Application"^) : UAC.ShellExecute "cmd.exe", "/k cd ""%~sdp0"" && ""%~s0"" %params%", "", "runas", 1 >> "%temp%\getadmin.vbs" && "%temp%\getadmin.vbs" && exit /B )


set dir=%~dp0
cd %dir%

echo %dir%

call %dir%\args.bat


:: swtch running mode

echo
echo "Run cmd on %RUN_MODE%"

if "%RUN_MODE%"=="install" (
    python %dir%\guru_unity_cli.py install --version %VERSION% --proj "%PROJECT%"
) else if "%RUN_MODE%"=="sync" (
    python %dir%\guru_unity_cli.py sync
) else if "%RUN_MODE%"=="debug" (
    python %dir%\guru_unity_cli.py debug_source --branch %BRANCH%
)

pause