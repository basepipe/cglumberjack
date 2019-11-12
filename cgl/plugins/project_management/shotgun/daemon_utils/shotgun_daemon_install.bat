if not exist "C:\CGLUMBERJACK\shotgun" mkdir C:\CGLUMBERJACK\shotgun
cd /D C:\CGLUMBERJACK\shotgun
git clone https://github.com/shotgunsoftware/python-api.git
SETX /M PYTHONPATH "%PYTHONPATH%;C:\CGLUMBERJACK\shotgun\python-api"
SETX /M PATH "%PATH%;%PYTHONPATH%"
SETX /M SG_SERVER "https://fsuada.shotgunstudio.com"
SETX /M SGDAEMON_TSUES_NAME "core_tools"
SETX /M SGDAEMON_TSUES_KEY "bc29cd2fd4ce9fe3c2598c4d559b09f88eaa95b05edfd12a834a23aea0797e2f"
git clone git://github.com/shotgunsoftware/shotgunEvents.git
cd /D C:\CGLUMBERJACK\shotgun\shotgunEvents\src
python shotgunEventDaemon.py install