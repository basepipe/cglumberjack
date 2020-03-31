from PySide import QtCore
import plugins.preflight.main
from cgl.core.config import app_config
from cgl.core.utils.general import current_user

CONFIG = app_config()

def launch_(task):
    project_management = CONFIG['account_info']['project_management']
    users = CONFIG['project_management'][project_management]['users']
    if current_user() in users:
        user_info = users[current_user()]
        if user_info:
            gui = plugins.preflight.main.Preflight(parent=None, software='nuke', preflight=task)
            gui.setWindowFlags(QtCore.Qt.Window)
            gui.setWindowTitle('Preflight')
            gui.setAttribute(QtCore.Qt.WA_DeleteOnClose)
            gui.show()
            gui.raise_()
            gui.exec_()
