import path
from cglcore.config import app_config, UserConfig


this = app_config()
that = UserConfig()
print this['paths']['cgl_tools']