from PySide2 import QtCore
from apps.cglumberjack.main import CGLumberjack, CGLumberjackWidget
import cglnuke
import cglui.startup as ui




class NukeBrowserWidget(CGLumberjackWidget):
    def __init__(self, parent=None):
        super(NukeBrowserWidget, self).__init__(parent=parent)
        print 'the best'


class CGLNuke(CGLumberjack):
    def __init__(self):
        super(CGLNuke, self).__init__()
        self.setCentralWidget(NukeBrowserWidget(self))


def launch():
    print 'yes!'
    main_window = cglnuke.get_main_window()
    gui = CGLNuke()
    ui.startup.do_maya_gui_init(gui)
    gui.setParent(main_window)
    gui.setWindowFlags(QtCore.Qt.Window)
    gui.setWindowTitle('CG LUmberjack')
    gui.setAttribute(QtCore.Qt.WA_DeleteOnClose)
    gui.show()
    gui.raise_()
