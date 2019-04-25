import os
from Qt import QtCore, QtGui, QtWidgets
from cglui.widgets.base import LJMainWindow
import core.assetcore as ac
from core.config import app_config


VIEWS = {'All Assets': ['mdl', 'rig', 'tex', 'shd'],
         'Rigged Assets': ['mdl', 'rig', 'tex', 'shd'],
         'Simple Assets': ['mdl', 'tex', 'shd'],
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
        self.label = QtWidgets.QLabel(label.title())
        self.label.setAlignment(QtCore.Qt.AlignCenter)
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

        self.button_bar = ButtonBar()

        self.vertical_layout.addLayout(self.button_bar)
        self.vertical_layout.addLayout(self.swim_lanes_layout)
        central_widget.setLayout(self.vertical_layout)

        self.load_swim_lanes()
        self.load_assets_into_lanes()
        self.button_bar.combo.currentIndexChanged.connect(self.load_swim_lanes)

    def load_swim_lanes(self):
        self.clear_layout(self.swim_lanes_layout)
        var = self.button_bar.combo.currentText()
        for each in VIEWS[var]:
            layout = SwimLane(label=each)
            self.swim_lanes_layout.addLayout(layout)

    def load_assets_into_lanes(self):
        self.load_project_json()

    def clear_layout(self, layout):
        while layout.count():
            child = layout.takeAt(0)
            if child.widget() is not None:
                child.widget().deleteLater()
            elif child.layout() is not None:
                self.clear_layout(child.layout())

    def load_project_json(self):
        json_file = r'Z:\Projects\VFX\render\19F3_2019_Lucia\19F3_2019_Lucia.json'
        layout_data = ac.readJson(json_file)
        for each in layout_data:
            if layout_data[each]['scope'] == 'assets':
                print layout_data[each]['name']
                if layout_data[each]['json']:
                    self.load_asset_json(layout_data[each]['json'])

        # read the json file
        # find all the assets

    def load_asset_json(self, asset, json):
        # add root to the json file
        simple_asset_dict = {asset: {'rig': {'status': 'ignored',
                                             'due': 'None',
                                             'assigned': 'not assigned'
                                             },
                                     'mdl': {'status': 'not started',
                                             'due': 'None',
                                             'assigned': 'not assigned'
                                             },
                                     'shd': {'status': 'not started',
                                             'due': 'None',
                                             'assigned': 'not assigned'
                                             },
                                     'tex': {'status': 'not started',
                                             'due': 'None',
                                             'assigned': 'not assigned'
                                             }
                                     }

                             }
        root = app_config()['paths']['root']
        root = r'Z:/Projects/VFX'
        json_with_root = '%s%s' % (root, json)
        asset_data = ac.readJson(json_with_root)
        for task in asset_data:
            if asset_data[task]['status']:
                simple_asset_dict[asset][task]['status'] = asset_data[task]['status']
            if asset_data[task]['due']:
                print 'due date found'
            if asset_data[task]['assigned']:
                print 'assignment found'

        for task in simple_asset_dict:
            print task
            # add the asset item if the status matches properly




if __name__ == "__main__":
    from cglui.startup import do_gui_init
    app = do_gui_init()
    td = Foreman()
    td.setWindowTitle('Foreman')
    td.show()
    td.raise_()
    app.exec_()


