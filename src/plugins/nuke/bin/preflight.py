from Qt import QtCore
import plugins.nuke.cglnuke as cglnuke
from plugins.nuke.gui import CGLNuke
import plugins.preflight.main
from src.core.config import app_config
from src.core.util import current_user


def launch_(task):
    project_management = app_config()['account_info']['project_management']
    users = app_config()['project_management'][project_management]['users']
    if current_user() in users:
        user_info = users[current_user()]
        if user_info:
            nk_window = CGLNuke(parent=cglnuke.get_main_window(), path=cglnuke.get_file_name(), user_info=user_info)
            gui = plugins.preflight.main.Preflight(parent=nk_window, software='nuke', preflight=task)
            gui.setWindowFlags(QtCore.Qt.Window)
            gui.setWindowTitle('Preflight')
            gui.setAttribute(QtCore.Qt.WA_DeleteOnClose)
            gui.show()
            gui.raise_()
            gui.exec_()
