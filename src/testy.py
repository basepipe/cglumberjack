import os
from cglcore.config import app_config
from cglcore.util import _execute

code_root = app_config()['paths']['code_root']
command = 'git remote show origin'
os.chdir(code_root)
output = _execute(command, return_output=True, print_output=False)

for line in output:
    if 'master pushes to master' in line:
        if 'up to date' in line:
            print 'up to date'
        else:
            print 'needs updated'
# os.system(command)

