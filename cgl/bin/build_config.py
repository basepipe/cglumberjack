from cgl.plugins.Qt import QtGui, QtWidgets
from cgl.apps.lumbermill import build_config

if __name__ == "__main__":
    # from cgl.core.utils import load_style_sheet
    app = QtWidgets.QApplication([])
    form = build_config.ConfigDialog(root='C:\CGLUMBERJACK')
    form.show()
    # style_sheet = load_style_sheet()
    # app.setStyleSheet(style_sheet)
    app.exec_()