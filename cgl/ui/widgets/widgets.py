import os
from cgl.plugins.Qt import QtGui, QtCore, QtWidgets
from cgl.core.utils import read_write
from cgl.core import path
from cgl.ui.util import drop_handler, define_palettes
from cgl.ui.widgets.containers.table import LJTableWidget
from cgl.ui.widgets.containers.model import ListItemModel, FilesModel
from cgl.ui.widgets.containers.menu import LJMenu
from cgl.core.project import get_task_info
from cgl.core.config.config import ProjectConfig


class LJButton(QtWidgets.QPushButton):

    def __init__(self, parent=None):
        QtWidgets.QPushButton.__init__(self, parent)
        self.setProperty('class', 'basic')


class LJTag(QtWidgets.QFrame):
    close_clicked = QtCore.Signal()

    def __init__(self, parent=None, text='Tab Text', height=30):
        QtWidgets.QFrame.__init__(self, parent)
        self.setProperty('class', 'tag_red')
        self.setMaximumHeight(height)
        self.text = text
        close_width = height/2
        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        label = QtWidgets.QLabel(text)
        label.setProperty('class', 'tag_text')
        close_button = QtWidgets.QToolButton()
        close_button.setText('x')
        close_button.setProperty('class', 'tag')
        close_button.setMaximumWidth(close_width)
        close_button.setMaximumHeight(close_width)
        layout.addWidget(label)
        layout.addWidget(close_button)
        # Shape of the button is a "Frame" with an hlayout
        # close button is a "tool button" with an 'x'
        close_button.clicked.connect(self.delete_tag)

    def delete_tag(self):
        print(self.text)
        print('delete')
        self.close_clicked.emit()


class TagWidget(QtWidgets.QWidget):

    def __init__(self, parent=None):
        QtWidgets.QWidget.__init__(self, parent)
        # TODO - add the tag icon to this
        # TODO - add the hide/show functionality to pushing the tag icon
        # TODO - add the abililty to choose the color of the tag
        # TODO - add the ability to have a list of commonly used tags.
        layout = QtWidgets.QVBoxLayout(self)
        self.frame = TagFrame()
        layout.addWidget(self.frame)


class TagFrame(QtWidgets.QFrame):

    def __init__(self, parent=None, tag_height=30):
        QtWidgets.QFrame.__init__(self, parent)
        self.tag_height = tag_height
        self.setProperty('class', 'tag_widget')
        self.setMinimumHeight(tag_height+4)
        self.layout = QtWidgets.QHBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.tags_layout = QtWidgets.QHBoxLayout()
        self.tags_layout.setContentsMargins(0, 0, 0, 0)
        self.text_entry = QtWidgets.QLineEdit()
        self.text_entry.setProperty('class', 'tag_entry')
        self.tag_dict = {}
        self.tags = []

        self.layout.addLayout(self.tags_layout)
        self.layout.addWidget(self.text_entry)
        self.text_entry.textEdited.connect(self.on_text_entry_changed)

    def on_text_entry_changed(self):
        text = self.sender().text()
        if ',' in text:
            text = text.replace(',', '')
            self.add_tag(tag_text=text)
            self.sender().setText('')

    def add_tag(self, tag_text):
        tag = LJTag(text=tag_text, height=self.tag_height)
        tag.close_clicked.connect(self.remove_tag)
        self.tag_dict['tag_text'] = tag
        self.tags.append(tag_text)
        self.tags_layout.addWidget(tag)

    def remove_tag(self):
        self.sender().deleteLater()
        self.layout.removeWidget(self.sender())


class VersionButton(LJButton):

    def __init__(self, parent):
        LJButton.__init__(self, parent)
        self.menu = QtWidgets.QMenu()
        self.setText(self.tr("Version Up"))
        self.empty_act = self.menu.addAction(self.tr("New Empty Version"))
        self.empty_act.setToolTip(self.tr("Create a new empty version"))
        self.empty_act.triggered.connect(lambda: self.parent().create_empty_version.emit())
        self.selected_act = self.menu.addAction(self.tr("New Version From Selected"))
        self.selected_act.triggered.connect(lambda: self.parent().copy_selected_version.emit())
        self.selected_act.setToolTip(self.tr("Create a new version copying from current version"))
        # self.latest_act = self.menu.addAction(self.tr("Copy Latest Version"))
        # self.latest_act.triggered.connect(lambda: self.parent().copy_latest_version.emit())
        # self.latest_act.setToolTip(self.tr("Create a new version copying from the latest version"))
        self.setMenu(self.menu)

    def set_new_version(self):
        self.selected_act.setVisible(False)
        self.latest_act.setVisible(False)
        self.setEnabled(True)

    def set_version_selected(self):
        self.selected_act.setVisible(True)
        self.latest_act.setVisible(True)
        self.setEnabled(True)


class EmptyStateWidget(QtWidgets.QPushButton):
    files_added = QtCore.Signal(object)

    def __init__(self, parent=None, path_object=None, text='Drag/Drop to Add Files', files=False):
        QtWidgets.QPushButton.__init__(self, parent)
        self.files = files
        self.path_object = path_object
        self.setAcceptDrops(True)
        self.setMinimumWidth(300)
        self.setMinimumHeight(100)
        self.setText(text)
        self.setProperty('class', 'empty_state')
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
        if not self.files:
            new_obj = self.path_object.copy(task=self.parent().task, version=self.parent().versions.currentText(),
                                            user=self.parent().users.currentText(),
                                            resolution=self.parent().resolutions.currentText(), filename=None,
                                            ext=None, filename_base=None)
            self.to_path = new_obj.path_root
            self.to_object = new_obj
            drop_handler(self.files_added, e)
        else:
            drop_handler(self.files_added, e)


class FileTableModel(ListItemModel):

    def data(self, index, role):
        row = index.row()
        col = index.column()
        if role == QtCore.Qt.DisplayRole:
            return self.data_[row][col]
        if role == QtCore.Qt.DecorationRole:
            data = self.data_[row][col]
            if "." not in data:
                return QtGui.QIcon(self.cfg.icon_path('folder2.png'))
        # if role == QtCore.Qt.ToolTipRole:
        #     return "hello tom"


class FilesWidget(QtWidgets.QFrame):
    open_button_clicked = QtCore.Signal()
    import_button_clicked = QtCore.Signal()
    reference_button_clicked = QtCore.Signal()
    new_version_clicked = QtCore.Signal()
    review_button_clicked = QtCore.Signal()
    publish_button_clicked = QtCore.Signal()
    create_empty_version = QtCore.Signal()
    copy_latest_version = QtCore.Signal()
    copy_selected_version = QtCore.Signal()
    create_edit_clicked = QtCore.Signal()

    def __init__(self, parent, show_import=False, show_reference=False, cfg=None):
        QtWidgets.QFrame.__init__(self, parent)
        self.cfg = cfg
        self.show_import = show_import
        self.show_reference = show_reference
        layout = QtWidgets.QVBoxLayout(self)
        table_layout = QtWidgets.QVBoxLayout()
        table_layout.setSpacing(0)
        tool_button_layout = QtWidgets.QHBoxLayout()

        layout.addLayout(table_layout)
        layout.addLayout(tool_button_layout)

        # The Files Area
        self.work_files_table = FileTableWidget(self, hide_header=False, cfg=self.cfg)
        self.work_files_table.horizontalHeader().setDefaultAlignment(QtCore.Qt.AlignLeft)
        # self.work_files_table.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.ResizeToContents)
        self.work_files_table.set_draggable(True)
        self.work_files_table.title = 'work_files'
        self.work_files_table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.export_files_table = FileTableWidget(self, hide_header=False, cfg=self.cfg)
        self.export_files_table.horizontalHeader().setProperty('class', 'output')
        self.export_files_table.horizontalHeader().setDefaultAlignment(QtCore.Qt.AlignLeft)
        self.export_files_table.set_draggable(True)
        self.export_files_table.title = 'outputs'
        self.export_files_table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.open_button = LJButton()
        self.open_button.setText('Open')
        self.import_button = LJButton()
        self.import_button.setText('Import')
        self.reference_button = LJButton()
        self.reference_button.setText('Reference')
        self.reference_button.hide()
        self.new_version_button = VersionButton(self)
        self.review_button = LJButton()
        self.review_button.setText('Review')
        self.publish_button = LJButton()
        self.publish_button.setText('Publish')
        self.create_edit_button = LJButton('Create Edit')
        self.create_edit_button.setText('Create Edit')
        self.create_edit_button.hide()

        tool_button_layout.addStretch()
        tool_button_layout.addWidget(self.open_button)
        tool_button_layout.addWidget(self.create_edit_button)
        tool_button_layout.addWidget(self.import_button)
        tool_button_layout.addWidget(self.reference_button)
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
        self.review_button.clicked.connect(self.on_review_button_clicked)
        self.publish_button.clicked.connect(self.on_publish_button_clicked)
        self.import_button.clicked.connect(self.on_import_clicked)
        self.reference_button.clicked.connect(self.on_reference_clicked)
        self.create_edit_button.clicked.connect(self.on_create_edit_button_clicked)
        if self.show_import:
            self.import_button.show()
        if self.show_reference:
            self.reference_button.show()

    def clear(self):
        self.export_files_table.clear()

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

    def show_tool_buttons(self, user):
        self.open_button.show()
        if self.parent().path_object.task == 'video':
            self.create_edit_button.show()
        if self.show_import:
            self.import_button.show()
        if user != 'publish':
            self.new_version_button.show()
            # self.publish_button.show()
        self.review_button.show()

    def on_new_version_clicked(self):
        self.new_version_clicked.emit()

    def on_review_button_clicked(self):
        self.review_button_clicked.emit()

    def on_publish_button_clicked(self):
        self.publish_button_clicked.emit()

    def on_import_clicked(self):
        self.import_button_clicked.emit()

    def on_reference_clicked(self):
        self.reference_button_clicked.emit()

    def on_open_button_clicked(self):
        self.open_button_clicked.emit()

    def on_create_edit_button_clicked(self):
        self.create_edit_clicked.emit()


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
    publish_button_clicked = QtCore.Signal()
    review_button_clicked = QtCore.Signal()
    create_empty_version = QtCore.Signal()
    copy_latest_version = QtCore.Signal()
    copy_selected_version = QtCore.Signal()

    def __init__(self, parent, title, filter_string=None, path_object=None, show_import=False, show_reference=False,
                 cfg=None):
        QtWidgets.QWidget.__init__(self, parent)
        v_layout = QtWidgets.QVBoxLayout(self)
        task_row = QtWidgets.QHBoxLayout()
        if not cfg:
            self.cfg = ProjectConfig(path_object)
        else:
            self.cfg = cfg
        self.show_import = show_import
        self.show_reference = show_reference
        self.path_object = path_object
        self.tool_button_layout = QtWidgets.QHBoxLayout()
        self.sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        self.setSizePolicy(self.sizePolicy)
        self.filter_string = filter_string
        self.label = title
        self.title = QtWidgets.QLabel("<b>%s</b>" % title.title())
        self.title.setProperty('class', 'title_text')
        self.status_button = QtWidgets.QPushButton('Get Status')
        self.status_button.setProperty('class', 'status_button')

        self.task = None
        self.user = None
        self.in_file_tree = None
        self.versions_label = QtWidgets.QLabel("Version:")
        self.versions = AdvComboBox()
        self.versions.name = 'versions'

        self.users_label = QtWidgets.QLabel("User:")
        self.users = AdvComboBox()
        self.users.name = 'users'
        self.resolutions_label = QtWidgets.QLabel("Resolution:")
        self.resolutions = AdvComboBox()
        self.resolutions.name = 'resolutions'
        self.start_task_button = LJButton()
        self.start_task_button.setText("Start Task")

        self.info_layout = QtWidgets.QHBoxLayout()
        self.info_layout.addWidget(self.users_label)
        self.info_layout.addWidget(self.users)
        self.info_layout.addWidget(self.versions_label)
        self.info_layout.addWidget(self.versions)
        self.info_layout.addWidget(self.resolutions_label)
        self.info_layout.addWidget(self.resolutions)
        self.info_layout.addWidget(self.start_task_button)
        # self.info_layout.setContentsMargins(0, 0, 0, 0)

        self.export_label = QtWidgets.QLabel('   Ready to Review/Publish')
        self.export_label.setProperty('class', 'basic')
        self.export_label_row = QtWidgets.QHBoxLayout()
        self.export_label_row.addWidget(self.export_label)
        self.export_label.hide()

        self.title_row = QtWidgets.QHBoxLayout()
        self.create_assignment = QtWidgets.QPushButton("Create Assignment")
        self.create_assignment.setProperty('class', 'add_button')
        self.title_row.addWidget(self.title)
        self.title_row.addWidget(self.status_button)
        self.title_row.addStretch(1)
        self.title_row.addWidget(self.create_assignment)

        self.empty_state = EmptyStateWidget(path_object=self.path_object)
        self.empty_state.hide()
        self.files_area = FilesWidget(self, show_import=self.show_import, show_reference=self.show_reference,
                                      cfg=self.cfg)

        v_layout.addLayout(self.title_row)
        v_layout.addLayout(self.info_layout)
        v_layout.addLayout(task_row)
        v_layout.addWidget(self.files_area)
        v_layout.addWidget(self.empty_state)
        v_layout.addLayout(self.tool_button_layout)
        v_layout.addStretch(1)
        self.setLayout(v_layout)
        # self.hide_combos()

        self.start_task_button.hide()
        # self.show_button.clicked.connect(self.on_show_button_clicked)
        # self.hide_button.clicked.connect(self.on_hide_button_clicked)
        self.status_button.clicked.connect(self.force_refresh_task_info)
        self.create_assignment.clicked.connect(self.on_start_task_clicked)
        self.files_area.copy_latest_version.connect(self.copy_latest)
        self.files_area.copy_selected_version.connect(self.copy_selected)
        self.files_area.create_empty_version.connect(self.create_empty)
        self.files_area.hide_tool_buttons()
        # self.refresh_task_info()

    def refresh_task_info(self, force=False):
        color_dict = {"pending review": "#EFB940",
                      "not started": "#E54A25",
                      "in progress": "#61BBF6",
                      "needs attention": "#EFB940",
                      "approved": "#4BA42F",
                      "client approved": "#4BA42F",
                      "on hold": "#927DF0",
                      "ommitted": "#808080",
                      "completed": "#4BA42F"}
        task_info = get_task_info(self.path_object, force=force)
        if task_info:
            status = task_info['status']
            self.status_button.setText(status)
            status_color = color_dict[status.lower()]
            self.status_button.setStyleSheet("QPushButton.status_button { background-color: %s }" % status_color)

    def force_refresh_task_info(self):
        self.refresh_task_info(force=False)

    def create_empty(self):
        self.create_empty_version.emit()

    def copy_selected(self):
        self.copy_selected_version.emit()

    def copy_latest(self):
        self.copy_latest_version.emit()

    def hide(self):
        self.hide_button.hide()
        self.add_button.hide()
        self.data_table.hide()
        self.search_box.hide()
        self.show_button.hide()
        self.hide_button.hide()
        self.title.hide()
        # self.users.hide()
        # self.users_label.hide()
        # self.resolutions.hide()
        # self.resolutions_label.hide()
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

    def setup(self, table, mdl):
        """
        Sets up the File Tables in the Task Widget
        :param table:
        :param mdl:
        :return:
        """

        if isinstance(mdl, FileTableModel):
            table.set_item_model(mdl)
            self.empty_state.hide()
            if not table.model().rowCount():
                table.hide()
                if not self.start_task_button.isVisible():
                    self.empty_state.show()
        elif isinstance(mdl, ListItemModel):
            table.set_item_model(mdl)
            self.empty_state.hide()
            if not table.model().rowCount():
                table.hide()
                if not self.start_task_button.isVisible():
                    self.empty_state.show()
        elif isinstance(mdl, FilesModel):
            table.set_item_model(mdl)
            self.empty_state.hide()
            if not table.model().rowCount():
                table.hide()
                if not self.start_task_button.isVisible():
                    self.empty_state.show()
        else:
            print('Found unexpected model: %s' % mdl)

    def on_add_button_clicked(self):
        self.add_clicked.emit()

    def on_start_task_clicked(self):
        self.start_task_clicked.emit(self.path_object)

    def set_title(self, new_title):
        self.title.setText('<b>%s</b>' % new_title.title())


class ProjectWidget(QtWidgets.QWidget):
    """
    Displays Projects within a company
    """
    button_clicked = QtCore.Signal(object)
    filter_changed = QtCore.Signal()
    add_clicked = QtCore.Signal()
    assign_clicked = QtCore.Signal(object)

    def __init__(self, parent=None, title='', filter_string=None, path_object=None, pixmap=None, search_box=None,
                 cfg=None):
        QtWidgets.QWidget.__init__(self, parent)
        v_layout = QtWidgets.QVBoxLayout(self)
        h_layout = QtWidgets.QHBoxLayout()
        self.path_object = path_object
        if not cfg:
            self.cfg = ProjectConfig(path_object)
        else:
            self.cfg = cfg
        self.tool_button_layout = QtWidgets.QHBoxLayout()
        self.sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding,
                                                QtWidgets.QSizePolicy.MinimumExpanding)
        self.setSizePolicy(self.sizePolicy)
        self.filter_string = filter_string
        self.label = title
        self.title = QtWidgets.QLabel("%s" % title)
        self.title.setProperty('class', 'ultra_title')
        self.task = None
        self.user = None
        self.search_box = search_box

        self.message = QtWidgets.QLabel("")
        self.message.setProperty('class', 'basic')
        self.add_button = QtWidgets.QToolButton()
        self.add_button.setText("add project")
        self.add_button.setProperty('class', 'add_button')
        self.data_table = LJTableWidget(self, path_object=self.path_object)
        self.data_table.title = title
        self.data_table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.installEventFilter(self)
        config = ProjectConfig(self.path_object)
        self.project_management = config.project_config['account_info']['project_management']


        # can i create a right click menu in this stage?

        if pixmap:
            self.icon = QtWidgets.QLabel()
            self.icon.setPixmap(pixmap)
            h_layout.addWidget(self.icon)
        h_layout.addWidget(self.title)
        h_layout.addStretch(1)
        h_layout.addWidget(self.add_button)

        v_layout.addLayout(h_layout)
        if not search_box:

            v_layout.addWidget(self.search_box)
        v_layout.addWidget(self.data_table, 1)
        v_layout.setContentsMargins(0, 0, 0, 0)

        self.add_button.clicked.connect(self.on_add_button_clicked)

    def eventFilter(self, widget, event):
        if isinstance(event, QtGui.QContextMenuEvent):
            # self.leftClicked(event.pos())
            self.menu = LJMenu(self.data_table)
            #self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
            self.menu.create_action("Mark as Favorite", self.mark_as_favorite)
            self.menu.create_action('Show in %s' % self.project_management, self.show_in_proj)
            self.menu.create_action('Share Project', self.share_project)
            self.menu.create_action('Calculate Project Size', self.calculate_project_size)
            self.menu.popup(QtGui.QCursor.pos())
            return True
        return False

    def mark_as_favorite(self):
        print(self.cfg.user_config_file)
        if self.parent().title == 'Companies':
            default = 'default_company'
        elif self.parent().title == 'Projects':
            default = 'default_project'
        print('Setting {} to: {}'.format(default, self.current_selection()))
        self.cfg.edit_user_config([default], self.current_selection())

    def current_selection(self):
        from cgl.core.cgl_info import create_full_project_cgl_info
        mdl_index = self.data_table.model().mapToSource(self.data_table.selectionModel().selectedRows()[0])
        mdl = self.data_table.model().sourceModel()
        row = mdl_index.row()
        return mdl.data_[row][0]

    def calculate_project_size(self):
        from cgl.core.cgl_info import create_full_project_cgl_info
        from cgl.core.config.config import user_config
        mdl_index = self.data_table.model().mapToSource(self.data_table.selectionModel().selectedRows()[0])
        mdl = self.data_table.model().sourceModel()
        row = mdl_index.row()
        project = mdl.data_[row][0]
        company = self.path_object.company
        branch = user_config()['default_branch'][company][project]
        create_full_project_cgl_info(company=company, project=project, branch=branch)

    def share_project(self):
        from cgl.core.path import PathObject
        from cgl.plugins.syncthing.utils import share_project, kill_syncthing, launch_syncthing
        mdl_index = self.data_table.model().mapToSource(self.data_table.selectionModel().selectedRows()[0])
        mdl = self.data_table.model().sourceModel()
        row = mdl_index.row()
        project = mdl.data_[row]
        path_object = self.path_object.copy()
        path_object.set_attr(project=project[0])
        share_project(path_object)

    def show_in_proj(self):
        from cgl.core.path import PathObject, show_in_project_management
        mdl_index = self.data_table.model().mapToSource(self.data_table.selectionModel().selectedRows()[0])
        mdl = self.data_table.model().sourceModel()
        row = mdl_index.row()
        sel = mdl.data_[row]
        print(sel)
        path_object = self.path_object.copy(project=sel[0])
        print(path_object.path_root)
        show_in_project_management(path_object)

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
    """
    GUI Element for Displaying shots, assets, and "my tasks"
    """
    button_clicked = QtCore.Signal(object)
    filter_changed = QtCore.Signal()
    add_clicked = QtCore.Signal()
    assign_clicked = QtCore.Signal(object)

    def __init__(self, parent, title, filter_string=None, path_object=None, search_box=None, cfg=None):
        QtWidgets.QWidget.__init__(self, parent)
        self.right_click = False

        self.v_layout = QtWidgets.QVBoxLayout(self)

        v_list = QtWidgets.QVBoxLayout()
        self.scope_layout = QtWidgets.QHBoxLayout()
        self.path_object = path_object
        if not cfg:
            print(AssetWidget)
            self.cfg = ProjectConfig(self.path_object)
        else:
            self.cfg = cfg
        self.shots_icon = QtGui.QPixmap(self.cfg.icon_path('shots24px.png'))
        self.assets_icon = QtGui.QPixmap(self.cfg.icon_path('assets24px.png'))
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
            self.message.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        except AttributeError:
            print('PySide2 Natively does not have QtWidgets.QSizePolicy')
        self.message.setAlignment(QtCore.Qt.AlignCenter)
        self.search_box = search_box
        self.add_button = QtWidgets.QToolButton()
        self.add_button.setText("add")
        self.add_button.setProperty('class', 'add_button')
        self.data_table = LJTableWidget(self, path_object=self.path_object)
        self.data_table.title = title
        self.data_table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.data_table.setMinimumWidth(min_width)
        # self.setProperty('class', 'basic')


        # tasks the filter options row
        self.assets_radio = QtWidgets.QRadioButton('Assets')
        self.shots_radio = QtWidgets.QRadioButton('Shots')
        self.tasks_radio = QtWidgets.QRadioButton('My Tasks')
        self.radio_group_scope = QtWidgets.QButtonGroup(self)
        self.radio_group_scope.addButton(self.shots_radio)
        self.radio_group_scope.addButton(self.assets_radio)
        self.radio_group_scope.addButton(self.tasks_radio)
        self.shot_icon = QtWidgets.QLabel()
        self.shot_icon.setPixmap(self.shots_icon)
        self.asset_icon = QtWidgets.QLabel()
        self.asset_icon.setPixmap(self.assets_icon)

        self.scope_layout.addWidget(self.tasks_radio)
        self.scope_layout.addWidget(self.shot_icon)
        self.scope_layout.addWidget(self.shots_radio)
        self.scope_layout.addWidget(self.asset_icon)
        self.scope_layout.addWidget(self.assets_radio)

        self.scope_layout.addStretch(1)
        self.scope_layout.addWidget(self.add_button)

        v_list.addItem(QtWidgets.QSpacerItem(0, 3, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Minimum))
        v_list.addWidget(self.data_table, 1)
        self.v_layout.addLayout(self.scope_layout)
        self.v_layout.addWidget(self.message)
        self.v_layout.addLayout(v_list)
        self.v_layout.setContentsMargins(0, 12, 0, 0)

        self.add_button.clicked.connect(self.on_add_button_clicked)

    def set_icon(self, scope='assets'):
        if scope == 'assets':
            self.shot_icon.setPixmap(self.assets_icon)
            self.add_button.setText('add asset')
        elif scope == 'shots':
            self.shot_icon.setPixmap(self.shots_icon)
            self.add_button.setText('add shot')

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
    copy_folder_path = QtCore.Signal()
    copy_file_path = QtCore.Signal()
    import_version_from = QtCore.Signal()
    share_download_link = QtCore.Signal()

    def __init__(self, parent, hide_header=True, cfg=None):
        LJTableWidget.__init__(self, parent)

        self.path_object = parent.parent().path_object
        if cfg:
            self.cfg = cfg
        else:
            self.cfg = ProjectConfig(self.path_object)
        self.project_management = self.cfg.project_config['account_info']['project_management']
        self.task = self.path_object.task
        self.sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding,
                                                QtWidgets.QSizePolicy.MinimumExpanding)
        self.setSortingEnabled(False)
        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.item_right_click_menu = LJMenu(self)
        self.item_right_click_menu.create_action("Show In Folder", self.show_in_folder)
        self.item_right_click_menu.create_action('Show in %s' % self.project_management, self.show_in_proj)
        self.item_right_click_menu.addSeparator()
        self.item_right_click_menu.create_action("Copy Folder Path", self.copy_folder_path)
        self.item_right_click_menu.create_action("Copy File Path", self.copy_file_path)
        self.item_right_click_menu.addSeparator()
        self.item_right_click_menu.create_action("Import Version From...", self.import_version_from)
        self.item_right_click_menu.addSeparator()
        # self.add_custom_task_items()
        self.item_right_click_menu.addSeparator()
        self.customContextMenuRequested.connect(self.item_right_click)

        # Set The Right Click Menu
        if hide_header:
            self.horizontalHeader().hide()

        self.setAcceptDrops(True)

    def show_in_proj(self):
        from cgl.core.path import show_in_project_management
        show_in_project_management(self.path_object)

    def item_right_click(self, position):
        self.item_right_click_menu.exec_(self.mapToGlobal(position))

    def sizeHint(self):
        return QtCore.QSize(350, 150)


class LJListWidget(QtWidgets.QWidget):
    def __init__(self, label, pixmap, empty_state_text='', empty_state_icon=None, search_box=None):
        QtWidgets.QWidget.__init__(self)
        self.setSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.Minimum)
        layout = QtWidgets.QVBoxLayout(self)
        self.label = QtWidgets.QLabel(label)
        self.label.setProperty('class', 'ultra_title')
        self.add_button = QtWidgets.QToolButton()
        self.add_button.setText('+')
        self.add_button.setProperty('class', 'add_button')
        self.h_layout = QtWidgets.QHBoxLayout()
        self.search_box = search_box
        layout.setContentsMargins(0, 0, 0, 0)
        if pixmap:
            self.icon = QtWidgets.QLabel()
            self.icon.setPixmap(pixmap)
            self.h_layout.addWidget(self.icon)
        self.h_layout.addWidget(self.label)
        self.h_layout.addStretch(1)
        self.h_layout.addWidget(self.add_button)
        self.list = QtWidgets.QListWidget()
        self.list.setProperty('class', 'basic')
        self.empty_state = QtWidgets.QPushButton(empty_state_text)
        if empty_state_icon:
            self.set_icon(empty_state_icon)
        self.empty_state.setSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.MinimumExpanding)
        self.empty_state.setProperty('class', 'empty_state2')
        self.empty_state.hide()
        layout.addLayout(self.h_layout)
        layout.addWidget(self.list)
        layout.addWidget(self.empty_state)

    def set_icon(self, icon):
        self.empty_state.setIcon(icon)

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

    def __init__(self, parent, company, variable):
        QtWidgets.QDialog.__init__(self, parent=parent)
        self.variable = variable
        self.company = company
        self.cfg = ProjectConfig(company=self.company)
        self.project_management = self.cfg.project_management
        self.proj_management_label = QtWidgets.QLabel('Project Management')
        layout = QtWidgets.QVBoxLayout(self)
        self.proj_management_combo = QtWidgets.QComboBox()
        self.proj_management_combo.addItems(['magic_browser', 'ftrack', 'shotgun', 'google_docs'])
        self.red_palette, self.green_palette, self.black_palette = define_palettes()

        self.server_label = QtWidgets.QLabel('server url:')
        self.api_key_label = QtWidgets.QLabel('api key:')
        self.api_user = QtWidgets.QLabel('api user:')
        self.server_line_edit = QtWidgets.QLineEdit()
        self.api_key_line_edit = QtWidgets.QLineEdit()
        self.api_user_line_edit = QtWidgets.QLineEdit()

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
        self.grid_layout.addWidget(self.proj_management_label, 2, 0)
        self.grid_layout.addWidget(self.proj_management_combo, 2, 1)
        self.grid_layout.addWidget(self.server_label, 3, 0)
        self.grid_layout.addWidget(self.server_line_edit, 3, 1)
        self.grid_layout.addWidget(self.api_key_label, 4, 0)
        self.grid_layout.addWidget(self.api_key_line_edit, 4, 1)
        self.grid_layout.addWidget(self.api_user, 5, 0)
        self.grid_layout.addWidget(self.api_user_line_edit, 5, 1)

        layout.addLayout(self.grid_layout)
        layout.addWidget(self.message)
        layout.addLayout(button_layout)

        self.proj_line_edit.textChanged.connect(self.on_project_text_changed)
        self.ok_button.clicked.connect(self.on_ok_clicked)
        self.cancel_button.clicked.connect(self.on_cancel_clicked)
        # self.proj_management_combo.currentIndexChanged.connect(self.on_pm_changed)
        self.adjust_to_variable()
        self.set_project_management()

    def set_project_management(self, proj_man=None):
        if not proj_man:
            proj_man = self.project_management
        index = self.proj_management_combo.findText(proj_man)
        self.proj_management_combo.setCurrentIndex(index)

    def adjust_to_variable(self):
        if self.variable == 'project':
            self.setWindowTitle('Create a Project')
            self.hide_api_info()
            # self.proj_management_combo.hide()
            # self.proj_management_label.hide()
        elif self.variable == 'company':
            self.setWindowTitle('Create a Company')
            self.hide_api_info()
            self.proj_management_combo.show()
            self.proj_management_label.show()

    def hide_api_info(self):
        self.server_label.hide()
        self.api_key_label.hide()
        self.api_user.hide()
        self.server_line_edit.hide()
        self.api_key_line_edit.hide()
        self.api_user_line_edit.hide()

    def show_api_info(self):
        self.server_label.show()
        self.api_key_label.show()
        self.api_user.show()
        self.server_line_edit.show()
        self.api_key_line_edit.show()
        self.api_user_line_edit.show()
        
    def on_pm_changed(self):
        if self.proj_management_combo.currentText() == 'magic_browser':
            self.hide_api_info()
        else:
            self.show_api_info()

    def on_project_text_changed(self):
        input_text = self.proj_line_edit.text()
        message = self.cfg.test_string_against_rules(input_text, self.variable, self.message)
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


class AdvComboBoxLabeled(QtWidgets.QVBoxLayout):
    def __init__(self, label):
        QtWidgets.QVBoxLayout.__init__(self)
        self.label = QtWidgets.QLabel("<b>%s</b>" % label)


class AdvComboBox(QtWidgets.QComboBox):
    def __init__(self, parent=None):
        super(AdvComboBox, self).__init__(parent)

        self.user_selected = False
        self.setFocusPolicy(QtCore.Qt.StrongFocus)
        self.setEditable(True)
        self.SizeAdjustPolicy(QtWidgets.QComboBox.AdjustToContents)
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
        self.setProperty('class', 'basic')
        self.setMinimumWidth(130)


        def filter_(text):
            self.pFilterModel.setFilterFixedString(str(text))

        self.lineEdit().textEdited[str].connect(filter_)
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
        obj_list = []
        for key in keys:
            if str(key) not in obj_list:
                obj_list.append(str(key))
        for item in obj_list:
            self.addItem(item)


class GifWidget(QtWidgets.QWidget):
    def __init__(self, parent=None, gif_path=None, animated=True):
        QtWidgets.QWidget.__init__(self, parent=parent)
        self.setProperty('class', 'gif_widget')
        self.animated = animated
        layout = QtWidgets.QHBoxLayout()
        self.image = QtWidgets.QLabel()
        self.label_1 = QtWidgets.QLabel('Working...')
        self.label_2 = QtWidgets.QLabel('Working...')
        self.label_1.setProperty('class', 'feedback')
        self.label_2.setProperty('class', 'feedback')
        self.label_1.setSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.Minimum)
        self.label_2.setSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.Minimum)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Create the Actual Gif Thingy
        if animated:
            self.gif = QtGui.QMovie(gif_path)
            self.image.setMovie(self.gif)
        else:
            self.gif = QtGui.QPixmap(gif_path)
            self.image.setPixmap(self.gif)

        self.gif.setScaledSize(QtCore.QSize(120, 80))
        layout.addWidget(self.label_1)
        layout.addWidget(self.image)
        layout.addWidget(self.label_2)
        self.setLayout(layout)

    def start(self):
        if self.animated:
            self.show()
            self.gif.start()

    def stop(self):
        self.gif.stop()
        self.hide()



