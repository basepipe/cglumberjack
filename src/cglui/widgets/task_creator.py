from Qt import QtCore, QtGui
from Qt import QtWidgets

from cglui.widgets.base import LJDialog
from cglui.widgets.combo import AdvComboBox


class TaskCreator(LJDialog):
    def __init__(self, parent=None, title="Title", message="Message"):
        LJDialog.__init__(self, parent)
        QtWidgets.QFormLayout()
        tasks = AdvComboBox()
        names = ['bob', 'fred', 'bobby', 'frederick', 'charles', 'charlie', 'rob']

        # fill the standard model of the combobox
        tasks.addItems(names)


if __name__ == "__main__":
    import sys

    app = QtGui.QApplication(sys.argv)
    combo = TaskCreator()
    combo.show()

    sys.exit(app.exec_())