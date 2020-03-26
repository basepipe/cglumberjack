@ECHO off
set save=%USERPROFILE%\cglumberjack\CGL-time-sheets.json
aws --no-sign-request s3 cp s3://cglumberjack-development/time_sheets/CGL-time-sheets-5b6701ce257c.json %save%
FOR /F "skip=1" %%I IN ( 'syncthing -paths' ) DO (
    set cfg=%%I
    goto config
)

:config
echo %cfg%