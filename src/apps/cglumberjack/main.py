import glob
import os
import shutil
import logging
from Qt import QtWidgets, QtCore, QtGui
from cglcore.config import app_config, UserConfig
from cglui.widgets.combo import AdvComboBox, LabelComboRow
from cglui.widgets.base import LJMainWindow
from cglui.widgets.search import LJSearchEdit
from cglui.widgets.containers.table import LJTableWidget
from cglui.widgets.containers.model import ListItemModel
from cglui.widgets.containers.menu import LJMenu
from cglui.widgets.dialog import InputDialog, LoginDialog
from cglcore.path import PathObject, CreateProductionData, start, replace_illegal_filename_characters, show_in_folder, create_project_config
from asset_ingestor_widget import AssetIngestor


class LabelEditRow(QtWidgets.QVBoxLayout):
    def __init__(self, label):
        QtWidgets.QVBoxLayout.__init__(self)
        self.label = QtWidgets.QLabel("<b>%s</b>" % label)
        self.lineEdit = QtWidgets.QLineEdit()
        self.addWidget(self.label)
        self.addWidget(self.lineEdit)


class ProjectWidget(QtWidgets.QWidget):
    button_clicked = QtCore.Signal(object)
    filter_changed = QtCore.Signal()
    add_clicked = QtCore.Signal()
    assign_clicked = QtCore.Signal(object)

    def __init__(self, parent, title, filter_string=None, path_object=None):
        QtWidgets.QWidget.__init__(self, parent)
        v_layout = QtWidgets.QVBoxLayout(self)
        h_layout = QtWidgets.QHBoxLayout()
        self.path_object = path_object
        self.tool_button_layout = QtWidgets.QHBoxLayout()
        self.sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.MinimumExpanding)
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
        self.data_table.setMinimumWidth(220)

        # this is where the filter needs to be!
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
        self.sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.MinimumExpanding)
        self.setSizePolicy(self.sizePolicy)
        self.filter_string = filter_string
        self.label = title
        self.title = QtWidgets.QLabel("<h2>Project: %s</h2>" % title)
        self.scope_title = QtWidgets.QLabel("<b>%s</b>" % 'Assets')
        self.task = None
        self.user = None
        minWidth = 340

        self.message = QtWidgets.QLabel("")
        self.message.setMinimumWidth(minWidth)
        # doesn't work on mac - self.message.setSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
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

        self.radio_layout = QtWidgets.QHBoxLayout()
        # create a button group for these radio buttons
        self.radio_group2 = QtWidgets.QButtonGroup(self)
        self.radio_user = QtWidgets.QRadioButton('My Assignments')
        self.radio_everything = QtWidgets.QRadioButton('Everything')
        self.radio_publishes = QtWidgets.QRadioButton('Publishes')
        self.radio_group2.addButton(self.radio_user)
        self.radio_group2.addButton(self.radio_everything)
        self.radio_group2.addButton(self.radio_publishes)
        # self.radio_layout.addWidget(self.title)
        self.radio_layout.addItem(QtWidgets.QSpacerItem(0, 0, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum))
        self.radio_layout.addWidget(self.radio_everything)
        self.radio_layout.addWidget(self.radio_user)
        self.radio_layout.addWidget(self.radio_publishes)

        # this is where the filter needs to be!
        scope_layout.addWidget(self.scope_title)
        scope_layout.addItem(QtWidgets.QSpacerItem(0, 0, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum))
        scope_layout.addWidget(self.shots_radio)
        scope_layout.addWidget(self.assets_radio)
        scope_layout.addWidget(self.add_button)

        #v_list.setSpacing(2)
        v_list.addItem(QtWidgets.QSpacerItem(0, 3, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Minimum))
        v_list.addWidget(self.search_box)
        v_list.addWidget(self.data_table, 1)

        self.v_layout.addWidget(self.title)
        self.v_layout.addItem(QtWidgets.QSpacerItem(0, 4, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Minimum))
        self.v_layout.addLayout(self.radio_layout)
        self.v_layout.addItem(QtWidgets.QSpacerItem(0, 8, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Minimum))
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
        self.versions = AdvComboBox()
        #self.versions.setMinimumWidth(200)
        self.versions.hide()
        self.setMinimumWidth(300)

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
        self.assign_button = QtWidgets.QPushButton()
        self.assign_button.setText("Create Assignment")
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

        v_layout.addLayout(task_row)
        # v_layout.addWidget(self.message)
        v_layout.addWidget(self.assign_button)
        v_layout.addLayout(self.users_layout)
        v_layout.addLayout(self.resolutions_layout)
        v_layout.addWidget(self.data_table, 1)
        v_layout.addItem((QtWidgets.QSpacerItem(0, 25, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Minimum)))
        v_layout.addLayout(self.tool_button_layout)
        self.setLayout(v_layout)
        self.hide_combos()

        self.assign_button.hide()
        self.hideall()
        self.show_button.clicked.connect(self.on_show_button_clicked)
        self.hide_button.clicked.connect(self.on_hide_button_clicked)
        # self.add_button.clicked.connect(self.on_add_button_clicked)
        self.assign_button.clicked.connect(self.on_assign_button_clicked)
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

    def hide_filters(self):
        self.category_combo.hide()
        self.category_label.hide()
        self.assets_radio.hide()
        self.shots_radio.hide()

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
        self.data_table.set_item_model(mdl)
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

    def on_assign_button_clicked(self):
        self.assign_clicked.emit(self.path_object)

    def set_title(self, new_title):
        self.title.setText('<b>%s</b>' % new_title.title())


class CGLumberjackWidget(QtWidgets.QWidget):

    def __init__(self, parent=None, user_name=None, user_email=None, company=None, path=None, radio_filter=None):
        QtWidgets.QWidget.__init__(self, parent)
        # Environment Stuff
        self.user = user_name
        self.default_user = user_name
        self.user_email = user_email
        self.user_name = user_name
        self.company = company
        self.user_default = self.user
        layout = QtWidgets.QVBoxLayout(self)
        self.h_layout = QtWidgets.QHBoxLayout()
        self.project_management = app_config(company=self.company)['account_info']['project_management']  # Company Specific
        self.root = app_config()['paths']['root']  # Company Specific
        self.user_root = app_config()['cg_lumberjack_dir']
        self.user = None
        self.context = 'source'
        self.initial_path_object = None
        self.radio_filter = radio_filter
        if path:
            self.initial_path_object = PathObject(path)
        self.project = '*'
        self.scope = 'assets'
        self.shot = '*'
        self.seq = '*'
        if self.initial_path_object:
            if self.initial_path_object.project:
                self.project = self.initial_path_object.project
            if self.initial_path_object.scope:
                self.scope = self.initial_path_object.scope
            if self.initial_path_object.shot:
                self.shot = self.initial_path_object.shot
            if self.initial_path_object.seq:
                self.seq = self.initial_path_object.seq
        self.user_favorites = ''
        self.version = ''
        self.task = ''
        self.resolution = ''
        self.current_location = {}
        self.path_root = ''
        self.path = ''

        # Create the Left Panel
        self.filter_layout = QtWidgets.QVBoxLayout()
        # company
        self.company_widget = LabelComboRow('Company')
        # filters
        self.project_filter = ProjectWidget(self, title="Projects")

        # assemble the filter_panel
        self.filter_layout.addLayout(self.company_widget)
        self.filter_layout.addWidget(self.project_filter)
        self.filter_layout.setSpacing(0)
        self.filter_layout.setContentsMargins(0, 10, 0, 0)

        # Create the Middle Panel
        self.middle_layout = QtWidgets.QVBoxLayout()
        self.assets = None
        self.assets_filter_default = filter
        self.middle_layout.setContentsMargins(10, 0, 10, 0)

        # Create the Right Panel

        # Create Empty layouts for tasks as well as renders.
        self.task_layout = QtWidgets.QVBoxLayout()
        self.task_layout.setContentsMargins(0, 10, 0, 0)
        self.render_layout = QtWidgets.QVBoxLayout()

        # create the current path
        self.current_location_label = QtWidgets.QLabel('Current Location')
        self.current_location_line_edit = QtWidgets.QLineEdit()
        self.current_location_line_edit.setReadOnly(True)
        self.cl_row = QtWidgets.QHBoxLayout()
        self.cl_row.addWidget(self.current_location_label)
        self.cl_row.addWidget(self.current_location_line_edit)

        # assemble the main h layoutQtWidgets.QLabel("<b>%s</b>" % title)
        # lineA = QtWidgets.QFrame()
        # lineA.setFrameShape(QtWidgets.QFrame.VLine)
        # lineA.setFrameShadow(QtWidgets.QFrame.Sunken)
        # lineA.setMinimumHeight(100)

        self.h_layout.addLayout(self.filter_layout)
        # self.h_layout.addWidget(lineA)
        self.h_layout.addLayout(self.middle_layout)
        self.h_layout.addLayout(self.task_layout)
        self.h_layout.addLayout(self.render_layout)
        #self.h_layout.addItem(QtWidgets.QSpacerItem(0, 0, QtWidgets.QSizePolicy.Expanding,
        #                                            QtWidgets.QSizePolicy.Minimum))
        self.h_layout.addStretch()
        self.h_layout.setSpacing(10)
        layout.addLayout(self.cl_row)
        layout.addLayout(self.h_layout)

        self.check_default_company_globals()
        self.load_companies()
        self.load_projects()
        # self.load_assets()
        # create connections
        self.project_filter.data_table.selected.connect(self.on_project_changed)
        self.company_widget.add_button.clicked.connect(self.on_create_company)
        self.project_filter.add_button.clicked.connect(self.on_create_project)
        self.company_widget.combo.currentIndexChanged.connect(self.on_company_changed)

    def check_default_company_globals(self):
        if self.company:
            if not os.path.exists(os.path.join(self.user_root, 'companies', self.company)):
                os.makedirs(os.path.join(self.user_root, 'companies', self.company))

    def on_filter_radio_changed(self):
        if self.sender().text() == 'Assets':
            self.scope = 'assets'
        elif self.sender().text() == 'Shots':
            self.scope = 'shots'
        self.assets.set_scope_title(self.scope)
        self.current_location['scope'] = self.scope
        self.on_project_changed(data=None, cmd=True)

    def on_user_radio_changed(self):
        self.set_user_from_radio_buttons()
        self.assets_filter_default = self.user
        if self.user == '':
            self.task = ''
        elif self.user == '*':
            self.task = ''
        else:
            self.task = '*'
        self.version = ''
        self.resolution = ''
        self.seq = '*'
        self.shot = '*'
        self.clear_layout(self.task_layout)
        self.clear_layout(self.render_layout)
        self.update_location()
        self.load_assets()

    def set_scope_radio(self):
        if self.scope == 'assets':
            self.assets.assets_radio.setChecked(True)
            self.assets.shots_radio.setChecked(False)
        elif self.scope == 'shots':
            self.assets.shots_radio.setChecked(True)
            self.assets.assets_radio.setChecked(False)

    # UI interface Functions / Stuff that happens when buttons get clicked/changed.
    def on_company_changed(self):
        self.company = self.company_widget.combo.currentText()
        self.project_management = app_config(company=self.company)['account_info']['project_management']  # Company Specific
        self.root = app_config()['paths']['root']  # Company Specific
        self.user_root = app_config()['cg_lumberjack_dir']
        self.load_projects()
        if self.middle_layout:
            self.clear_layout(self.middle_layout)
        if self.task_layout:
            self.clear_layout(self.task_layout)
        if self.render_layout:
            self.clear_layout(self.render_layout)

    def on_create_company(self):
        dialog = InputDialog(title='Create Company', message='Type a Company Name & Choose Project Management',
                             line_edit=True, combo_box_items=['lumbermil', 'ftrack', 'shotgun'], line_edit_text='Name')
        dialog.exec_()
        if dialog.button == 'Ok':
            self.company = '%s' % dialog.line_edit.text()
            d = {'root': self.root,
                 'company': self.company}
            self.create_company_globals(dialog.line_edit.text())
            CreateProductionData(d)
            self.load_companies(company=self.company)
            self.load_projects()

    def create_company_globals(self, company):
        print '##########################################'
        print 'Creating Company Globlas %s' % company
        dir_ = os.path.join(self.user_root, 'companies', company)
        if not os.path.exists(dir_):
            print '%s doesnt exist, making it' % dir_
            os.makedirs(dir_)

    def on_create_project(self):
        print 'CURRENT LOCATION: %s' % self.current_location
        dialog = InputDialog(title='Create Project', message='Type a Project Name & Choose Proj Management',
                             line_edit=True, combo_box_items=['lumbermill', 'shotgun', 'ftrack'])
        dialog.exec_()
        if dialog.button == 'Ok':
            project_name = dialog.line_edit.text()
            self.project = project_name
            self.update_location()
            CreateProductionData(self.current_location, project_management=self.project_management)
            production_management = dialog.combo_box.currentText()
            print 'setting project management to %s' % production_management
            self.load_projects()
            create_project_config(self.company, self.project)
        else:
            pass

    def on_create_asset(self, set_vars=False):
        import asset_creator
        if 'asset' in self.current_location:
            task_mode = True
        else:
            task_mode = False
        dialog = asset_creator.AssetCreator(self, path_dict=self.current_location, task_mode=task_mode)
        dialog.exec_()
        self.on_project_changed([[self.current_location['project']]])

    def on_file_dragged_to_assets(self, data):
        dialog = AssetIngestor(self, path_dict=self.current_location, current_user=self.user_default)
        dialog.on_files_added(data)
        dialog.exec_()
        self.load_assets()

    def on_task_version_changed(self):
        self.reload_task_widget(self.sender().parent(), populate_versions=False)

    def on_task_user_changed(self):
        self.reload_task_widget(self.sender().parent())

    def on_task_resolution_changed(self):
        print 'resolution changed %s' % self.sender().currentText()

    def on_assign_button_clicked(self, data):
        task = self.sender().task
        dialog = InputDialog(title="Make an %s Assignment" % task,
                             combo_box_items=[self.default_user],
                             message='Type or Choose the username for assignment',
                             buttons=['Cancel', 'Assign Task'])
        dialog.exec_()
        if dialog.button == 'Assign Task':
            self.task = task
            self.user = dialog.combo_box.currentText()
            self.version = '000.000'
            self.resolution = 'high'
            self.shot = data.shot
            self.seq = data.seq
            self.update_location()
            CreateProductionData(path_object=self.current_location, project_management=self.project_management)
        data = self.assets.data_table.row_selected()
        self.on_main_asset_selected(data)

    def on_source_selected(self, data):
        # clear everything
        object_ = PathObject(self.current_location)
        parent = self.sender().parent()
        object_.set_attr(root=self.root)
        object_.set_attr(version=parent.versions.currentText())
        object_.set_attr(context='source')
        object_.set_attr(resolution=parent.resolutions.currentText())
        object_.set_attr(user=parent.users.currentText())
        object_.set_attr(task=self.sender().task)
        try:
            object_.set_attr(filename=data[0][0])
            filename_base, ext = os.path.splitext(data[0][0])
            object_.set_attr(filename_base=filename_base)
            object_.set_attr(ext=ext.replace('.', ''))
        except IndexError:
            # this indicates a selection within the module, but not a specific selected files
            pass
        self.update_location(object_)
        self.clear_task_selection_except(self.sender().task)
        self.sender().parent().show_tool_buttons()
        self.load_render_files()
        if object_.context == 'source':
            self.sender().parent().review_button.hide()
            self.sender().parent().publish_button.hide()

    def on_render_selected(self, data):
        object_ = PathObject(self.current_location)
        object_.set_attr(root=self.root)
        object_.set_attr(context='render')
        object_.set_attr(filename=data[0][0])
        self.update_location(object_)
        self.sender().parent().show_tool_buttons()
        self.clear_task_selection_except()

    def on_project_changed(self, data, cmd=False):
        if not cmd:
            self.project = data[0][0]
        # reset the env vars after a project change
        self.seq = '*'
        self.shot = '*'
        self.resolution = ''
        self.version = ''
        self.task = ''
        self.user = None
        # build the asset Widget
        self.clear_layout(self.middle_layout)
        self.assets = AssetWidget(self, title="")
        if not self.radio_filter:
            self.assets.radio_everything.setChecked(True)
        elif self.radio_filter == 'Everything':
            self.assets.radio_everything.setChecked(True)
        elif self.radio_filter == 'My Assignments':
            self.assets.radio_user.setChecked(True)
        elif self.radio_filter == 'Publishes':
            self.assets.radio_publishes.setChecked(True)
        self.set_scope_radio()
        self.assets.set_title('<b>%s</b>' % self.project)
        self.assets.set_scope_title('<b>%s</b>' % self.scope)
        self.assets.add_button.show()

        # update location and display the resulting assets.
        self.update_location()
        self.middle_layout.addWidget(self.assets)

        self.load_assets()
        self.clear_layout(self.task_layout)
        self.clear_layout(self.render_layout)
        self.assets.data_table.selected.connect(self.on_main_asset_selected)

        self.assets.shots_radio.clicked.connect(self.on_filter_radio_changed)
        self.assets.assets_radio.clicked.connect(self.on_filter_radio_changed)
        self.assets.radio_publishes.clicked.connect(self.on_user_radio_changed)
        self.assets.radio_everything.clicked.connect(self.on_user_radio_changed)
        self.assets.radio_user.clicked.connect(self.on_user_radio_changed)

    def on_main_asset_selected(self, data):
        # data format: ['Project', 'Seq', 'Shot', 'Task', 'User', 'Path']
        if data:
            # reset the GUI
            self.task_layout.tasks = []
            self.clear_layout(self.task_layout)
            self.clear_layout(self.render_layout)
            task_label = QtWidgets.QLabel('<H2>Tasks</H2>')
            task_add = QtWidgets.QToolButton()
            task_add.setText('+')
            task_label_layout = QtWidgets.QHBoxLayout()
            # task_label_layout.addWidget(task_label)

            self.task_layout.addWidget(task_label)
            self.task_layout.addItem((QtWidgets.QSpacerItem(0, 32, QtWidgets.QSizePolicy.Minimum,
                                                            QtWidgets.QSizePolicy.Minimum)))
            self.task_layout.addLayout(task_label_layout)

            # set our current location
            path = data[0][2]
            current = PathObject(str(path))

            current.set_attr(task='*')
            current.set_attr(root=self.root)
            current.set_attr(user_email=self.user_email)
            self.task_layout.seq = current.seq
            self.task_layout.shot = current.shot
            task_add.clicked.connect(self.on_create_asset)
            self.update_location(path_object=current)
            # Get the list of tasks for the selection
            task_list = current.glob_project_element('task')
            task_label_layout.addItem(QtWidgets.QSpacerItem(0, 0, QtWidgets.QSizePolicy.Expanding,
                                                            QtWidgets.QSizePolicy.Minimum))
            for task in task_list:
                task_radio = QtWidgets.QCheckBox(task)
                task_label_layout.addWidget(task_radio)
                if '.' not in task:
                    if task not in self.task_layout.tasks:
                        # version_location = copy.copy(self.current_location)
                        task_widget = TaskWidget(parent=self,
                                                 title=app_config()['pipeline_steps']['short_to_long'][task],
                                                 short_title=task,
                                                 path_object=current)
                        task_widget.task = task
                        task_widget.showall()
                        task_widget.hide_button.hide()
                        task_widget.show_button.show()

                        # find the version information for the task:
                        user = self.populate_users_combo(task_widget, current, task)
                        version = self.populate_versions_combo(task_widget, current, task)
                        resolution = self.populate_resolutions_combo(task_widget, current, task)
                        self.task_layout.addWidget(task_widget)
                        self.task_layout.tasks.append(task)
                        version_obj = current.copy(task=task, user=user, version=version,
                                                   resolution=resolution, filename='*')
                        task_widget.data_table.task = version_obj.task
                        task_widget.data_table.user = version_obj.user
                        task_widget.data_table.version = version_obj.version
                        task_widget.data_table.resolution = version_obj.resolution
                        files_ = version_obj.glob_project_element('filename')
                        task_widget.setup(ListItemModel(self.prep_list_for_table(files_, split_for_file=True),
                                                        ['Name']))
                        task_widget.data_table.selected.connect(self.on_source_selected)
                        task_widget.data_table.doubleClicked.connect(self.on_open_clicked)
                        task_widget.open_button_clicked.connect(self.on_open_clicked)
                        task_widget.new_version_clicked.connect(self.on_new_version_clicked)
                        task_widget.versions.currentIndexChanged.connect(self.on_task_version_changed)
                        task_widget.users.currentIndexChanged.connect(self.on_task_user_changed)
                        task_widget.resolutions.currentIndexChanged.connect(self.on_task_resolution_changed)
                        task_widget.assign_clicked.connect(self.on_assign_button_clicked)
                        task_widget.data_table.dropped.connect(self.on_file_dragged_to_source)
                        task_widget.data_table.show_in_folder.connect(self.show_in_folder)
                        task_widget.data_table.show_in_shotgun.connect(self.show_in_shotgun)
                        task_widget.data_table.copy_folder_path.connect(self.copy_folder_path)
                        task_widget.data_table.copy_file_path.connect(self.copy_file_path)
                        task_widget.data_table.import_version_from.connect(self.import_versions_from)
                        task_widget.data_table.push_to_cloud.connect(self.push)
                        task_widget.data_table.pull_from_cloud.connect(self.pull)
                        task_widget.data_table.share_download_link.connect(self.share_download_link)
                        if not user:
                            task_widget.users_label.hide()
                            task_widget.users.hide()
                            task_widget.data_table.hide()
                            task_widget.versions.hide()
                            task_widget.show_button.hide()
                            task_widget.assign_button.show()
            task_label_layout.addWidget(task_add)
            self.task_layout.addItem((QtWidgets.QSpacerItem(0, 0, QtWidgets.QSizePolicy.Minimum,
                                                            QtWidgets.QSizePolicy.Expanding)))

    def show_in_folder(self):
        show_in_folder(self.path_root)

    def show_in_shotgun(self):
        CreateProductionData(path_object=self.current_location, file_system=False, do_scope=False, test=False, json=True)

    def copy_folder_path(self):
        clipboard = QtWidgets.QApplication.clipboard()
        clipboard.setText(os.path.dirname(self.path_root))

    def copy_file_path(self):
        clipboard = QtWidgets.QApplication.clipboard()
        clipboard.setText(self.path_root)

    def import_versions_from(self):
        print 'import versions'

    def push(self):
        print 'push'

    def pull(self):
        print 'pull'

    def share_download_link(self):
        print 'download link'

    def on_new_version_clicked(self):
        current = PathObject(self.current_location)
        next_minor = current.new_minor_version_object()
        shutil.copytree(os.path.dirname(current.path_root), os.path.dirname(next_minor.path_root))
        CreateProductionData(next_minor)
        # reselect the original asset.
        data = [[current.seq, current.shotname, current.path_root, '', '']]
        self.on_main_asset_selected(data)

    def on_open_clicked(self):
        if '####' in self.path_root:
            print 'Nothing set for sequences yet'
            # config = app_config()['paths']
            # settings = app_config()['default']
            # cmd = "%s -framerate %s %s" % (config['ffplay'], settings['frame_rate'], self.path_root.replace('####', '%04d'))
            # subprocess.Popen(cmd)
        else:
            start(self.path_root)

    # LOAD FUNCTIONS
    def on_file_dragged_to_source(self, data):
        # Only do this if it's dragged into a thing that hasn't been selected
        object_ = PathObject(self.current_location)
        parent = self.sender().parent()
        object_.set_attr(root=self.root)
        object_.set_attr(version=parent.versions.currentText())
        object_.set_attr(context='source')
        object_.set_attr(resolution=parent.resolutions.currentText())
        object_.set_attr(user=parent.users.currentText())
        object_.set_attr(task=self.sender().task)
        self.update_location(object_)
        self.clear_task_selection_except(self.sender().task)
        for d in data:
            if os.path.isfile(d):
                path_, filename_ = os.path.split(d)
                # need to make the filenames safe (no illegal chars)
                filename_ = replace_illegal_filename_characters(filename_)
                logging.info('Copying File From %s to %s' % (d, os.path.join(self.path_root, filename_)))
                shutil.copy2(d, os.path.join(self.path_root, filename_))
                self.reload_task_widget(self.sender().parent())
            elif os.path.isdir(d):
                print 'No support for directories yet'

    def reload_task_widget(self, widget, populate_versions=True):
        path_obj = PathObject(self.current_location)
        path_obj.set_attr(filename='*')
        path_obj.set_attr(user=widget.users.currentText())
        if populate_versions:
            path_obj.set_attr(version=self.populate_versions_combo(widget, path_obj, widget.label))
        else:
            path_obj.set_attr(version=widget.versions.currentText())
            path_obj.set_attr(resolution=widget.resolutions.currentText())
        path_obj.set_attr(task=widget.task)
        self.update_location(path_obj)
        files_ = path_obj.glob_project_element('filename')
        widget.setup(ListItemModel(self.prep_list_for_table(files_), ['Name']))
        self.clear_layout(self.render_layout)

    def load_render_files(self):
        self.clear_layout(self.render_layout)
        current = PathObject(self.current_location)
        renders = current.copy(context='render', filename='*')
        files_ = renders.glob_project_element('filename')
        if files_:
            label = QtWidgets.QLabel('<b>%s: Published Files</b>' % renders.task)
            render_widget = TaskWidget(self, 'Output', 'Output')
            render_widget.showall()
            render_widget.title.hide()
            # render_widget.search_box.hide()
            render_widget.hide_button.hide()
            self.render_layout.addWidget(label)
            self.render_layout.addWidget(render_widget)
            self.render_layout.addItem((QtWidgets.QSpacerItem(340, 0, QtWidgets.QSizePolicy.Minimum,
                                                              QtWidgets.QSizePolicy.Expanding)))
            render_widget.setup(ListItemModel(self.prep_list_for_table(files_, split_for_file=True), ['Name']))
            render_widget.data_table.selected.connect(self.on_render_selected)
        else:
            print 'No Published Files for %s' % current.path_root

    def populate_users_combo(self, widget, path_object, task):
        object_ = path_object.copy(user='*', task=task)
        users = object_.glob_project_element('user')
        for each in users:
            widget.users.addItem(each)
        # set the combo box according to what filters are currently selected.
        widget.users.hide()
        widget.users_label.hide()
        self.set_user_from_radio_buttons()
        if self.user == '*':
            widget.users.show()
            widget.users_label.show()
        elif self.user == 'publish':
            index_ = widget.users.findText('publish')
            if index_ != -1:
                widget.users.setCurrentIndex(index_)
                self.user = 'publish'
        else:
            index_ = widget.users.findText(self.user_default)
            if index_ != -1:
                widget.users.setCurrentIndex(index_)
                self.user = self.user_default
        return widget.users.currentText()

    @staticmethod
    def populate_versions_combo(task_widget, path_object, task):
        task_widget.versions.show()
        task_widget.versions.clear()
        object_ = path_object.copy(user=task_widget.users.currentText(), task=task, version='*')
        items = object_.glob_project_element('version')
        for each in items:
            task_widget.versions.insertItem(0, each)
        if len(items) == 1:
            task_widget.versions.setEnabled(False)
        else:
            task_widget.versions.setEnabled(True)
            task_widget.versions.setCurrentIndex(0)
        return task_widget.versions.currentText()

    @staticmethod
    def populate_resolutions_combo(task_widget, path_object, task):

        object_ = path_object.copy(user=task_widget.users.currentText(), task=task, version=task_widget.versions.currentText(),
                                   resolution='*')
        items = object_.glob_project_element('resolution')
        for each in items:
            task_widget.resolutions.addItem(each)
        index_ = task_widget.resolutions.findText('high')
        if index_:
            task_widget.resolutions.setCurrentIndex(index_)
        return task_widget.resolutions.currentText()

    def load_projects(self):
        d = {'root': self.root,
             'company': self.company,
             'project': '*',
             'context': 'source'}
        path_object = PathObject(d)
        projects = path_object.glob_project_element('project')
        if not projects:
            print 'no projects'
            self.project_filter.search_box.setEnabled(False)
            self.project_filter.data_table.setEnabled(False)
            self.project_filter.add_button.setText('Create First Project')
        else:
            self.project_filter.search_box.setEnabled(True)
            self.project_filter.data_table.setEnabled(True)
            self.project_filter.add_button.setText('+')
        self.project_filter.setup(ListItemModel(self.prep_list_for_table(projects, split_for_file=True), ['Name']))
        if self.project != '*':
            self.project_filter.data_table.select_row_by_text(self.project)
            self.on_project_changed(data=[self.project], cmd=True)
        self.update_location()

    def load_companies(self, company=None):
        self.company_widget.combo.clear()
        companies_dir = os.path.join(self.user_root, 'companies')
        if os.path.exists(companies_dir):
            companies = os.listdir(companies_dir)
            if not companies:
                dialog = InputDialog(buttons=['Create Company', 'Find Company'], message='No companies found in Config'
                                                                                         'location %s:' % companies_dir)
                dialog.exec_()
                if dialog.button == 'Create Company':
                    print 'Create Company pushed'
                elif dialog.button == 'Find Company':
                    company_paths = QtWidgets.QFileDialog.getExistingDirectory(self,
                                                                               'Choose existing company(ies) to add to '
                                                                               'the registry', self.root,
                                                                               QtWidgets.QFileDialog.ShowDirsOnly)
                    company = os.path.split(company_paths)[-1]
                    companies.append(company)
                    os.makedirs(os.path.join(companies_dir, company))
                # ask me to type the name of companies i'm looking for?
                # ask me to create a company if there are none at all.
                # Open the location and ask me to choose folders that are companies
        else:
            return

        self.company_widget.combo.addItem('')
        for each in companies:
            c = os.path.split(each)[-1]
            self.company_widget.combo.addItem(c)
        if not company:
            company = self.company
        index = self.company_widget.combo.findText(company)
        if index:
            self.company_widget.combo.setCurrentIndex(index)
        else:
            self.company_widget.combo.setCurrentIndex(0)

    def load_assets(self):
        # TODO it'd be cool to pass an asset and be able to selected it if passed.
        self.clear_layout(self.task_layout)
        self.clear_layout(self.render_layout)
        red_palette = QtGui.QPalette()
        red_palette.setColor(self.foregroundRole(), QtGui.QColor(255, 0, 0))
        self.assets.data_table.clearSpans()
        current = PathObject(self.current_location)
        items = glob.glob(current.path_root)
        data = []
        temp_ = []
        self.assets.add_button.clicked.connect(self.on_create_asset)
        if items:
            self.assets.data_table.show()
            self.assets.search_box.show()
            self.assets.message.hide()
            self.assets.radio_publishes.show()
            self.assets.radio_everything.show()
            self.assets.radio_user.show()
            self.assets.scope_title.show()
            self.assets.message.setText('')
            for each in items:
                obj_ = PathObject(str(each))
                d = obj_.data
                shot_name = '%s_%s' % (d['seq'], d['shot'])
                if shot_name not in temp_:
                    temp_.append(shot_name)
                    if d['scope'] == 'assets':
                        data.append([d['seq'], d['shot'], each, '', ''])
                    elif d['scope'] == 'shots':
                        data.append([d['seq'], shot_name, each, '', ''])
            if d['scope'] == 'assets':
                self.assets.setup(ListItemModel(data, ['Category', 'Name', 'Path', 'Due Date', 'Status']))
                self.assets.data_table.hideColumn(0)
            elif d['scope'] == 'shots':
                self.assets.setup(ListItemModel(data, ['Seq', 'Shot', 'Path', 'Due Date', 'Status']))
                self.assets.data_table.hideColumn(0)
            self.assets.data_table.hideColumn(2)
            self.assets.data_table.set_draggable(True)
            self.assets.data_table.dropped.connect(self.on_file_dragged_to_assets)
        else:
            self.assets.scope_title.hide()
            self.assets.data_table.hide()
            self.assets.search_box.hide()
            self.assets.radio_publishes.hide()
            self.assets.radio_everything.hide()
            self.assets.radio_user.hide()
            self.assets.message.setText('No %s Found! \nClick + button to create %s' % (self.scope.title(), self.scope))
            self.assets.message.setPalette(red_palette)
            self.assets.message.show()

    # CLEAR/DELETE FUNCTIONS

    def clear_task_selection_except(self, task=None):
        layout = self.task_layout
        i = -1
        while i <= layout.count():
            i += 1
            child = layout.itemAt(i)
            if child:
                if child.widget():
                    if isinstance(child.widget(), AssetWidget):
                        if task:
                            if task != child.widget().data_table.task:
                                child.widget().hide_tool_buttons()
                                child.widget().data_table.clearSelection()
                        else:
                            child.widget().hide_tool_buttons()
                            child.widget().data_table.clearSelection()
        return

    def clear_layout(self, layout):
        while layout.count():
            child = layout.takeAt(0)
            if child.widget() is not None:
                child.widget().deleteLater()
            elif child.layout() is not None:
                self.clear_layout(child.layout())

    # CONVENIENCE FUNCTIONS

    def set_user_from_radio_buttons(self):
        if self.assets.radio_publishes.isChecked():
            self.user = 'publish'
        elif self.assets.radio_user.isChecked():
            self.user = self.user_default
        elif self.assets.radio_everything.isChecked():
            self.user = ''

    def update_location(self, path_object=None):
        if path_object:
            self.current_location_line_edit.setText(path_object.path_root)
            self.current_location = path_object.data
            self.path_root = path_object.path_root
            self.path = path_object.path
            return self.path_root
        else:
            self.current_location = {'company': self.company, 'root': self.root, 'scope': self.scope,
                                     'context': self.context, 'project': self.project, 'seq': self.seq,
                                     'shot': self.shot, 'user': self.user,
                                     'version': self.version, 'task': self.task,
                                     'resolution': self.resolution, 'user_email': self.user_email
                                     }
            path_obj = PathObject(self.current_location)
            self.path_root = path_obj.path_root
            self.path = path_obj.path
            self.current_location_line_edit.setText(self.path_root)
            return self.path_root

    @staticmethod
    def append_unique_to_list(item, item_list):
        if item not in item_list:
            item_list.append(item)
        return item_list

    @staticmethod
    def prep_list_for_table(list_, path_filter=None, split_for_file=False):
        # TODO - would be awesome to make this smart enough to know what to do with a dict, list, etc...
        list_.sort()
        output_ = []
        for each in list_:
            if path_filter:
                filtered = PathObject(each).data[path_filter]
                output_.append([filtered])
            else:
                if split_for_file:
                    each = os.path.split(each)[-1]
                output_.append([each])
        return output_


class CGLumberjack(LJMainWindow):
    def __init__(self):
        LJMainWindow.__init__(self)
        self.user_name = ''
        self.user_email = ''
        self.company = ''
        self.previous_path = ''
        self.filter = 'Everything'
        self.previous_paths = {}
        self.load_user_config()
        if not self.user_name:
            self.on_login_clicked()
        self.setCentralWidget(CGLumberjackWidget(self, user_email=self.user_email,
                                                 user_name=self.user_name,
                                                 company=self.company,
                                                 path=self.previous_path,
                                                 radio_filter=self.filter))
        if self.user_name:
            self.setWindowTitle('CG Lumberjack - Logged in as %s' % self.user_name)
        else:
            self.setWindowTitle("CG Lumberjack - Log In")
        self.status_bar = QtWidgets.QStatusBar()
        self.setStatusBar(self.status_bar)
        w = 400
        h = 500

        self.resize(w, h)
        menu_bar = self.menuBar()
        two_bar = self.menuBar()
        icon = QtGui.QPixmap(":images/'lumberjack.24px.png").scaled(24, 24)
        self.setWindowIcon(icon)
        login = QtWidgets.QAction('Login', self)
        tools_menu = menu_bar.addMenu('&Tools')
        kanban_view = QtWidgets.QAction('Kanban View', self)
        self.kanban_menu = two_bar.addAction(kanban_view)
        self.login_menu = two_bar.addAction(login)
        settings = QtWidgets.QAction('Settings', self)
        settings.setShortcut('Ctrl+,')
        shelves = QtWidgets.QAction('Menu Designer', self)
        ingest_dialog = QtWidgets.QAction('Ingest Tool', self)
        # add actions to the file menu
        tools_menu.addAction(settings)
        tools_menu.addAction(shelves)
        tools_menu.addAction(ingest_dialog)
        # connect signals and slots
        settings.triggered.connect(self.on_settings_clicked)
        shelves.triggered.connect(self.on_shelves_clicked)
        login.triggered.connect(self.on_login_clicked)
        kanban_view.triggered.connect(self.on_kanban_clicked)

    def on_kanban_clicked(self):
        print 'Opening up the Kanban View and closing this one'

    def load_user_config(self):
        user_config = UserConfig()
        if 'd' in user_config.__dict__:
            config = user_config.d
            self.user_name = str(config['user_name'])
            self.user_email = str(config['user_email'])
            self.company = str(config['company'])
            try:
                self.previous_path = str(config['previous_path'])
            except KeyError:
                self.previous_path = '%s%s/source' % (app_config()['paths']['root'], self.company)
            if self.user_name in self.previous_path:
                self.filter = 'My Assignments'
            elif 'publish' in self.previous_path:
                self.filter = 'Publishes'
            else:
                self.filter = 'Everything'

    def on_login_clicked(self):
        dialog = LoginDialog(parent=self)
        dialog.exec_()
        self.user_name = dialog.user_name
        self.user_email = dialog.user_email

    def on_settings_clicked(self):
        from apps.configurator.main import Configurator
        dialog = Configurator(self, self.company)
        dialog.exec_()

    def on_shelves_clicked(self):
        from apps.menu_designer.main import MenuDesigner
        dialog = MenuDesigner(self)
        dialog.exec_()

    def closeEvent(self, event):
        user_config = UserConfig(company=self.centralWidget().company,
                                 user_email=self.centralWidget().user_email,
                                 user_name=self.centralWidget().user_name,
                                 current_path=self.centralWidget().path_root)
        print 'Saving Session to -> %s' % user_config.user_config_path
        user_config.update_all()


if __name__ == "__main__":
    from cglui.startup import do_gui_init
    app = do_gui_init()
    td = CGLumberjack()
    td.show()
    td.raise_()
    # setup stylesheet
    app.exec_()
