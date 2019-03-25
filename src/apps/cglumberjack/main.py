import glob
import os
from Qt import QtWidgets, QtCore, QtGui
from core.config import app_config
from cglui.widgets.combo import AdvComboBox, LabelComboRow
from cglui.widgets.base import LJMainWindow
from cglui.widgets.search import LJSearchEdit
from cglui.widgets.containers.table import LJTableWidget
from cglui.widgets.containers.model import ListItemModel
from cglui.widgets.dialog import InputDialog, LoginDialog
from core.path import PathObject, CreateProductionData
from asset_ingestor_widget import AssetIngestor


class LabelEditRow(QtWidgets.QVBoxLayout):
    def __init__(self, label):
        QtWidgets.QVBoxLayout.__init__(self)
        self.label = QtWidgets.QLabel("<b>%s</b>" % label)
        self.lineEdit = QtWidgets.QLineEdit()
        self.addWidget(self.label)
        self.addWidget(self.lineEdit)


class FunctionButtons(QtWidgets.QHBoxLayout):
    def __init__(self):
        QtWidgets.QHBoxLayout.__init__(self)
        self.open_button = QtWidgets.QPushButton('Open')
        self.publish_button = QtWidgets.QPushButton('Publish')
        self.review_button = QtWidgets.QPushButton('Review')
        self.version_up = QtWidgets.QPushButton('Version Up')

        self.addWidget(self.open_button)
        self.addWidget(self.version_up)
        self.addWidget(self.review_button)
        self.addWidget(self.publish_button)


class ProjectWidget(QtWidgets.QWidget):
    button_clicked = QtCore.Signal(object)
    filter_changed = QtCore.Signal()
    add_clicked = QtCore.Signal()
    assign_clicked = QtCore.Signal(object)

    def __init__(self, parent, title, filter_string=None, path_object=None):
        QtWidgets.QWidget.__init__(self, parent)
        v_layout = QtWidgets.QVBoxLayout(self)
        h_layout = QtWidgets.QHBoxLayout(self)
        self.path_object = path_object
        self.tool_button_layout = QtWidgets.QHBoxLayout(self)
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
        self.data_table.setMinimumWidth(200)

        # this is where the filter needs to be!
        h_layout.addWidget(self.title)
        h_layout.addWidget(self.add_button)

        v_layout.addLayout(h_layout)
        #v_layout.addWidget(self.message)
        v_layout.addWidget(self.search_box)
        v_layout.addWidget(self.data_table, 1)

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
        v_list = QtWidgets.QVBoxLayout(self)
        h_layout = QtWidgets.QHBoxLayout(self)
        self.path_object = path_object
        self.tool_button_layout = QtWidgets.QHBoxLayout(self)
        self.sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.MinimumExpanding)
        self.setSizePolicy(self.sizePolicy)
        self.filter_string = filter_string
        self.label = title
        self.title = QtWidgets.QLabel("<b>%s</b>" % title)
        self.scope_title = QtWidgets.QLabel("<b>%s</b>" % 'Assets')
        self.task = None
        self.user = None

        self.message = QtWidgets.QLabel("")
        self.search_box = LJSearchEdit(self)
        self.search_box
        self.add_button = QtWidgets.QToolButton()
        self.add_button.setText("+")
        self.data_table = LJTableWidget(self)
        self.data_table.title = title
        self.data_table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.data_table.setMinimumWidth(340)

        # build the filter optoins row
        self.assets_radio = QtWidgets.QRadioButton('Assets')
        self.shots_radio = QtWidgets.QRadioButton('Shots')

        self.radio_layout = QtWidgets.QHBoxLayout()
        # create a button group for these radio buttons
        self.radio_group2 = QtGui.QButtonGroup(self)
        self.radio_user = QtWidgets.QRadioButton('My Assignments')
        self.radio_everything = QtWidgets.QRadioButton('Everything')
        self.radio_publishes = QtWidgets.QRadioButton('Publishes')
        self.radio_group2.addButton(self.radio_user)
        self.radio_group2.addButton(self.radio_everything)
        self.radio_group2.addButton(self.radio_publishes)
        self.radio_layout.addWidget(self.scope_title)
        self.radio_layout.addWidget(self.radio_everything)
        self.radio_layout.addWidget(self.radio_user)
        self.radio_layout.addWidget(self.radio_publishes)

        # this is where the filter needs to be!
        h_layout.addWidget(self.title)
        h_layout.addItem(QtWidgets.QSpacerItem(0, 0, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum))
        h_layout.addWidget(self.shots_radio)
        h_layout.addWidget(self.assets_radio)
        h_layout.addWidget(self.add_button)

        self.v_layout.setSpacing(10)
        v_list.setSpacing(0)
        v_list.addWidget(self.search_box)
        v_list.addWidget(self.data_table, 1)

        self.v_layout.addLayout(h_layout)
        self.v_layout.addWidget(self.message)
        self.v_layout.addLayout(self.radio_layout)
        #self.v_layout.addWidget(self.scope_title)
        self.v_layout.addLayout(v_list)
        #self.v_layout.addStretch(1)

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
        self.title.setText('<b>%s</b>' % new_title.title())

    def set_scope_title(self, new_title):
        self.scope_title.setText('<b>%s</b>' % new_title.title())


class TaskWidget(QtWidgets.QWidget):
    button_clicked = QtCore.Signal(object)
    filter_changed = QtCore.Signal()
    add_clicked = QtCore.Signal()
    assign_clicked = QtCore.Signal(object)

    def __init__(self, parent, title, filter_string=None, path_object=None):
        QtWidgets.QWidget.__init__(self, parent)
        v_layout = QtWidgets.QVBoxLayout(self)
        h_layout = QtWidgets.QHBoxLayout(self)
        self.path_object = path_object
        self.tool_button_layout = QtWidgets.QHBoxLayout(self)
        self.sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.MinimumExpanding)
        self.setSizePolicy(self.sizePolicy)
        self.filter_string = filter_string
        self.label = title
        self.title = QtWidgets.QLabel("<b>%s</b>" % title)
        self.task = None
        self.user = None
        self.versions = AdvComboBox()
        self.versions.setMinimumWidth(500)
        self.versions.hide()

        self.users_label = QtWidgets.QLabel("  User:")
        self.users = AdvComboBox()
        self.users_layout = QtWidgets.QHBoxLayout(self)
        self.users_layout.addWidget(self.users_label)
        self.users_layout.addItem(QtWidgets.QSpacerItem(0, 0, QtWidgets.QSizePolicy.Expanding,
                                                        QtWidgets.QSizePolicy.Minimum))
        self.users_layout.addWidget(self.users)

        self.resolutions = AdvComboBox()
        self.resolutions_layout = QtWidgets.QHBoxLayout(self)
        self.resolutions_label = QtWidgets.QLabel("  Resolution:")
        self.resolutions_layout.addWidget(self.resolutions_label)
        self.resolutions_layout.addItem(QtWidgets.QSpacerItem(0, 0, QtWidgets.QSizePolicy.Expanding,
                                                              QtWidgets.QSizePolicy.Minimum))
        self.resolutions_layout.addWidget(self.resolutions)

        self.message = QtWidgets.QLabel("")
        self.search_box = LJSearchEdit(self)
        self.add_button = QtWidgets.QToolButton()
        self.add_button.setText("+")
        self.show_button = QtWidgets.QToolButton()
        self.show_button.setText("more")
        self.assign_button = QtWidgets.QToolButton()
        self.assign_button.setText("Create Assignment")
        self.hide_button = QtWidgets.QToolButton()
        self.hide_button.setText("less")
        self.data_table = LJTableWidget(self)
        self.data_table.title = title
        self.data_table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.data_table.setMinimumWidth(340)

        # build the tool button row
        self.open_button = QtWidgets.QToolButton()
        self.open_button.setText('Open')
        self.new_version_button = QtWidgets.QToolButton()
        self.new_version_button.setText('New Version')
        self.review_button = QtWidgets.QToolButton()
        self.review_button.setText('Review')
        self.publish_button = QtWidgets.QToolButton()
        self.publish_button.setText('Publish')
        self.tool_button_layout.addWidget(self.open_button)
        self.tool_button_layout.addWidget(self.new_version_button)
        self.tool_button_layout.addWidget(self.review_button)
        self.tool_button_layout.addWidget(self.publish_button)

        # this is where the filter needs to be!
        h_layout.addWidget(self.title)
        h_layout.addWidget(self.versions)
        h_layout.addWidget(self.search_box)
        h_layout.addWidget(self.show_button)
        h_layout.addWidget(self.hide_button)
        h_layout.addWidget(self.assign_button)
        h_layout.addWidget(self.add_button)

        v_layout.addLayout(h_layout)
        v_layout.addWidget(self.message)
        v_layout.addLayout(self.users_layout)
        v_layout.addLayout(self.resolutions_layout)
        v_layout.addWidget(self.data_table, 1)
        v_layout.addLayout(self.tool_button_layout)
        self.hide_combos()

        self.message.hide()
        self.assign_button.hide()
        self.add_button.hide()
        self.hideall()
        self.show_button.clicked.connect(self.on_show_button_clicked)
        self.hide_button.clicked.connect(self.on_hide_button_clicked)
        self.add_button.clicked.connect(self.on_add_button_clicked)
        self.assign_button.clicked.connect(self.on_assign_button_clicked)
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


class CGLumberjackWidget(QtWidgets.QWidget):

    def __init__(self, parent=None, user_name=None, user_email=None, company=None):
        QtWidgets.QWidget.__init__(self, parent)
        # Environment Stuff
        self.user = user_name
        self.default_user = user_name
        self.user_email = user_email
        self.company = company
        self.user_default = self.user
        layout = QtWidgets.QVBoxLayout(self)
        self.h_layout = QtWidgets.QHBoxLayout(self)
        self.project_management = app_config(company=self.company)['account_info']['project_management']  # Company Specific
        self.root = app_config()['paths']['root']  # Company Specific
        self.user_root = app_config()['cg_lumberjack_dir']
        self.user = None
        self.context = 'source'
        self.project = '*'
        self.scope = 'assets'
        self.shot = '*'
        self.seq = '*'
        self.user_favorites = ''
        self.version = ''
        self.task = ''
        self.resolution = ''
        self.current_location = {}
        self.path_root = ''
        self.path = ''

        # Create the Left Panel
        self.filter_layout = QtWidgets.QVBoxLayout(self)
        # company
        self.company_widget = LabelComboRow('Company')
        # filters
        self.project_filter = ProjectWidget(self, title="Projects")

        # assemble the filter_panel
        self.filter_layout.addLayout(self.company_widget)
        self.filter_layout.addWidget(self.project_filter)

        # Create the Middle Panel
        self.middle_layout = QtWidgets.QVBoxLayout()
        self.assets = None
        self.assets_filter_default = 'Everything'

        # Create the Right Panel

        # Create Empty layouts for tasks as well as renders.
        self.task_layout = QtWidgets.QVBoxLayout()
        self.render_layout = QtWidgets.QVBoxLayout()

        # create the current path
        self.current_location_label = QtWidgets.QLabel('Current Location')
        self.current_location_line_edit = QtWidgets.QLineEdit()
        self.current_location_line_edit.setReadOnly(True)
        self.cl_row = QtWidgets.QHBoxLayout()
        self.cl_row.addWidget(self.current_location_label)
        self.cl_row.addWidget(self.current_location_line_edit)

        # assemble the main h layoutQtWidgets.QLabel("<b>%s</b>" % title)
        self.h_layout.addLayout(self.filter_layout)
        self.h_layout.addLayout(self.middle_layout)
        self.h_layout.addLayout(self.task_layout)
        self.h_layout.addLayout(self.render_layout)
        self.h_layout.addItem(QtWidgets.QSpacerItem(0, 0, QtWidgets.QSizePolicy.Expanding,
                                                    QtWidgets.QSizePolicy.Minimum))
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
        if self.render_layout:
            self.clear_layout(self.render_layout)

    def on_create_company(self):
        dialog = InputDialog(title='Create Company', message='Type a Company Name', line_edit=True)
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
        dialog = InputDialog(title='Create Project', message='Type a Project Name', line_edit=True)
        dialog.exec_()
        if dialog.button == 'Ok':
            project_name = dialog.line_edit.text()
            self.project = project_name
            self.update_location()
            CreateProductionData(self.current_location, project_management=self.project_management)
            self.load_projects()
        else:
            pass

    def on_create_asset(self, set_vars=False):
        import asset_creator
        print 'create asset clicked'
        if 'asset' in self.current_location:
            print self.current_location['asset']
            task_mode = True
        else:
            task_mode = False
        dialog = asset_creator.AssetCreator(self, path_dict=self.current_location, task_mode=task_mode)
        dialog.exec_()
        self.load_assets()

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
        task = self.sender().label
        print self.default_user, 'USERR'
        dialog = InputDialog(title="Make an %s Assignment" % task,
                             combo_box_items=['', self.default_user],
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
        self.reload_task_widget(self.sender())

    def on_source_selected(self, data):
        # clear everything
        object_ = PathObject(self.current_location)
        parent = self.sender().parent()
        object_.set_attr(attr='root', value=self.root)
        object_.set_attr(attr='version', value=parent.versions.currentText())
        object_.set_attr(attr='context', value='source')
        object_.set_attr(attr='resolution', value=parent.resolutions.currentText())
        object_.set_attr(attr='user', value=parent.users.currentText())
        object_.set_attr(attr='task', value=self.sender().task)
        try:
            object_.set_attr(attr='filename', value=data[0][0])
        except IndexError:
            # this indicates a selection within the module, but not a specific selected files
            pass
        self.update_location(object_)
        self.clear_task_selection_except(self.sender().task)
        self.sender().parent().show_tool_buttons()
        self.load_render_files()

    def on_render_selected(self, data):
        object_ = PathObject(self.current_location)
        object_.set_attr(attr='root', value=self.root)
        object_.set_attr(attr='context', value='render')
        object_.set_attr(attr='filename', value=data[0][0])
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
        # build the asset Widget
        self.clear_layout(self.middle_layout)
        self.assets = AssetWidget(self, title="")
        self.assets.radio_everything.setChecked(True)
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
            task_label = QtWidgets.QLabel('<b>Tasks</b>')
            task_add = QtWidgets.QToolButton()
            task_add.setText('+')
            task_label_layout = QtWidgets.QHBoxLayout()
            task_label_layout.addWidget(task_label)
            task_label_layout.addWidget(task_add)
            task_label_layout.addItem(QtWidgets.QSpacerItem(0, 0, QtWidgets.QSizePolicy.Minimum,
                                                            QtWidgets.QSizePolicy.Minimum))
            self.task_layout.addLayout(task_label_layout)

            # set our current location
            path = data[0][2]
            current = PathObject(str(path))
            current.set_attr(attr='task', value='*')
            current.set_attr(attr='root', value=self.root)
            current.new_set_attr(user_email=self.user_email)
            self.task_layout.seq = current.seq
            self.task_layout.shot = current.shot
            task_add.clicked.connect(self.on_create_asset)

            self.update_location(path_object=current)
            # Get the list of tasks for the selection
            task_list = current.glob_project_element('task')
            for task in task_list:
                if '.' not in task:
                    if task not in self.task_layout.tasks:
                        # version_location = copy.copy(self.current_location)
                        task_widget = TaskWidget(self, task, path_object=current)
                        task_widget.task = task
                        task_widget.showall()
                        task_widget.search_box.hide()
                        task_widget.hide_button.hide()
                        task_widget.show_button.show()

                        # find the version information for the task:
                        user = self.populate_users_combo(task_widget, current, task)
                        version = self.populate_versions_combo(task_widget, current, task)
                        resolution = self.populate_resolutions_combo(task_widget, current, task)
                        self.task_layout.addWidget(task_widget)
                        self.task_layout.tasks.append(task)
                        self.task_layout.addItem((QtWidgets.QSpacerItem(340, 0, QtWidgets.QSizePolicy.Minimum,
                                                                        QtWidgets.QSizePolicy.Expanding)))
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
                        task_widget.versions.currentIndexChanged.connect(self.on_task_version_changed)
                        task_widget.users.currentIndexChanged.connect(self.on_task_user_changed)
                        task_widget.resolutions.currentIndexChanged.connect(self.on_task_resolution_changed)
                        task_widget.assign_clicked.connect(self.on_assign_button_clicked)
                        if not user:
                            task_widget.users_label.hide()
                            task_widget.users.hide()
                            task_widget.data_table.hide()
                            task_widget.versions.hide()
                            task_widget.show_button.hide()
                            task_widget.assign_button.show()

    # LOAD FUNCTIONS

    def reload_task_widget(self, widget, populate_versions=True):
        # TODO - need to get a really good method written for what is shown when the task widget is reloaded/loaded
        path_obj = PathObject(self.current_location)
        path_obj.set_attr(attr='filename', value='*')
        path_obj.set_attr('user', widget.users.currentText())
        if populate_versions:
            path_obj.set_attr('version', self.populate_versions_combo(widget, path_obj, widget.label))
        else:
            path_obj.set_attr('version', widget.versions.currentText())
            path_obj.set_attr('resolution', widget.resolutions.currentText())
        path_obj.set_attr('task', widget.label)
        self.update_location(path_obj)
        files_ = path_obj.glob_project_element('filename')
        widget.setup(ListItemModel(self.prep_list_for_table(files_), ['Name']))
        self.clear_layout(self.render_layout)

    def load_render_files(self):
        self.clear_layout(self.render_layout)
        current = PathObject(self.current_location)
        renders = current.copy(context='render', filename='*')
        files_ = renders.glob_project_element('filename')
        label = QtWidgets.QLabel('<b>%s: Published Files</b>' % renders.task)
        render_widget = TaskWidget(self, 'Output')
        render_widget.showall()
        render_widget.title.hide()
        render_widget.search_box.hide()
        render_widget.hide_button.hide()
        self.render_layout.addWidget(label)
        self.render_layout.addWidget(render_widget)
        self.render_layout.addItem((QtWidgets.QSpacerItem(340, 0, QtWidgets.QSizePolicy.Minimum,
                                                          QtWidgets.QSizePolicy.Expanding)))
        render_widget.setup(ListItemModel(self.prep_list_for_table(files_, split_for_file=True), ['Name']))
        render_widget.data_table.selected.connect(self.on_render_selected)

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
        self.update_location()

    def load_companies(self, company=None):
        self.company_widget.combo.clear()
        companies_dir = os.path.join(self.user_root, 'companies')
        if os.path.exists(companies_dir):
            companies = os.listdir(companies_dir)
            print 'Companies: %s' % companies
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
                shot_name = '%s:%s' % (d['seq'], d['shot'])
                if shot_name not in temp_:
                    temp_.append(shot_name)
                    data.append([d['shot'], d['seq'], each, ''])
            self.assets.setup(ListItemModel(data, ['Name', 'Category', 'Path', 'Due Date']))
            self.assets.data_table.hideColumn(1)
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
            print 'Setting path as: ', self.path_root
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
        self.load_user_config()
        if not self.user_name:
            self.on_login_clicked()
        self.setCentralWidget(CGLumberjackWidget(self, user_email=self.user_email,
                                                 user_name=self.user_name,
                                                 company=self.company))
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
        self.login_menu = two_bar.addAction(login)
        settings = QtWidgets.QAction('Settings', self)
        settings.setShortcut('Ctrl+,')
        shelves = QtWidgets.QAction('Shelf Builder', self)
        ingest_dialog = QtWidgets.QAction('Ingest Tool', self)
        # add actions to the file menu
        tools_menu.addAction(settings)
        tools_menu.addAction(shelves)
        tools_menu.addAction(ingest_dialog)
        # connect signals and slots
        settings.triggered.connect(self.on_settings_clicked)
        shelves.triggered.connect(self.on_shelves_clicked)
        login.triggered.connect(self.on_login_clicked)

    def load_user_config(self):
        dialog = LoginDialog(parent=self)
        self.user_name = dialog.user_name
        self.user_email = dialog.user_email
        self.company = dialog.company
        dialog.close()

    def on_login_clicked(self):
        dialog = LoginDialog(parent=self)
        dialog.exec_()
        self.user_name = dialog.user_name
        self.user_email = dialog.user_email

    def on_settings_clicked(self):
        from apps.configurator.main import Configurator
        dialog = Configurator(self)
        dialog.exec_()

    def on_shelves_clicked(self):
        from apps.shelf_tool.main import ShelfTool
        dialog = ShelfTool(self)
        dialog.exec_()


if __name__ == "__main__":
    from cglui.startup import do_gui_init
    app = do_gui_init()
    td = CGLumberjack()
    td.show()
    td.raise_()
    # setup stylesheet
    app.exec_()
