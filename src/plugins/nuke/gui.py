from Qt import QtWidgets, QtCore, QtGui
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
    gui = CGLNuke()
    ui.startup.do_nuke_gui_init(gui)
    gui.setWindowFlags(QtCore.Qt.Window)
    gui.setWindowTitle('CG LUmberjack')
    gui.setAttribute(QtCore.Qt.WA_DeleteOnClose)
    gui.show()
    gui.raise_()
