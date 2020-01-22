from cgl.plugins.Qt import QtCore
from plugins.preflight.main import Preflight


def launch_(parent, task, path_object, do_review=True):
    print 'Do Review = %s' % do_review
    pf_mw = Preflight(parent=parent, software='lumbermill', preflight=task, path_object=path_object, do_review=True)
    pf_mw.setWindowTitle('%s Preflight' % task.title())
    pf_mw.setAttribute(QtCore.Qt.WA_DeleteOnClose)
    pf_mw.show()
    pf_mw.raise_()


