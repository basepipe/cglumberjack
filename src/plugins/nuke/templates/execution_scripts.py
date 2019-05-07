# This is used to load the shelves in Nuke from CG Lumberjack.

import sys
import os

os.environ["LUMBERJACK_THEME_DEV"] = "1"
source_dir = r"C:\Users\tmiko\PycharmProjects\cglumberjack\src"
sys.path.insert(0, source_dir)
from plugins.nuke import shelves
reload(shelves)
shelves.load_shelves()