import os
from Qt.QtCore import Qt
from Qt import QtWidgets, QtCore, QtGui
from cglcore import path
from cglui.widgets.combo import AdvComboBox
from cglui.widgets.search import LJSearchEdit
from cglui.widgets.containers.table import LJTableWidget
from cglui.widgets.containers.model import ListItemModel
from cglui.widgets.containers.menu import LJMenu


class VersionButton(QtWidgets.QPushButton):

    def __init__(self, parent):
        QtWidgets.QPushButton.__init__(self, parent)
        self.menu = QtWidgets.QMenu()
        self.setText(self.tr("Version Up"))
        self.empty_act = self.menu.addAction(self.tr("Empty"))
        self.empty_act.setToolTip(self.tr("Create a new empty version"))
        self.empty_act.triggered.connect(lambda: self.parent().create_empty_version.emit())
        self.selected_act = self.menu.addAction(self.tr("Copy Current Version"))
        self.selected_act.triggered.connect(lambda: self.parent().copy_selected_version.emit())
        self.selected_act.setToolTip(self.tr("Create a new version copying from current version"))
        self.latest_act = self.menu.addAction(self.tr("Copy Latest Version"))
        self.latest_act.triggered.connect(lambda: self.parent().copy_latest_version.emit())
        self.latest_act.setToolTip(self.tr("Create a new version copying from the latest version"))
        self.setMenu(self.menu)

    def set_new_version(self):
        self.selected_act.setVisible(False)
        self.latest_act.setVisible(False)
        self.setEnabled(True)

    def set_version_selected(self):
        self.selected_act.setVisible(True)
        self.latest_act.setVisible(True)
        self.setEnabled(True)


# noinspection PyPep8Naming,PyPep8Naming,PyPep8Naming,PyPep8Naming
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
        self.to_object = None

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
                                        resolution=self.parent().resolutions.currentText(), filename=None,
                                        ext=None, filename_base=None)
        self.to_path = new_obj.path_root
        self.to_object = new_obj
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


class TaskWidget(QtWidgets.QFrame):
    button_clicked = QtCore.Signal(object)
    filter_changed = QtCore.Signal()
    add_clicked = QtCore.Signal()
    start_task_clicked = QtCore.Signal(object)
    open_button_clicked = QtCore.Signal()
    import_button_clicked = QtCore.Signal()
    new_version_clicked = QtCore.Signal()
    create_empty_version = QtCore.Signal()
    copy_selected_version = QtCore.Signal()
    copy_latest_version = QtCore.Signal()

    def __init__(self, parent, title, filter_string=None, path_object=None, show_import=False):
        QtWidgets.QFrame.__init__(self, parent)
        self.setFrameStyle(QtWidgets.QFrame.StyledPanel | QtWidgets.QFrame.Sunken)
        self.setAutoFillBackground(True)
        p = self.palette()
        brightness = 235
        p.setColor(self.backgroundRole(), QtGui.QColor(brightness, brightness, brightness))
        self.setPalette(p)
        v_layout = QtWidgets.QVBoxLayout(self)
        task_row = QtWidgets.QHBoxLayout()
        self.show_import = show_import
        self.path_object = path_object
        self.tool_button_layout = QtWidgets.QHBoxLayout()
        self.sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        self.setSizePolicy(self.sizePolicy)
        self.filter_string = filter_string
        self.label = title
        self.title = QtWidgets.QLabel("<b>%s</b>" % title.title())
        self.task = None
        self.user = None
        self.in_file_tree = None
        self.versions = AdvComboBox()
        self.versions.hide()

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
        self.data_table2 = FileTableWidget(self)
        self.data_table2.set_draggable(True)
        self.data_table2.title = 'blob'
        self.data_table2.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.my_files_label = QtWidgets.QLabel('My Files')
        self.export_label = QtWidgets.QLabel('Ready to Review/Publish')
        self.export_label_row = QtWidgets.QHBoxLayout()
        self.export_label_row.addWidget(self.export_label)
        self.export_label.hide()
        self.my_files_label.hide()

        # build the tool button row
        self.open_button = QtWidgets.QToolButton()
        self.open_button.setText('Open')
        self.import_button = QtWidgets.QToolButton()
        self.import_button.setText('Import')
        self.new_version_button = VersionButton(self)
        self.review_button = QtWidgets.QToolButton()
        self.review_button.setText('Review')
        self.publish_button = QtWidgets.QToolButton()
        self.publish_button.setText('Publish')
        self.tool_button_layout.addItem(QtWidgets.QSpacerItem(0, 0, QtWidgets.QSizePolicy.Expanding,
                                                              QtWidgets.QSizePolicy.Minimum))
        self.tool_button_layout.addWidget(self.open_button)
        self.tool_button_layout.addWidget(self.import_button)
        self.tool_button_layout.addWidget(self.new_version_button)
        self.tool_button_layout.addWidget(self.review_button)
        self.tool_button_layout.addWidget(self.publish_button)

        # this is where the filter needs to be!
        task_row.addWidget(self.my_files_label)
        task_row.addWidget(self.versions)
        task_row.addWidget(self.show_button)
        task_row.addWidget(self.hide_button)

        self.empty_state = EmptyStateWidget(path_object=self.path_object)
        self.empty_state.hide()

        v_layout.addWidget(self.title)
        v_layout.addLayout(task_row)
        v_layout.addWidget(self.start_task_button)
        v_layout.addLayout(self.users_layout)
        v_layout.addLayout(self.resolutions_layout)

        v_layout.addWidget(self.data_table, 1)
        v_layout.addLayout(self.export_label_row)
        v_layout.addWidget(self.data_table2, 1)
        v_layout.addWidget(self.empty_state)
        v_layout.addLayout(self.tool_button_layout)
        v_layout.addStretch(1)
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
        self.import_button.clicked.connect(self.on_import_clicked)
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
        self.import_button.hide()
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
        if self.show_import:
            self.import_button.show()
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

    def setup(self, table, mdl):
        if mdl:
            table.set_item_model(mdl)
            self.empty_state.hide()
            if not table.model().rowCount():
                table.hide()
                if not self.start_task_button.isVisible():
                    self.empty_state.show()

    def on_new_version_clicked(self):
        self.new_version_clicked.emit()

    def on_import_clicked(self):
        self.import_button_clicked.emit()

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
        self.start_task_clicked.emit(self.path_object)

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
        self.sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding,
                                                QtWidgets.QSizePolicy.MinimumExpanding)
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
        h_layout.addWidget(self.title)
        h_layout.addWidget(self.add_button)

        v_layout.addLayout(h_layout)
        v_layout.addWidget(self.search_box)
        v_layout.addWidget(self.data_table, 1)
        v_layout.setContentsMargins(0, 20, 0, 0)

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
        self.sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding,
                                                QtWidgets.QSizePolicy.MinimumExpanding)
        self.setSizePolicy(self.sizePolicy)
        self.filter_string = filter_string
        self.label = title
        self.task = None
        self.user = None
        min_width = 340

        self.message = QtWidgets.QLabel("")
        self.message.setMinimumWidth(min_width)
        try:
            self.message.setSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
        except AttributeError:
            print 'PySide2 Natively does not have QtGui.QSizePolicy'
        self.message.setAlignment(QtCore.Qt.AlignCenter)
        self.search_box = LJSearchEdit(self)
        self.add_button = QtWidgets.QToolButton()
        self.add_button.setText("+")
        self.data_table = LJTableWidget(self)
        self.data_table.title = title
        self.data_table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.data_table.setMinimumWidth(min_width)

        # build the filter optoins row
        self.assets_radio = QtWidgets.QRadioButton('Assets')
        self.shots_radio = QtWidgets.QRadioButton('Shots')
        self.radio_group_scope = QtWidgets.QButtonGroup(self)
        self.radio_group_scope.addButton(self.shots_radio)
        self.radio_group_scope.addButton(self.assets_radio)

        scope_layout.addWidget(self.shots_radio)
        scope_layout.addWidget(self.assets_radio)
        scope_layout.addStretch(1)
        scope_layout.addWidget(self.add_button)

        v_list.addItem(QtWidgets.QSpacerItem(0, 3, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Minimum))
        v_list.addWidget(self.search_box)
        v_list.addWidget(self.data_table, 1)
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
        # self.setMaximumHeight(self.height_hint)

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

    def sizeHint(self):
        return QtCore.QSize(300, 150)


class LJListWidget(QtWidgets.QWidget):
    def __init__(self, label):
        QtWidgets.QWidget.__init__(self)
        layout = QtWidgets.QVBoxLayout(self)
        self.label = QtWidgets.QLabel("<b>%s</b>" % label)
        self.add_button = QtWidgets.QToolButton()
        self.add_button.setText('+')
        self.h_layout = QtWidgets.QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        self.h_layout.addWidget(self.label)
        self.h_layout.addWidget(self.add_button)
        self.list = QtWidgets.QListWidget()
        self.list.setMaximumHeight(80)
        layout.addLayout(self.h_layout)
        layout.addWidget(self.list)

    def hide(self):
        self.label.hide()
        self.add_button.hide()
        self.list.hide()
        # self.combo.hide()

    def show(self):
        self.label.show()
        self.add_button.show()
        self.list.show()

