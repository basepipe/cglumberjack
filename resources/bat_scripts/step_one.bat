xcopy Z:\02_SYSTEMS\02_SystemConfig\CG_Lumberjack\install_chocolatey.bat "%userprofile%\Desktop" 
xcopy Z:\02_SYSTEMS\02_SystemConfig\CG_Lumberjack\lumbermill.bat "%userprofile%\Desktop" 
xcopy Z:\02_SYSTEMS\02_SystemConfig\CG_Lumberjack\python_requirements.bat "%userprofile%\Desktop"
xcopy Z:\02_SYSTEMS\02_SystemConfig\CG_Lumberjack\python_setup.bat "%userprofile%\Desktop"
xcopy /s Z:\02_SYSTEMS\02_SystemConfig\CG_Lumberjack\copy_user_globals_from_here "%userprofile%\Documents"
setx PYTHONPATH=Z:\02_SYSTEMS\02_SystemConfig\CG_Lumberjack\latest\cglumberjack\src;
setx PATH=%PYTHONPATH%;%PATH%;