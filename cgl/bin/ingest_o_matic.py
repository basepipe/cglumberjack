from cgl.plugins.Qt import QtCore, QtGui, QtWidgets
import apps.lumbermill.elements.IOPanel as IoP
from cgl.core.path import PathObject
from cgl.core.utils.general import load_style_sheet


class IngestDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        QtWidgets.QDialog.__init__(self, parent)
        self.layout = QtWidgets.QVBoxLayout(self)
        temp = r'Y:/CGLUMBERJACK/COMPANIES/forge/source/vr_scout/shots/010/0021/cam/tmikota/000.000/high/2020_10_21_10_55_36.mkv'
        io_widget = IoP.IOPanel(path_object=PathObject(temp))
        self.layout.addWidget(io_widget)


if __name__ == '__main__':
    app = QtWidgets.QApplication([])
    form = IngestDialog()
    form.show()
    style_sheet = load_style_sheet()
    app.setStyleSheet(style_sheet)
    app.exec_()
