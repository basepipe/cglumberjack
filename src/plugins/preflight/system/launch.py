from Qt import QtCore
from plugins.preflight.main import Preflight


def launch_(parent, task):
    pf_mw = Preflight(parent=parent, software='system', preflight=task)
    pf_mw.setWindowTitle('Preflight')
    pf_mw.setAttribute(QtCore.Qt.WA_DeleteOnClose)
    pf_mw.show()
    pf_mw.raise_()


