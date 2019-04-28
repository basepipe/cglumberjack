from Qt import QtWidgets, QtCore, QtGui
from cglui.widgets.base import LJMainWindow

class FrameTest(QtWidgets.QFrame):
    def __init__(self):
        QtWidgets.QFrame.__init__(self)
        self.setFrameStyle(QtWidgets.QFrame.StyledPanel | QtWidgets.QFrame.Sunken)

        v_layout = QtWidgets.QVBoxLayout()
        button1 = QtWidgets.QPushButton('One')
        button2 = QtWidgets.QPushButton('two')

        v_layout.addWidget(button1)
        v_layout.addWidget(button2)
        self.setLayout(v_layout)

class Widget(QtWidgets.QWidget):
    def __init__(self):
        QtWidgets.QWidget.__init__(self)
        self.setLayout(QtWidgets.QVBoxLayout())
        self.layout().addWidget(FrameTest())
        self.layout().addWidget(FrameTest())

class GUI(LJMainWindow):
    def __init__(self):
        LJMainWindow.__init__(self)
        self.setCentralWidget(Widget())



if __name__ == "__main__":
    from cglui.startup import do_gui_init
    app = do_gui_init()
    td = GUI()
    td.show()
    td.raise_()
    # setup stylesheet
    app.exec_()
