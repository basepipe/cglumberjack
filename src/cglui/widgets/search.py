from Qt import QtWidgets
from Qt import QtCore
from Qt import QtTest


class LJSearchEdit(QtWidgets.QLineEdit):
    def __init__(self, parent):
        QtWidgets.QLineEdit.__init__(self, parent)
        QtWidgets.QLineEdit.setPlaceholderText(self, self.tr("Type to Filter"))
        self.button = QtWidgets.QToolButton(self)
        self.button.setObjectName("search_cancel_button")
        self.layout = QtWidgets.QHBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.addWidget(self.button, 0, QtCore.Qt.AlignRight)
        self.button.clicked.connect(self.cancel_clicked)

    def cancel_clicked(self):
        QtWidgets.QLineEdit.setText(self, "")
        QtTest.QTest.keyClick(self, QtCore.Qt.Key_Return)
