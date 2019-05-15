import os
import pandas as pd
import shutil
from Qt.QtCore import Qt
from Qt import QtWidgets, QtCore, QtGui
from cglcore import path
from cglcore.config import app_config
from cglui.widgets.combo import AdvComboBox
from cglui.widgets.base import LJFileBrowser
from cglui.widgets.search import LJSearchEdit
from cglui.widgets.containers.table import LJTableWidget
from cglui.widgets.containers.model import ListItemModel
from cglui.widgets.containers.menu import LJMenu


class EmptyStateWidget(QtWidgets.QPushButton):
    files_added = QtCore.Signal(object)

    def __init__(self, parent=None, path_object=None):
        QtWidgets.QPushButton.__init__(self, parent)
        self.path_object = path_object
        self.setAcceptDrops(True)
        self.setMinimumWidth(300)
        self.setMinimumHeight(100)
        self.setText('Drag/Drop to Add Files')
        self.setStyleSheet("background-color: white; border:1px dashed black;")
        self.to_path = ''

    def mouseReleaseEvent(self, e):
        super(EmptyStateWidget, self).mouseReleaseEvent(e)

    def dragEnterEvent(self, e):
        if e.mimeData().hasUrls:
            e.accept()
        else:
            e.ignore()

    def dragMoveEvent(self, e):
        if e.mimeData().hasUrls:
            e.setDropAction(QtCore.Qt.CopyAction)
            e.accept()
        else:
            e.ignore()

    def dropEvent(self, e):
        new_obj = self.path_object.copy(task=self.parent().task, version=self.parent().versions.currentText(),
                                        user=self.parent().users.currentText(),
                                        resolutions=self.parent().resolutions.currentText(), filename=None,
                                        ext=None, filename_base=None)
        self.to_path = new_obj.path_root
        if e.mimeData().hasUrls:
            e.setDropAction(QtCore.Qt.CopyAction)
            e.accept()
            file_list = []
            for url in e.mimeData().urls():
                file_list.append(str(url.toLocalFile()))
            self.files_added.emit(file_list)
            print file_list
        else:
            print 'invalid'
            e.ignore()


class FileTableModel(ListItemModel):
    def data(self, index, role):
        row = index.row()
        col = index.column()
        if role == Qt.DisplayRole:
            return self.data_[row][col]
        if role == Qt.DecorationRole:
            data = self.data_[row][col]
            if "." not in data:
                icon_path = os.path.join(path.icon_path(), 'folder2.png')
                return QtWidgets.QIcon(icon_path)
        # if role == Qt.ToolTipRole:
        #     return "hello tom"


class AddAssetModel(ListItemModel):
    def data(self, index, role):
        row = index.row()
        col = index.column()
        if role == Qt.DisplayRole:
            return self.data_[row][col]
        if role == Qt.DecorationRole:
            data = self.data_[row][col]
            if "." not in data:
                icon_path = os.path.join(path.icon_path(), 'folder2.png')
                return QtWidgets.QIcon(icon_path)
        # if role == Qt.ToolTipRole:
        #     return "hello tom"


class FileTable(LJTableWidget):
    files_added = QtCore.Signal(basestring)
    file_selected = QtCore.Signal(object)

    def __init__(self, parent):
        LJTableWidget.__init__(self, parent)
        self.setShowGrid(False)
        self.setAcceptDrops(True)

    def mouseReleaseEvent(self, e):
        super(FileTable, self).mouseReleaseEvent(e)
        self.row_selected()

    def dragEnterEvent(self, e):
        if e.mimeData().hasUrls:
            e.accept()
        else:
            e.ignore()

    def dragMoveEvent(self, e):
        if e.mimeData().hasUrls:
            e.setDropAction(QtCore.Qt.CopyAction)
            e.accept()
        else:
            e.ignore()

    def dropEvent(self, e):
        if e.mimeData().hasUrls:
            e.setDropAction(QtCore.Qt.CopyAction)
            e.accept()
            file_list = []
            for url in e.mimeData().urls():
                file_list.append(str(url.toLocalFile()))
            self.files_added.emit(file_list)
        else:
            print 'invalid'
            e.ignore()


class AssetWidget(QtWidgets.QWidget):
    button_clicked = QtCore.Signal(object)
    filter_changed = QtCore.Signal()

    def __init__(self, parent, title, filter_string=None):
        QtWidgets.QWidget.__init__(self, parent)
        v_layout = QtWidgets.QVBoxLayout(self)
        h_layout = QtWidgets.QHBoxLayout(self)
        self.filter_string = filter_string
        self.label = title
        self.title = QtWidgets.QLabel("<b>%s</b>" % title)
        self.message = QtWidgets.QLabel("")
        self.search_box = LJSearchEdit(self)
        self.button = QtWidgets.QToolButton()
        self.button.setText("+")
        self.data_table = LJTableWidget(self)
        self.data_table.setMinimumHeight(200)

        # this is where the filter needs to be!
        h_layout.addWidget(self.title)
        h_layout.addWidget(self.search_box)
        h_layout.addWidget(self.button)

        v_layout.addLayout(h_layout)
        v_layout.addWidget(self.message)
        v_layout.addWidget(self.data_table, 1)

        self.message.hide()
        self.button.clicked.connect(self.on_button_clicked)

    def setup(self, mdl):
        self.data_table.set_item_model(mdl)
        self.data_table.set_search_box(self.search_box)

    def on_button_clicked(self):
        data = {'title': self.label}
        self.button_clicked.emit(data)

    def set_title(self, new_title):
        self.title.setText('<b>%s</b>' % new_title.title())


class TaskWidget(QtWidgets.QFrame):
    button_clicked = QtCore.Signal(object)
    filter_changed = QtCore.Signal()
    add_clicked = QtCore.Signal()
    assign_clicked = QtCore.Signal(object)
    open_button_clicked = QtCore.Signal()
    new_version_clicked = QtCore.Signal()

    def __init__(self, parent, title, short_title, filter_string=None, path_object=None):
        QtWidgets.QFrame.__init__(self, parent)
        self.setFrameStyle(QtWidgets.QFrame.StyledPanel | QtWidgets.QFrame.Sunken)
        v_layout = QtWidgets.QVBoxLayout(self)
        task_row = QtWidgets.QHBoxLayout()
        self.path_object = path_object
        self.tool_button_layout = QtWidgets.QHBoxLayout()
        self.sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.Maximum)
        self.setSizePolicy(self.sizePolicy)
        self.filter_string = filter_string
        self.label = title
        self.title = QtWidgets.QLabel("<b>%s</b>" % title.title())
        self.task = None
        self.user = None
        self.in_file_tree = None
        self.versions = AdvComboBox()
        # self.versions.setMinimumWidth(200)
        self.versions.hide()
        self.setMinimumWidth(300)
        #self.setMinimumHeight(200)

        self.users_label = QtWidgets.QLabel("User:")
        self.users = AdvComboBox()
        self.users_layout = QtWidgets.QHBoxLayout()
        self.users_layout.addItem(QtWidgets.QSpacerItem(0, 0, QtWidgets.QSizePolicy.Expanding,
                                                        QtWidgets.QSizePolicy.Minimum))
        self.users_layout.addWidget(self.users_label)

        self.users_layout.addWidget(self.users)

        self.resolutions = AdvComboBox()
        self.resolutions_layout = QtWidgets.QHBoxLayout()
        self.resolutions_layout.addItem(QtWidgets.QSpacerItem(0, 0, QtWidgets.QSizePolicy.Expanding,
                                                              QtWidgets.QSizePolicy.Minimum))
        self.resolutions_label = QtWidgets.QLabel("Resolution:")
        self.resolutions_layout.addWidget(self.resolutions_label)
        self.resolutions_layout.addWidget(self.resolutions)
        self.resolutions_layout.setContentsMargins(0, 0, 0, 0)

        # self.search_box = LJSearchEdit(self)
        # self.add_button = QtWidgets.QToolButton()
        # self.add_button.setText("+")
        self.show_button = QtWidgets.QToolButton()
        self.show_button.setText("more")
        self.start_task_button = QtWidgets.QPushButton()
        self.start_task_button.setText("Start Task")
        self.hide_button = QtWidgets.QToolButton()
        self.hide_button.setText("less")
        self.data_table = FileTableWidget(self)
        self.data_table.set_draggable(True)
        self.data_table.title = title
        self.data_table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.data_table.setMinimumHeight(50)
        self.data_table.setMinimumWidth(150)

        # build the tool button row
        self.open_button = QtWidgets.QToolButton()
        self.open_button.setText('Open')
        self.new_version_button = QtWidgets.QToolButton()
        self.new_version_button.setText('Version Up')
        self.review_button = QtWidgets.QToolButton()
        self.review_button.setText('Review')
        self.publish_button = QtWidgets.QToolButton()
        self.publish_button.setText('Publish')
        self.tool_button_layout.addItem(QtWidgets.QSpacerItem(0, 0, QtWidgets.QSizePolicy.Expanding,
                                                              QtWidgets.QSizePolicy.Minimum))
        self.tool_button_layout.addWidget(self.open_button)
        self.tool_button_layout.addWidget(self.new_version_button)
        self.tool_button_layout.addWidget(self.review_button)
        self.tool_button_layout.addWidget(self.publish_button)

        # this is where the filter needs to be!
        task_row.addWidget(self.title)
        task_row.addWidget(self.versions)
        # task_row.addWidget(self.search_box)
        task_row.addWidget(self.show_button)
        task_row.addWidget(self.hide_button)
        # task_row.addWidget(self.assign_button)
        # task_row.addWidget(self.add_button)

        self.empty_state = EmptyStateWidget(path_object=self.path_object)
        self.empty_state.hide()

        v_layout.addLayout(task_row)
        # v_layout.addWidget(self.message)
        v_layout.addWidget(self.start_task_button)
        v_layout.addLayout(self.users_layout)
        v_layout.addLayout(self.resolutions_layout)
        v_layout.addWidget(self.data_table, 1)
        v_layout.addWidget(self.empty_state)
        v_layout.addItem((QtWidgets.QSpacerItem(0, 25, QtWidgets.QSizePolicy.Minimum,
                                                QtWidgets.QSizePolicy.Minimum)))
        v_layout.addLayout(self.tool_button_layout)
        v_layout.addItem((QtWidgets.QSpacerItem(0, 0, QtWidgets.QSizePolicy.Minimum,
                                                QtWidgets.QSizePolicy.MinimumExpanding)))
        self.setLayout(v_layout)
        self.hide_combos()

        self.start_task_button.hide()
        self.hideall()
        self.show_button.clicked.connect(self.on_show_button_clicked)
        self.hide_button.clicked.connect(self.on_hide_button_clicked)
        # self.add_button.clicked.connect(self.on_add_button_clicked)
        self.start_task_button.clicked.connect(self.on_start_task_clicked)
        self.open_button.clicked.connect(self.on_open_button_clicked)
        self.new_version_button.clicked.connect(self.on_new_version_clicked)
        self.hide_tool_buttons()

    def get_category_label(self):
        if self.scope == 'assets':
            return 'Category'
        elif self.scope == 'shots':
            return 'Sequence'

    def hide(self):
        self.hide_button.hide()
        self.add_button.hide()
        self.data_table.hide()
        self.search_box.hide()
        self.show_button.hide()
        self.hide_button.hide()
        self.title.hide()
        self.users.hide()
        self.users_label.hide()
        self.resolutions.hide()
        self.resolutions_label.hide()
        self.assets_radio.hide()
        self.shots_radio.hide()
        self.io_radio.hide()
        self.category_combo.hide()
        self.category_label.hide()

    def show(self, combos=False):
        self.show_button.show()
        self.data_table.show()
        self.search_box.show()
        self.show_button.show()
        self.hide_button.show()
        self.title.show()
        if combos:
            self.show_combos()

    def hide_tool_buttons(self):
        self.open_button.hide()
        self.new_version_button.hide()
        self.publish_button.hide()
        self.review_button.hide()

    def show_filters(self):
        self.category_combo.show()
        self.category_label.show()
        self.assets_radio.show()
        self.shots_radio.show()
        self.io_radio.show()

    def hide_filters(self):
        self.category_combo.hide()
        self.category_label.hide()
        self.assets_radio.hide()
        self.shots_radio.hide()
        self.io_radio.hide()

    def show_tool_buttons(self):
        self.open_button.show()
        self.new_version_button.show()
        self.publish_button.show()
        self.review_button.show()

    def show_combos(self):
        self.users.show()
        self.users_label.show()
        self.resolutions.show()
        self.resolutions_label.show()

    def hide_combos(self):
        self.users.hide()
        self.users_label.hide()
        self.resolutions.hide()
        self.resolutions_label.hide()

    def hideall(self):
        self.hide_button.hide()
        self.data_table.hide()

    def showall(self):
        self.hide_button.show()
        self.show_button.hide()
        self.data_table.show()

    def setup(self, mdl):
        # This is where i add the layout
        self.data_table.set_item_model(mdl)
        self.empty_state.hide()
        if not self.data_table.model().rowCount():
            self.data_table.hide()
            if not self.start_task_button.isVisible():
                self.empty_state.show()
        # self.data_table.set_search_box(self.search_box)

    def on_new_version_clicked(self):
        self.new_version_clicked.emit()

    def on_open_button_clicked(self):
        self.open_button_clicked.emit()

    def on_add_button_clicked(self):
        self.add_clicked.emit()

    def on_show_button_clicked(self):
        self.show_combos()
        self.hide_button.show()
        self.show_button.hide()

    def on_hide_button_clicked(self):
        self.hide_combos()
        self.hide_button.hide()
        self.show_button.show()

    def on_start_task_clicked(self):
        self.assign_clicked.emit(self.path_object)

    def set_title(self, new_title):
        self.title.setText('<b>%s</b>' % new_title.title())


class ProjectWidget(QtWidgets.QWidget):
    button_clicked = QtCore.Signal(object)
    filter_changed = QtCore.Signal()
    add_clicked = QtCore.Signal()
    assign_clicked = QtCore.Signal(object)

    def __init__(self, parent=None, title='', filter_string=None, path_object=None):
        QtWidgets.QWidget.__init__(self, parent)
        v_layout = QtWidgets.QVBoxLayout(self)
        h_layout = QtWidgets.QHBoxLayout()
        self.path_object = path_object
        self.tool_button_layout = QtWidgets.QHBoxLayout()
        self.sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.MinimumExpanding)
        self.setSizePolicy(self.sizePolicy)
        self.filter_string = filter_string
        self.label = title
        self.title = QtWidgets.QLabel("<b>%s</b>" % title)
        self.task = None
        self.user = None

        self.message = QtWidgets.QLabel("")
        # TODO - need to remove the dropdown button on this instance
        self.search_box = LJSearchEdit(self)
        self.add_button = QtWidgets.QToolButton()
        self.add_button.setText("+")
        self.data_table = LJTableWidget(self)
        self.data_table.title = title
        self.data_table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        #self.data_table.setMinimumWidth(220)
        h_layout.addWidget(self.title)
        h_layout.addWidget(self.add_button)

        v_layout.addLayout(h_layout)
        #v_layout.addWidget(self.message)
        v_layout.addWidget(self.search_box)
        v_layout.addWidget(self.data_table, 1)
        # v_layout.setSpacing(10)
        v_layout.setContentsMargins(0, 20, 0, 0)  # left, top, right, bottom

        self.add_button.clicked.connect(self.on_add_button_clicked)

    def setup(self, mdl):
        self.data_table.set_item_model(mdl)
        self.data_table.set_search_box(self.search_box)

    def on_add_button_clicked(self):
        self.add_clicked.emit()

    def on_show_button_clicked(self):
        self.show_combos()
        self.hide_button.show()
        self.show_button.hide()

    def on_hide_button_clicked(self):
        self.hide_combos()
        self.hide_button.hide()
        self.show_button.show()

    def on_assign_button_clicked(self):
        self.assign_clicked.emit(self.path_object)

    def set_title(self, new_title):
        self.title.setText('<b>%s</b>' % new_title.title())

    def hide_all(self):
        self.search_box.hide()
        self.add_button.hide()
        self.data_table.hide()
        self.title.hide()

    def show_all(self):
        self.search_box.show()
        self.add_button.show()
        self.data_table.show()
        self.title.show()


class AssetWidget(QtWidgets.QWidget):
    button_clicked = QtCore.Signal(object)
    filter_changed = QtCore.Signal()
    add_clicked = QtCore.Signal()
    assign_clicked = QtCore.Signal(object)

    def __init__(self, parent, title, filter_string=None, path_object=None):
        QtWidgets.QWidget.__init__(self, parent)
        self.v_layout = QtWidgets.QVBoxLayout(self)
        v_list = QtWidgets.QVBoxLayout()
        scope_layout = QtWidgets.QHBoxLayout()
        self.path_object = path_object
        self.tool_button_layout = QtWidgets.QHBoxLayout()
        self.sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.MinimumExpanding)
        self.setSizePolicy(self.sizePolicy)
        self.filter_string = filter_string
        self.label = title
        #self.title = QtWidgets.QLabel("<h2>Project: %s</h2>" % title)
        self.scope_title = QtWidgets.QLabel("<b>%s</b>" % 'Assets')
        self.task = None
        self.user = None
        minWidth = 340

        self.message = QtWidgets.QLabel("")
        self.message.setMinimumWidth(minWidth)
        self.message.setSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
        self.message.setAlignment(QtCore.Qt.AlignCenter)
        self.search_box = LJSearchEdit(self)
        self.add_button = QtWidgets.QToolButton()
        self.add_button.setText("+")
        self.data_table = LJTableWidget(self)
        self.data_table.title = title
        self.data_table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.data_table.setMinimumWidth(minWidth)

        # build the filter optoins row
        self.assets_radio = QtWidgets.QRadioButton('Assets')
        self.shots_radio = QtWidgets.QRadioButton('Shots')
        self.radio_group_scope = QtWidgets.QButtonGroup(self)
        self.radio_group_scope.addButton(self.shots_radio)
        self.radio_group_scope.addButton(self.assets_radio)

        scope_layout.addWidget(self.scope_title)
        scope_layout.addItem(QtWidgets.QSpacerItem(0, 0, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum))
        scope_layout.addWidget(self.shots_radio)
        scope_layout.addWidget(self.assets_radio)
        scope_layout.addWidget(self.add_button)

        v_list.addItem(QtWidgets.QSpacerItem(0, 3, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Minimum))
        v_list.addWidget(self.search_box)
        v_list.addWidget(self.data_table, 1)

        #self.v_layout.addWidget(self.title)
        self.v_layout.addLayout(scope_layout)
        self.v_layout.addWidget(self.message)
        self.v_layout.addLayout(v_list)
        self.v_layout.setContentsMargins(0, 12, 0, 0)

        self.add_button.clicked.connect(self.on_add_button_clicked)

    def get_category_label(self):
        if self.scope == 'assets':
            return 'Category'
        elif self.scope == 'shots':
            return 'Sequence'

    def setup(self, mdl):
        self.data_table.set_item_model(mdl)
        self.data_table.set_search_box(self.search_box)

    def on_add_button_clicked(self):
        self.add_clicked.emit()

    def on_show_button_clicked(self):
        self.show_combos()
        self.hide_button.show()
        self.show_button.hide()

    def on_hide_button_clicked(self):
        self.hide_combos()
        self.hide_button.hide()
        self.show_button.show()

    def on_assign_button_clicked(self):
        self.assign_clicked.emit(self.path_object)

    def set_title(self, new_title):
        self.title.setText('<h2>Project:  %s</h2>' % new_title.title())

    def set_scope_title(self, new_title):
        self.scope_title.setText('<b>%s</b>' % new_title.title())


class FileTableWidget(LJTableWidget):
    show_in_folder = QtCore.Signal()
    show_in_shotgun = QtCore.Signal()
    copy_folder_path = QtCore.Signal()
    copy_file_path = QtCore.Signal()
    import_version_from = QtCore.Signal()
    push_to_cloud = QtCore.Signal()
    pull_from_cloud = QtCore.Signal()
    share_download_link = QtCore.Signal()

    def __init__(self, parent):
        LJTableWidget.__init__(self, parent)
        # Set The Right Click Menu
        self.horizontalHeader().hide()
        self.item_right_click_menu = LJMenu(self)
        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.item_right_click_menu.create_action("Show In Folder", self.show_in_folder)
        self.item_right_click_menu.create_action("Show In ShotGun", self.show_in_shotgun)
        self.item_right_click_menu.addSeparator()
        self.item_right_click_menu.create_action("Copy Folder Path", self.copy_folder_path)
        self.item_right_click_menu.create_action("Copy File Path", self.copy_file_path)
        self.item_right_click_menu.addSeparator()
        self.item_right_click_menu.create_action("Import Version From...", self.import_version_from)
        self.item_right_click_menu.addSeparator()
        self.item_right_click_menu.create_action("Push", self.push_to_cloud)
        self.item_right_click_menu.create_action("Pull", self.pull_from_cloud)
        self.item_right_click_menu.create_action("Share Download Link", self.share_download_link)
        self.item_right_click_menu.addSeparator()
        # self.item_right_click_menu.create_action("Create Dailies Template", self.create_dailies_template_signal)
        # self.item_right_click_menu.addSeparator()
        self.customContextMenuRequested.connect(self.item_right_click)
        self.setAcceptDrops(True)
        self.setMaximumHeight(self.height_hint)

    def item_right_click(self, position):
        self.item_right_click_menu.exec_(self.mapToGlobal(position))

    def dragEnterEvent(self, e):
        if e.mimeData().hasUrls:
            e.accept()
        else:
            e.ignore()

    def dragMoveEvent(self, e):
        if e.mimeData().hasUrls:
            e.setDropAction(QtCore.Qt.CopyAction)
            e.accept()
        else:
            e.ignore()