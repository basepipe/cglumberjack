

print 'This module simply sets all the needed env vars for lumbermill after a user_globals.json file and a globals.json file have been craeted'

# app_config()['paths']['code_root'] must be in PYTHONPATH
# app_config()['paths']['cgl_tools'] must be in PYTHONPATH
# os.dirname(app_config()['paths']['config']) must be in PYTHONPATH