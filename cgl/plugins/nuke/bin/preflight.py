from PySide import QtCore
import plugins.nuke.cgl_nuke as cgl_nuke
from plugins.nuke.gui import CGLNuke
import plugins.preflight.main
from cgl.core.config import app_config
from cgl.core.util import current_user


def launch_(task):
    project_management = app_config()['account_info']['project_management']
    users = app_config()['project_management'][project_management]['users']
    if current_user() in users:
        user_info = users[current_user()]
        if user_info:
            nk_window = CGLNuke(parent=cgl_nuke.get_main_window(), path=cgl_nuke.get_file_name(), user_info=user_info)
            gui = plugins.preflight.main.Preflight(parent=nk_window, software='nuke', preflight=task)
            gui.setWindowFlags(QtCore.Qt.Window)
            gui.setWindowTitle('Preflight')
            gui.setAttribute(QtCore.Qt.WA_DeleteOnClose)
            gui.show()
            gui.raise_()
            gui.exec_()
