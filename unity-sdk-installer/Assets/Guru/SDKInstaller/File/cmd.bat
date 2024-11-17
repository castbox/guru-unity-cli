@echo off

:: Run as Administrator
set "params=%*"
cd /d "%~dp0" && ( if exist "%temp%\getadmin.vbs" del "%temp%\getadmin.vbs" ) && fsutil dirty query %systemdrive% 1>nul 2>nul || (  echo Set UAC = CreateObject^("Shell.Application"^) : UAC.ShellExecute "cmd.exe", "/k cd ""%~sdp0"" && ""%~s0"" %params%", "", "runas", 1 >> "%temp%\getadmin.vbs" && "%temp%\getadmin.vbs" && exit /B )

set dir=%~dp0
cd %dir%
echo %dir%

:: include all args
call %dir%\args.bat

:: check and download guru-unity-cli
set CLI_HOME=%USERPROFILE%\.guru\unity
set CLI=%CLI_HOME%\guru_unity_cli.py
set CLI_URL=https://raw.githubusercontent.com/castbox/guru-unity-cli/refs/heads/main/cmd/guru_unity_cli.py

:: if not exist "%CLI%" (
echo "Download guru-unity-cli"
curl -o %CLI% %CLI_URL%
::)

:: switch running mode
echo
echo "Run cmd on %RUN_MODE%"

if "%RUN_MODE%"=="install" (
    python %CLI% install --version %VERSION% --proj %PROJECT%
) else if "%RUN_MODE%"=="sync" (
    python %CLI% sync
) else if "%RUN_MODE%"=="debug" (
    python %CLI% debug_source --branch %BRANCH%
)

pause