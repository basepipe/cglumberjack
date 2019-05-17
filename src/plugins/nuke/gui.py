from Qt import QtWidgets, QtCore, QtGui
from apps.cglumberjack.main import CGLumberjack, CGLumberjackWidget
import nuke
import cglnuke
import cglui.startup as startup


class NukeBrowserWidget(CGLumberjackWidget):
    def __init__(self, parent=None, user_name=None, user_email=None, company=None, path=None, radio_filter=None,
                 show_import=False):
        super(NukeBrowserWidget, self).__init__(parent=parent, path=path, show_import=show_import)
        print 'path: ', path
        print 'the best'

    def open_clicked(self):
        print self.path_object.path_root
        print 'open nuke'

    def import_clicked(self):
        print self.path_object.path_root
        cglnuke.import_media(self.path_object.path_root)
        print 'nuke import'


class CGLNuke(CGLumberjack):
    def __init__(self, parent=None, path=None):
        super(CGLNuke, self).__init__()
        print 'CGLNuke path is %s' % path
        self.setCentralWidget(NukeBrowserWidget(self, user_name=None, user_email=None, company=None, path=path,
                                                radio_filter=None, show_import=True))


def launch():
    gui = CGLNuke(parent=cglnuke.get_main_window(), path=cglnuke.get_file_name())
    startup.do_nuke_gui_init(gui)
    gui.setWindowFlags(QtCore.Qt.Window)
    gui.setWindowTitle('CG LUmberjack')
    gui.setAttribute(QtCore.Qt.WA_DeleteOnClose)
    gui.show()
    gui.raise_()
    gui.exec_()
