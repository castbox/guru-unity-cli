@echo off

:: ======== RUN AS Admin =========
:: %1 %2
:: ver|find "5.">nul&&goto :Admin
:: mshta vbscript:createobject("shell.application").shellexecute("%~s0","goto :Admin","","runas",1)(window.close)&goto :eof
:: :Admin

set dir=%~dp0
cd %dir%

echo %dir%

call %dir%\args.bat
echo %VALUE%

:: python %dir%\guru_unity_cli.py test
python %dir%\guru_unity_cli.py debug_source --branch %TAG%

pause