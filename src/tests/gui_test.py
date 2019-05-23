from PySide2 import QtWidgets


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        self.construct_ui()

    def construct_ui(self):
        self.setWindowTitle('PySide2 Test')

        # match look & feel to H16
        self.setProperty("houdiniStyle", True)

        # main widget
        main_widget = QtWidgets.QWidget(self)
        self.setCentralWidget(main_widget)

        # layout initialize
        g_layout = QtWidgets.QVBoxLayout()
        layout = QtWidgets.QFormLayout()
        main_widget.setLayout(g_layout)

        # Add Widgets
        self.parm = QtWidgets.QSpinBox()
        self.parm.setValue(30)
        layout.addRow('Parameter', self.parm)
        self.exec_btn = QtWidgets.QPushButton('Execute')

        # global layout setting
        g_layout.addLayout(layout)
        g_layout.addWidget(self.exec_btn)

w = MainWindow()
w.show()
