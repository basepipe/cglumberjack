from Qt import QtCore
import plugins.nuke.cglnuke as cglnuke
from plugins.nuke.gui import CGLNuke
import plugins.preflight.main


def launch_(task):
    nk_window = CGLNuke(parent=cglnuke.get_main_window(), path=cglnuke.get_file_name())
    gui = plugins.preflight.main.Preflight(parent=nk_window, software='nuke', preflight=task)
    gui.setWindowFlags(QtCore.Qt.Window)
    gui.setWindowTitle('Preflight')
    gui.setAttribute(QtCore.Qt.WA_DeleteOnClose)
    gui.show()
    gui.raise_()
    gui.exec_()
