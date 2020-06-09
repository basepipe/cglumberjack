@echo off

:: BatchGotAdmin
:-------------------------------------
REM  --> Check for permissions
>nul 2>&1 "%SYSTEMROOT%\system32\cacls.exe" "%SYSTEMROOT%\system32\config\system"

REM --> If error flag set, we do not have admin.
if '%errorlevel%' NEQ '0' (
    echo Requesting administrative privileges...
    goto UACPrompt
) else ( goto gotAdmin )

:UACPrompt
    echo Set UAC = CreateObject^("Shell.Application"^) > "%temp%\getadmin.vbs"
    set params = %*:"=""
    echo UAC.ShellExecute "cmd.exe", "/c %~s0 %params%", "", "runas", 1 >> "%temp%\getadmin.vbs"

    "%temp%\getadmin.vbs"
    del "%temp%\getadmin.vbs"
    exit /B

:gotAdmin
    pushd "%CD%"
    CD /D "%~dp0"
:--------------------------------------

if not exist "%USERPROFILE%\PycharmProjects" mkdir "%USERPROFILE%\PycharmProjects"
if not exist "%USERPROFILE%\PycharmProjects\cglumberjack" git clone https://github.com/basepipe/cglumberjack.git %HOMEPATH%\PycharmProjects\cglumberjack
cd %USERPROFILE%\PycharmProjects\cglumberjack
pip install -r requirements.txt
setx PYTHONPATH "%PYTHONPATH%;%USERPROFILE%\PycharmProjects\cglumberjack\cgl;%USERPROFILE%\PycharmProjects\cglumberjack"
setx CGL_USER_GLOBALS "%USERPROFILE%\Documents\cglumberjack\user_globals.json"
