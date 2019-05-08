# This is used to load the shelves in Nuke from CG Lumberjack.

import sys
import os

os.environ["LUMBERJACK_THEME_DEV"] = "1"
source_dir = r"C:\Users\tmiko\PycharmProjects\cglumberjack\src"
sys.path.insert(0, source_dir)
import plugins.nuke.custom_menu as cm
reload(cm)
cm.CustomMenu().load_menus()