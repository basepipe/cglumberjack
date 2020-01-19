from PySide import QtGui
from PySide import QtCore
# noinspection PyUnresolvedReferences

class LJSearchEdit(QtGui.QLineEdit):
    def __init__(self, parent, button=False):
        QtGui.QLineEdit.__init__(self, parent)
        QtGui.QLineEdit.setPlaceholderText(self, self.tr("Type to Filter"))
        self.setSizePolicy(QtGui.QSizePolicy.MinimumExpanding, QtGui.QSizePolicy.Minimum)
        self.button = QtGui.QToolButton(self)
        self.button.setObjectName("search_cancel_button")
        self.layout = QtGui.QHBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.addWidget(self.button, 0, QtCore.Qt.AlignRight)
        self.button.clicked.connect(self.cancel_clicked)
        self.button.hide()
        if button:
            self.button.show()
        self.setProperty('class', 'medium_grey_rounded')
        self.setMinimumWidth(250)

    def cancel_clicked(self):
        from PySide import QtTest
        QtGui.QLineEdit.setText(self, "")
        QtTest.QTest.keyClick(self, QtCore.Qt.Key_Return)
