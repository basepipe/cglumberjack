import os
from Qt.QtCore import Qt
from Qt import QtWidgets, QtCore, QtGui
from cglcore import path
from cglui.widgets.search import LJSearchEdit
from cglui.widgets.containers.table import LJTableWidget
from cglui.widgets.containers.model import ListItemModel
from cglui.widgets.containers.menu import LJMenu
from cglcore.config import app_config
from palettes import set_color

MBW = 130
MBH = 28

GUI = app_config()['gui']


class LJButton(QtWidgets.QPushButton):

    def __init__(self, parent=None, mh=MBH, mw=MBW, color='white', border=1, border_color='grey', font=None):
        QtWidgets.QPushButton.__init__(self, parent)
        if font:
            self.setFont(font)
        else:
            font = QtGui.QFont(GUI['button']['font']['name'], GUI['button']['font']['size'])
            self.setFont(font)
        self.setMinimumHeight(mh)
        self.setMinimumWidth(mw)
        self.setStyleSheet("background-color: %s; border:%spx solid %s;" % (color, border, border_color))


class VersionButton(LJButton):

    def __init__(self, parent, font=None):
        LJButton.__init__(self, parent)
        if font:
            self.setFont(font)
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


class FilesWidget(QtWidgets.QFrame):

    def __init__(self, parent, show_import=False, font=None):
        QtWidgets.QFrame.__init__(self, parent)
        self.show_import = show_import
        brightness = 255
        #self.setAutoFillBackground(True)
        #p = self.palette()
        #p.setColor(self.backgroundRole(), QtGui.QColor(brightness, brightness, brightness))
        #self.setPalette(p)
        layout = QtWidgets.QVBoxLayout(self)
        table_layout = QtWidgets.QVBoxLayout()
        table_layout.setSpacing(0)
        tool_button_layout = QtWidgets.QHBoxLayout()

        table_font = QtGui.QFont('Monospaced', 8)
        layout.addLayout(table_layout)
        layout.addLayout(tool_button_layout)
        to_icon = os.path.join(path.icon_path(), 'arrow-right_12px.png')
        #self.to_button = QtWidgets.QPushButton()
        #self.to_button.hide()
        #self.to_button.setStyleSheet("background: transparent;")
        #self.to_button.setIcon(QtGui.QIcon(to_icon))

        # The Files Area
        self.work_files_table = FileTableWidget(self, hide_header=False)
        self.work_files_table.horizontalHeader().setDefaultAlignment(QtCore.Qt.AlignLeft)
        self.work_files_table.set_draggable(True)
        self.work_files_table.title = 'work_files'
        self.work_files_table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.export_files_table = FileTableWidget(self, hide_header=False)
        self.export_files_table.horizontalHeader().setDefaultAlignment(QtCore.Qt.AlignLeft)
        self.export_files_table.set_draggable(True)
        self.export_files_table.title = 'outputs'
        self.export_files_table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        to_icon = os.path.join(path.icon_path(), 'arrow-right_12px.png')

        self.open_button = LJButton(font=font)
        self.open_button.setText('Open')
        self.import_button = LJButton(font=font)
        self.import_button.setText('Import')
        self.new_version_button = VersionButton(self, font=font)
        self.review_button = LJButton(font=font)
        self.review_button.setText('Review')
        self.publish_button = LJButton(font=font)
        self.publish_button.setText('Publish')

        tool_button_layout.addStretch()
        tool_button_layout.addWidget(self.open_button)
        tool_button_layout.addWidget(self.import_button)
        tool_button_layout.addWidget(self.new_version_button)
        tool_button_layout.addWidget(self.review_button)
        tool_button_layout.addWidget(self.publish_button)

        # Create the Frame

        table_layout.setSpacing(0)
        table_layout.addWidget(self.work_files_table)
        # table_layout.addWidget(self.to_button)
        table_layout.addWidget(self.export_files_table)
        table_layout.addLayout(tool_button_layout)

        self.open_button.clicked.connect(self.on_open_button_clicked)
        self.new_version_button.clicked.connect(self.on_new_version_clicked)
        self.import_button.clicked.connect(self.on_import_clicked)

    def hide_files(self):
        self.to_button.hide()
        self.work_files_table.hide()
        self.export_files_table.hide()

    def show_files(self):
        self.to_button.show()
        self.work_files_table.show()
        self.export_files_table.show()

    def hide_tool_buttons(self):
        self.open_button.hide()
        self.import_button.hide()
        self.new_version_button.hide()
        self.publish_button.hide()
        self.review_button.hide()

    def show_tool_buttons(self):
        self.open_button.show()
        if self.show_import:
            self.import_button.show()
        self.new_version_button.show()
        self.publish_button.show()
        self.review_button.show()

    def on_new_version_clicked(self):
        self.new_version_clicked.emit()

    def on_import_clicked(self):
        self.import_button_clicked.emit()

    def on_open_button_clicked(self):
        self.open_button_clicked.emit()


class QHLine(QtWidgets.QFrame):
    def __init__(self):
        super(QHLine, self).__init__()
        self.setFrameShape(QtWidgets.QFrame.HLine)
        self.setFrameShadow(QtWidgets.QFrame.Sunken)


class QVLine(QtWidgets.QFrame):
    def __init__(self):
        super(QVLine, self).__init__()
        self.setFrameShape(QtWidgets.QFrame.VLine)
        self.setFrameShadow(QtWidgets.QFrame.Sunken)


class TaskWidget(QtWidgets.QWidget):
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
        QtWidgets.QWidget.__init__(self, parent)
        #self.setFrameStyle(QtWidgets.QFrame.StyledPanel | QtWidgets.QFrame.Sunken)
        font_db = QtWidgets.QFontDatabase()
        font_db.addApplicationFont(os.path.join(path.font_path(), 'ARCADECLASSIC.TTF'))
        font_db.addApplicationFont(os.path.join(path.font_path(), 'ka1.ttf'))

        font = QtGui.QFont('Courier New', 10)
        # font = QtGui.QFont(GUI['button']['font']['name'], int(GUI['button']['font']['size']))
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
        self.title.setFont(QtGui.QFont(GUI['title']['font']['name'], GUI['title']['font']['size']))
        set_color(self.title, GUI['title']['font']['color'])

        # self.title.setForeground(QtGui.QColor(GUI['title']['font']['color']))
        self.task = None
        self.user = None
        self.in_file_tree = None
        self.versions = AdvComboBox()
        self.versions.setFont(font)
        set_color(self.versions, GUI['title']['font']['color'])
        self.versions.hide()

        self.users_label = QtWidgets.QLabel("User:")
        self.users_label.setFont(font)
        set_color(self.versions, GUI['title']['font']['color'])
        self.users = AdvComboBox()
        self.users.setMaximumWidth(MBW)
        self.users.setFont(font)
        set_color(self.versions, GUI['title']['font']['color'])
        self.users_layout = QtWidgets.QHBoxLayout()
        self.users_layout.addItem(QtWidgets.QSpacerItem(0, 0, QtWidgets.QSizePolicy.Expanding,
                                                        QtWidgets.QSizePolicy.Minimum))
        self.users_layout.addWidget(self.users_label)

        self.users_layout.addWidget(self.users)

        self.resolutions = AdvComboBox()
        self.resolutions.setMaximumWidth(MBW)
        self.resolutions.setFont(font)
        set_color(self.resolutions, GUI['button']['font']['color'])
        self.resolutions_layout = QtWidgets.QHBoxLayout()
        self.resolutions_layout.addItem(QtWidgets.QSpacerItem(0, 0, QtWidgets.QSizePolicy.Expanding,
                                                              QtWidgets.QSizePolicy.Minimum))
        self.resolutions_label = QtWidgets.QLabel("Resolution:")
        self.resolutions_label.setFont(font)
        set_color(self.resolutions_label, GUI['button']['font']['color'])
        self.resolutions_layout.addWidget(self.resolutions_label)
        self.resolutions_layout.addWidget(self.resolutions)
        self.resolutions_layout.setContentsMargins(0, 0, 0, 0)

        self.show_button = LJButton()
        self.show_button.setText("more")
        self.start_task_button = LJButton()
        self.start_task_button.setText("Start Task")
        self.start_task_button.setMinimumWidth(150)
        self.start_task_button.setMinimumHeight(MBH)
        self.export_label = QtWidgets.QLabel('   Ready to Review/Publish')
        self.export_label.setFont(font)
        set_color(self.export_label, GUI['button']['font']['color'])
        self.export_label_row = QtWidgets.QHBoxLayout()
        self.export_label_row.addWidget(self.export_label)
        self.export_label.hide()
        self.hide_button = LJButton()
        self.hide_button.setText("less")

        self.title_row = QtWidgets.QHBoxLayout()
        self.title_row.addWidget(self.title)
        self.title_row.addStretch(1)
        self.title_row.addWidget(self.versions)
        self.title_row.addWidget(self.show_button)
        self.title_row.addWidget(self.hide_button)
        self.title_row.addWidget(self.start_task_button)

        self.empty_state = EmptyStateWidget(path_object=self.path_object)
        self.empty_state.hide()
        self.files_area = FilesWidget(self)

        v_layout.addLayout(self.title_row)
        v_layout.addLayout(task_row)
        v_layout.addLayout(self.users_layout)
        v_layout.addLayout(self.resolutions_layout)
        v_layout.addWidget(self.files_area)
        v_layout.addWidget(self.empty_state)
        v_layout.addLayout(self.tool_button_layout)
        v_layout.addStretch(1)
        self.setLayout(v_layout)
        self.hide_combos()

        self.start_task_button.hide()
        self.hideall()
        self.show_button.clicked.connect(self.on_show_button_clicked)
        self.hide_button.clicked.connect(self.on_hide_button_clicked)
        self.start_task_button.clicked.connect(self.on_start_task_clicked)
        self.files_area.hide_tool_buttons()

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

    def showall(self):
        self.hide_button.show()
        self.show_button.hide()

    def setup(self, table, mdl):
        if mdl:
            table.set_item_model(mdl)
            self.empty_state.hide()
            if not table.model().rowCount():
                table.hide()
                if not self.start_task_button.isVisible():
                    self.empty_state.show()

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
        self.title = QtWidgets.QLabel("%s" % title)
        self.title.setFont(QtGui.QFont(GUI['super']['font']['name'], GUI['super']['font']['size']))
        set_color(self.title, GUI['super']['font']['color'])
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
        h_layout.addStretch(1)

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
        scope_layout.addWidget(self.add_button)
        scope_layout.addStretch(1)


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

    def __init__(self, parent, hide_header=True, header_color=GUI['table_header']['background_color'], table_color=False):
        LJTableWidget.__init__(self, parent)
        # Deal with Stylesheets
        header_stylesheet = "QHeaderView::section{Background-color:rgb(%s, %s, %s); " \
                     "height: 30px; " \
                     "padding-left: 5px;" \
                     "padding-top: 2px; " \
                     "border-radius:16 px;}" % (header_color[0], header_color[1], header_color[2])
        #stylesheet = "QTableView::item{padding: 10px;}"
        self.horizontalHeader().setFixedHeight(24)
        # Set fonts from Globals
        table_font = QtGui.QFont(GUI['table']['font']['name'], GUI['table']['font']['size'])
        header_font = QtGui.QFont(GUI['table_header']['font']['name'], GUI['table_header']['font']['size'])
        self.setFont(table_font)
        set_color(self, GUI['table']['font']['color'])
        self.horizontalHeader().setFont(header_font)
        self.horizontalHeader().setStyleSheet(header_stylesheet)
        #self.setStyleSheet(stylesheet)

        self.sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.MinimumExpanding)
        self.setSortingEnabled(False)
        if table_color:
            print 'table color defined'
        # Set The Right Click Menu
        if hide_header:
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
        return QtCore.QSize(350, 150)


class LJListWidget(QtWidgets.QWidget):
    def __init__(self, label):
        QtWidgets.QWidget.__init__(self)
        self.setSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.Minimum)
        layout = QtWidgets.QVBoxLayout(self)
        self.label = QtWidgets.QLabel("<b>%s</b>" % label)
        self.label.setFont(QtGui.QFont(GUI['super']['font']['name'], GUI['super']['font']['size']))
        set_color(self.label, GUI['super']['font']['color'])
        self.add_button = QtWidgets.QToolButton()
        self.add_button.setText('+')
        self.h_layout = QtWidgets.QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        self.h_layout.addWidget(self.label)
        self.h_layout.addWidget(self.add_button)
        self.h_layout.addStretch(1)
        self.list = QtWidgets.QListWidget()
        #self.list.setMaximumHeight(80)
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


class CreateProjectDialog(QtWidgets.QDialog):

    def __init__(self, parent, variable):
        QtWidgets.QDialog.__init__(self, parent=parent)
        self.variable = variable
        proj_management_label = QtWidgets.QLabel('Project Management')
        layout = QtWidgets.QVBoxLayout(self)
        self.proj_management_combo = QtWidgets.QComboBox()
        self.proj_management_combo.addItems(['lumbermill', 'ftrack', 'shotgun', 'google_docs'])
        self.red_palette = QtGui.QPalette()
        self.red_palette.setColor(self.foregroundRole(), QtGui.QColor(255, 0, 0))
        self.green_palette = QtGui.QPalette()
        self.green_palette.setColor(self.foregroundRole(), QtGui.QColor(0, 255, 0))
        self.black_palette = QtGui.QPalette()
        self.black_palette.setColor(self.foregroundRole(), QtGui.QColor(0, 0, 0))
        self.cancel_button = QtWidgets.QPushButton('Cancel')
        self.ok_button = QtWidgets.QPushButton('Ok')
        self.button = ''

        button_layout = QtWidgets.QHBoxLayout()
        button_layout.addStretch(1)
        button_layout.addWidget(self.cancel_button)
        button_layout.addWidget(self.ok_button)

        proj_label = QtWidgets.QLabel('%s Name' % self.variable.title())
        self.proj_line_edit = QtWidgets.QLineEdit('')
        self.message = QtWidgets.QLabel()

        self.grid_layout = QtWidgets.QGridLayout()
        self.grid_layout.addWidget(proj_label, 0, 0)
        self.grid_layout.addWidget(self.proj_line_edit, 0, 1)
        self.grid_layout.addWidget(proj_management_label, 2, 0)
        self.grid_layout.addWidget(self.proj_management_combo, 2, 1)

        layout.addLayout(self.grid_layout)
        layout.addWidget(self.message)
        layout.addLayout(button_layout)

        self.proj_line_edit.textChanged.connect(self.on_project_text_changed)
        self.ok_button.clicked.connect(self.on_ok_clicked)
        self.cancel_button.clicked.connect(self.on_cancel_clicked)

    def on_project_text_changed(self):
        input_text = self.proj_line_edit.text()
        message = path.test_string_against_path_rules(self.variable, input_text)
        if input_text:
            if message:
                self.message.setText(message)
                self.message.setPalette(self.red_palette)
            else:
                self.message.setText('Creating %s: %s' % (self.variable, input_text))
        else:
            self.message.setText('')

    def on_ok_clicked(self):
        self.button = 'Ok'
        self.accept()

    def on_cancel_clicked(self):
        self.accept()


class LabelComboRow(QtWidgets.QVBoxLayout):
    def __init__(self, label, button=True, bold=True):
        QtWidgets.QVBoxLayout.__init__(self)
        if bold:
            self.label = QtWidgets.QLabel("<b>%s</b>" % label)
        else:
            self.label = QtWidgets.QLabel("%s" % label)
        self.combo = AdvComboBox()
        self.h_layout = QtWidgets.QHBoxLayout()
        self.h_layout.addWidget(self.label)
        self.h_layout.addWidget(self.combo)
        if button:
            self.button = button
            self.add_button = LJButton
            self.add_button.setText('+')
            self.h_layout.addWidget(self.add_button)
            self.addLayout(self.h_layout)
            #self.addWidget(self.combo)
        else:
            self.h_layout.addWidget(self.combo)
            self.addLayout(self.h_layout)

    def hide(self):
        self.label.hide()
        self.combo.hide()
        if self.button:
            self.add_button.hide()

    def show(self):
        self.label.show()
        self.combo.show()
        if self.button:
            self.add_button.show()


class AdvComboBoxLabeled(QtWidgets.QVBoxLayout):
    def __init__(self, label):
        QtWidgets.QVBoxLayout.__init__(self)
        self.label = QtWidgets.QLabel("<b>%s</b>" % label)


class AdvComboBox(QtWidgets.QComboBox):
    def __init__(self, parent=None):
        super(AdvComboBox, self).__init__(parent)

        self.userselected = False
        self.setFocusPolicy(QtCore.Qt.StrongFocus)
        self.setEditable(True)
        self.setMinimumWidth(90)
        self.SizeAdjustPolicy(QtWidgets.QComboBox.AdjustToContents)
        # self.setSizePolicy(QtGui.QSizePolicy.MinimumExpanding, QtGui.QSizePolicy.Minimum)
        self.setSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.Minimum)
        # add a filter model to filter matching items
        self.pFilterModel = QtCore.QSortFilterProxyModel(self)
        self.pFilterModel.setFilterCaseSensitivity(QtCore.Qt.CaseInsensitive)
        self.pFilterModel.setSourceModel(self.model())

        # add a completer
        self.completer = QtWidgets.QCompleter(self)
        # Set the model that the QCompleter uses
        # - in PySide doing this as a separate step worked better
        self.completer.setModel(self.pFilterModel)
        # always show all (filtered) completions
        self.completer.setCompletionMode(QtWidgets.QCompleter.UnfilteredPopupCompletion)

        self.setCompleter(self.completer)

        # connect signals

        def filter_(text):
            self.pFilterModel.setFilterFixedString(str(text))

        self.lineEdit().textEdited[unicode].connect(filter_)
        self.completer.activated.connect(self.on_completer_activated)

    # on selection of an item from the completer, select the corresponding item from combobox
    def on_completer_activated(self, text):
        if text:
            index = self.findText(str(text))
            self.setCurrentIndex(index)

    # on model change, update the models of the filter and completer as well
    def setModel(self, model):
        super(AdvComboBox, self).setModel(model)
        self.pFilterModel.setSourceModel(model)
        self.completer.setModel(self.pFilterModel)

    # on model column change, update the model column of the filter and completer as well
    def setModelColumn(self, column):
        self.completer.setCompletionColumn(column)
        self.pFilterModel.setFilterKeyColumn(column)
        super(AdvComboBox, self).setModelColumn(column)

    def populate_from_project(self, keys):
        self.clear()
        # load the shading/texture assets from the library
        # clear duplicates
        objlist = []
        for key in keys:
            if str(key) not in objlist:
                objlist.append(str(key))
        for item in objlist:
            self.addItem(item)


class LabelComboRow(QtWidgets.QVBoxLayout):
    def __init__(self, label, button=True, bold=True):
        QtWidgets.QVBoxLayout.__init__(self)
        if bold:
            self.label = QtWidgets.QLabel("<b>%s</b>" % label)
        else:
            self.label = QtWidgets.QLabel("%s" % label)
        self.combo = AdvComboBox()
        self.h_layout = QtWidgets.QHBoxLayout()
        self.h_layout.addWidget(self.label)
        self.h_layout.addWidget(self.combo)
        if button:
            self.button = button
            self.add_button = LJButton()
            self.add_button.setText('+')
            self.h_layout.addWidget(self.add_button)
            self.addLayout(self.h_layout)
            #self.addWidget(self.combo)
        else:
            self.h_layout.addWidget(self.combo)
            self.addLayout(self.h_layout)

    def hide(self):
        self.label.hide()
        self.combo.hide()
        if self.button:
            self.add_button.hide()

    def show(self):
        self.label.show()
        self.combo.show()
        if self.button:
            self.add_button.show()


class AdvComboBoxLabeled(QtWidgets.QVBoxLayout):
    def __init__(self, label):
        QtWidgets.QVBoxLayout.__init__(self)
        self.label = QtWidgets.QLabel("<b>%s</b>" % label)


class AdvComboBox(QtWidgets.QComboBox):
    def __init__(self, parent=None):
        super(AdvComboBox, self).__init__(parent)

        self.userselected = False
        self.setFocusPolicy(QtCore.Qt.StrongFocus)
        self.setEditable(True)
        self.setMinimumWidth(90)
        self.SizeAdjustPolicy(QtWidgets.QComboBox.AdjustToContents)
        # self.setSizePolicy(QtGui.QSizePolicy.MinimumExpanding, QtGui.QSizePolicy.Minimum)
        self.setSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.Minimum)
        # add a filter model to filter matching items
        self.pFilterModel = QtCore.QSortFilterProxyModel(self)
        self.pFilterModel.setFilterCaseSensitivity(QtCore.Qt.CaseInsensitive)
        self.pFilterModel.setSourceModel(self.model())

        # add a completer
        self.completer = QtWidgets.QCompleter(self)
        # Set the model that the QCompleter uses
        # - in PySide doing this as a separate step worked better
        self.completer.setModel(self.pFilterModel)
        # always show all (filtered) completions
        self.completer.setCompletionMode(QtWidgets.QCompleter.UnfilteredPopupCompletion)

        self.setCompleter(self.completer)

        # connect signals

        def filter_(text):
            self.pFilterModel.setFilterFixedString(str(text))

        self.lineEdit().textEdited[unicode].connect(filter_)
        self.completer.activated.connect(self.on_completer_activated)

    # on selection of an item from the completer, select the corresponding item from combobox
    def on_completer_activated(self, text):
        if text:
            index = self.findText(str(text))
            self.setCurrentIndex(index)

    # on model change, update the models of the filter and completer as well
    def setModel(self, model):
        super(AdvComboBox, self).setModel(model)
        self.pFilterModel.setSourceModel(model)
        self.completer.setModel(self.pFilterModel)

    # on model column change, update the model column of the filter and completer as well
    def setModelColumn(self, column):
        self.completer.setCompletionColumn(column)
        self.pFilterModel.setFilterKeyColumn(column)
        super(AdvComboBox, self).setModelColumn(column)

    def populate_from_project(self, keys):
        self.clear()
        # load the shading/texture assets from the library
        # clear duplicates
        objlist = []
        for key in keys:
            if str(key) not in objlist:
                objlist.append(str(key))
        for item in objlist:
            self.addItem(item)