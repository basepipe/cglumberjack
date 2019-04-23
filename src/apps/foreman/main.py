from Qt import QtCore, QtGui, QtWidgets
from cglui.widgets.base import LJDialog, LJMainWindow


class AssetWidget(QtWidgets.QWidget):
    status_clicked = QtCore.Signal(object)
    user_clicked = QtCore.Signal(object)
    priority_clicked = QtCore.Signal(object)
    date_clicked = QtCore.Signal(object)

    def __init__(self):
        QtWidgets.QWidget.__init__(self)
        # self.setStyleSheet("border: 1px solid black")
        layout = QtWidgets.QVBoxLayout()

        self.priority = QtWidgets.QLabel('Priority:')
        self.priority.setStyleSheet("border: 0px")
        self.date = QtWidgets.QLabel('Due: ')
        self.date.setStyleSheet("border: 0px")
        self.user = QtWidgets.QLabel('tmikota')
        self.user.setStyleSheet("border: 0px")
        self.status = QtWidgets.QLabel('Ready To Start')
        self.status.setStyleSheet("border: 0px")
        self.name = QtWidgets.QLabel('King Kong')
        self.name.setStyleSheet("border: 0px")
        self.thumbpath = ''

        top_row = QtWidgets.QHBoxLayout()
        top_row.addWidget(self.priority)
        top_row.addItem(QtWidgets.QSpacerItem(0, 0, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum))
        top_row.addWidget(self.date)

        middle_row = QtWidgets.QHBoxLayout()
        middle_row.addItem(QtWidgets.QSpacerItem(0, 0, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum))
        middle_row.addWidget(self.name)
        middle_row.addItem(QtWidgets.QSpacerItem(0, 0, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum))

        bottom_row = QtWidgets.QHBoxLayout()
        bottom_row.addWidget(self.user)
        middle_row.addItem(QtWidgets.QSpacerItem(0, 0, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum))
        bottom_row.addWidget(self.status)

        layout.addLayout(top_row)
        layout.addLayout(middle_row)
        layout.addLayout(bottom_row)
        self.setLayout(layout)
        #self.setFixedWidth(230)
        self.setFixedHeight(70)

        self.priority.mousePressEvent = self.priority_press
        self.priority.mouseReleaseEvent = self.priority_release
        self.user.mousePressEvent = self.user_press
        self.user.mouseReleaseEvent = self.user_release
        self.status.mousePressEvent = self.status_press
        self.status.mouseReleaseEvent = self.status_release
        self.date.mousePressEvent = self.date_press
        self.date.mouseReleaseEvent = self.date_release

    def priority_press(self, event):
        self.priority.setStyleSheet('color: blue')

    def priority_release(self, event):
        self.priority.setStyleSheet('color: black')
        self.priority_clicked.emit('priority')

    def user_press(self, event):
        self.user.setStyleSheet('color: blue')

    def user_release(self, event):
        self.user.setStyleSheet('color: black')
        self.user_clicked.emit('user')

    def date_press(self, event):
        self.date.setStyleSheet('color: blue')

    def date_release(self, event):
        self.date.setStyleSheet('color: black')
        self.date_clicked.emit('date')

    def status_press(self, event):
        self.status.setStyleSheet('color: blue')

    def status_release(self, event):
        self.status.setStyleSheet('color: black')
        self.status_clicked.emit('status')




class SwimLane(QtWidgets.QVBoxLayout):
    def __init__(self, label):
        QtWidgets.QVBoxLayout.__init__(self)
        self.label = QtWidgets.QLabel(label)
        self.list_widget = QtWidgets.QListWidget()
        self.list_widget.setMinimumWidth(230)

        self.addWidget(self.label)
        self.addWidget(self.list_widget)

    def add_item(self, widget):
        item = QtGui.QListWidgetItem(self.list_widget)
        item.setSizeHint(widget.sizeHint())
        # Set size hint
        # Add QListWidgetItem into QListWidget
        self.list_widget.addItem(item)
        self.list_widget.setItemWidget(item, widget)

class Foreman(LJMainWindow):
    def __init__(self):
        LJMainWindow.__init__(self)
        central_widget = QtWidgets.QWidget(self)
        self.setCentralWidget(central_widget)
        swim_lanes_layout = QtWidgets.QHBoxLayout()
        central_widget.setLayout(swim_lanes_layout)
        model_layout = SwimLane(label='Modelling')
        test = AssetWidget()
        test2 = AssetWidget()
        swim_lanes_layout.addLayout(model_layout)
        model_layout.add_item(test)
        model_layout.add_item(test2)



if __name__ == "__main__":
    from cglui.startup import do_gui_init
    app = do_gui_init()
    td = Foreman()
    td.setWindowTitle('Foreman')
    td.show()
    td.raise_()
    app.exec_()


