from cgl.plugins.Qt import QtGui, QtWidgets


class LJMenu(QtWidgets.QMenu):
    def __init__(self, parent):
        QtWidgets.QMenu.__init__(self, parent)

    def create_action(self, name, trigger=None, checkable=False):
        action = QtWidgets.QAction(name, self)
        if trigger:
            action.triggered[()].connect(trigger)
        if checkable:
            action.setCheckable(True)
        self.addAction(action)
