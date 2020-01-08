from PySide import QtGui


class LJMenu(QtGui.QMenu):
    def __init__(self, parent):
        QtGui.QMenu.__init__(self, parent)

    def create_action(self, name, trigger=None, checkable=False):
        action = QtGui.QAction(name, self)
        if trigger:
            action.triggered[()].connect(trigger)
        if checkable:
            action.setCheckable(True)
        self.addAction(action)
