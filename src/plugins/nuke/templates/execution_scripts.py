# This is used to load the shelves in Nuke from CG Lumberjack.
import sys
import os

def load_meuns():
    os.environ["LUMBERJACK_THEME_DEV"] = "1"
    source_dir = r"C:\Users\tmiko\PycharmProjects\cglumberjack\src"
    sys.path.insert(0, source_dir)
    import plugins.nuke.custom_menu as cm
    reload(cm)
    cm.CustomMenu().load_menus()

def launch_cgl():
    main_maya_window = get_nuke_window()

    gui = apps.maya.main.MayaBrowserWindow()

    ui.startup.do_maya_gui_init(gui)

    gui.setParent(main_maya_window)

    gui.setWindowFlags(QtCore.Qt.Window)
    gui.setWindowTitle('Browser')
    gui.setAttribute(QtCore.Qt.WA_DeleteOnClose)
    gui.show()
    gui.raise_()