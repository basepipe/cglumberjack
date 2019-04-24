from Qt import QtCore, QtGui, QtWidgets
from cglui.widgets.base import LJMainWindow

VIEWS = {'3d Assets': ['mdl', 'rig', 'tex', 'shd'],
         'Shots': ['prev', 'anim', 'lite', 'comp']}


class AssetWidget(QtWidgets.QWidget):
    status_clicked = QtCore.Signal(object)
    user_clicked = QtCore.Signal(object)
    priority_clicked = QtCore.Signal(object)
    date_clicked = QtCore.Signal(object)

    def __init__(self):
        QtWidgets.QWidget.__init__(self)
        # self.setStyleSheet("border: 1px solid black")
        layout = QtWidgets.QVBoxLayout()


        # TODO - figure out the text sizing for this label as well as the fonts.
        self.priority = QtWidgets.QLabel('Priority:')
        self.priority.setStyleSheet("border: 0px")
        self.date = QtWidgets.QLabel('Due: ')
        self.date.setStyleSheet("border: 0px")
        self.user = QtWidgets.QLabel('tmikota')
        self.user.setStyleSheet("border: 0px")
        self.status = QtWidgets.QLabel('Ready To Start')
        self.status.setStyleSheet("border: 0px")
        self.name = QtWidgets.QLabel('<b>King Kong</b>')
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
        self.label = QtWidgets.QLabel(label) # TODO: Center this label
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


class ButtonBar(QtWidgets.QHBoxLayout):
    view_changed = QtCore.Signal()
    graph_clicked = QtCore.Signal()
    connections_clicked = QtCore.Signal()
    focus_clicked = QtCore.Signal()

    def __init__(self):
        QtWidgets.QHBoxLayout.__init__(self)
        self.label = QtWidgets.QLabel('View: ')
        self.combo = QtWidgets.QComboBox()
        for each in VIEWS:
            self.combo.addItem(each)
        self.connections_button = QtWidgets.QToolButton()
        self.graph_button = QtWidgets.QToolButton()
        self.focus_button = QtWidgets.QToolButton()
        self.addWidget(self.label)
        self.addWidget(self.combo)
        self.addWidget(self.connections_button)
        self.addWidget(self.graph_button)
        self.addWidget(self.focus_button)
        self.addItem(QtWidgets.QSpacerItem(0, 0, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum))


class Foreman(LJMainWindow):
    def __init__(self):
        LJMainWindow.__init__(self)
        central_widget = QtWidgets.QWidget(self)
        self.setCentralWidget(central_widget)
        self.vertical_layout = QtWidgets.QVBoxLayout()
        self.swim_lanes_layout = QtWidgets.QHBoxLayout()



        self.vertical_layout.addLayout(ButtonBar())
        self.vertical_layout.addLayout(self.swim_lanes_layout)
        central_widget.setLayout(self.vertical_layout)

        self.load_swim_lanes()

    def load_swim_lanes(self):
        for each in VIEWS['3d Assets']:
            layout = SwimLane(label=each)
            self.swim_lanes_layout.addLayout(layout)

    def load_assets_into_lanes(self):
        pass



if __name__ == "__main__":
    from cglui.startup import do_gui_init
    app = do_gui_init()
    td = Foreman()
    td.setWindowTitle('Foreman')
    td.show()
    td.raise_()
    app.exec_()


