import sys
import os
os.environ["LUMBERJACK_THEME_DEV"] = "1"
source_dir = r"C:\Users\tmiko\PycharmProjects\cglumberjack\src"
sys.path.insert(0, source_dir)
python_dev_packages = r'C:\Python27\Lib\site-packages'
sys.path.insert(0, python_dev_packages)

# run this code with ctrl+enter if there are new shelves to grab
import plugins.CustomMenu as CustomMenu
reload(CustomMenu)
import plugins.maya.custom_menu as cm
reload(cm)

cm.MayaCustomMenu().load_menus()

