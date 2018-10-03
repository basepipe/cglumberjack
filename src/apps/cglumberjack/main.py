import glob
import copy
import os
from Qt import QtWidgets, QtCore, QtGui
from core.config import app_config
from cglui.widgets.combo import AdvComboBox
from cglui.widgets.base import LJMainWindow
from cglui.widgets.search import LJSearchEdit
from cglui.widgets.containers.table import LJTableWidget
from cglui.widgets.containers.model import ListItemModel
from cglui.widgets.dialog import InputDialog
from core.path import PathObject, CreateProductionData
from asset_ingestor_widget import AssetIngestor


class LabelEditRow(QtWidgets.QVBoxLayout):
    def __init__(self, label):
        QtWidgets.QVBoxLayout.__init__(self)
        self.label = QtWidgets.QLabel("<b>%s</b>" % label)
        self.lineEdit = QtWidgets.QLineEdit()
        self.addWidget(self.label)
        self.addWidget(self.lineEdit)


class LabelComboRow(QtWidgets.QVBoxLayout):
    def __init__(self, label):
        QtWidgets.QVBoxLayout.__init__(self)
        self.label = QtWidgets.QLabel("<b>%s</b>" % label)
        self.add_button = QtWidgets.QToolButton()
        self.add_button.setText('+')
        self.h_layout = QtWidgets.QHBoxLayout()
        self.h_layout.addWidget(self.label)
        self.h_layout.addWidget(self.add_button)
        self.combo = AdvComboBox()
        self.addLayout(self.h_layout)
        self.addWidget(self.combo)
        
    def hide(self):
        self.label.hide()
        self.combo.hide()
        
    def show(self):
        self.label.show()
        self.combo.show()


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


class AssetWidget(QtWidgets.QWidget):
    button_clicked = QtCore.Signal(object)
    filter_changed = QtCore.Signal()
    add_clicked = QtCore.Signal()

    def __init__(self, parent, title, filter_string=None):
        QtWidgets.QWidget.__init__(self, parent)
        v_layout = QtWidgets.QVBoxLayout(self)
        h_layout = QtWidgets.QHBoxLayout(self)
        self.tool_button_layout = QtWidgets.QHBoxLayout(self)
        self.sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.MinimumExpanding)
        self.setSizePolicy(self.sizePolicy)
        self.filter_string = filter_string
        self.label = title
        self.title = QtWidgets.QLabel("<b>%s</b>" % title)

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
        h_layout.addWidget(self.add_button)

        v_layout.addLayout(h_layout)
        v_layout.addWidget(self.message)
        v_layout.addLayout(self.users_layout)
        v_layout.addLayout(self.resolutions_layout)
        v_layout.addWidget(self.data_table, 1)
        v_layout.addLayout(self.tool_button_layout)
        self.hide_combos()

        self.message.hide()
        self.add_button.hide()
        self.hideall()
        self.show_button.clicked.connect(self.on_show_button_clicked)
        self.hide_button.clicked.connect(self.on_hide_button_clicked)
        self.add_button.clicked.connect(self.on_add_button_clicked)
        self.hide_tool_buttons()
        
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

    def set_title(self, new_title):
        self.title.setText('<b>%s</b>' % new_title.title())


class CGLumberjackWidget(QtWidgets.QWidget):
    def __init__(self, parent=None):
        QtWidgets.QWidget.__init__(self, parent)
        # Environment Stuff
        self.do_shotgun = False  # TODO - add this to the globals
        self.root = app_config()['paths']['root']
        self.company = app_config()['account_info']['company']
        self.user_root = app_config()['cg_lumberjack_dir']
        self.context = 'source'
        self.project = '*'
        self.scope = 'assets'
        self.shot = '*'
        self.seq = '*'
        self.user = '*'
        #self.user_default = app_config()['account_info']['user']
        self.user_default = 'PADL_dev'
        self.version = ''
        self.task = ''
        self.resolution = ''
        self.current_location = {}
        self.path_root = ''
        self.path = ''
        layout = QtWidgets.QVBoxLayout(self)
        self.h_layout = QtWidgets.QHBoxLayout(self)

        # Create the Left Panel
        self.filter_layout = QtWidgets.QVBoxLayout(self)
        self.user_widget = LabelComboRow('User')
        self.user_widget.combo.addItem(self.user_default)
        # company
        self.company_widget = LabelComboRow('Company')
        # filters
        self.project_filter = AssetWidget(self, title="Project")
        self.project_filter.showall()
        self.project_filter.add_button.show()
        self.project_filter.hide_button.hide()
        self.radio_label = QtWidgets.QLabel('<b>Filter</b>')
        self.radio_layout = QtWidgets.QHBoxLayout(self)
        self.radio_user = QtWidgets.QRadioButton('User Assignments')
        self.radio_everyone = QtWidgets.QRadioButton('Everything')
        self.radio_publishes = QtWidgets.QRadioButton('Publishes')

        self.radio_layout.addWidget(self.radio_user)
        self.radio_user.setChecked(True)
        self.radio_layout.addWidget(self.radio_publishes)
        self.radio_layout.addWidget(self.radio_everyone)
        self.radio_layout.addItem(QtWidgets.QSpacerItem(340, 0, QtWidgets.QSizePolicy.Maximum,
                                                        QtWidgets.QSizePolicy.Minimum))
        # assemble the filter_panel
        self.filter_layout.addLayout(self.user_widget)
        self.filter_layout.addLayout(self.company_widget)
        self.filter_layout.addWidget(self.radio_label)
        self.filter_layout.addLayout(self.radio_layout)
        self.filter_layout.addWidget(self.project_filter)

        # Create the Middle Panel
        self.middle_layout = QtWidgets.QHBoxLayout()
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

        # assemble the main h layout
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

    # UI interface Functions / Stuff that happens when buttons get clicked/changed.
    def on_company_changed(self):
        print 'combo changed'
        self.company = self.company_widget.combo.currentText()
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
            CreateProductionData(self.current_location)
            self.load_projects()
        else:
            pass

    def on_create_asset(self):
        # This needs to be properly designed, i need to design the create project and create company dialogs as well
        # to ensure that regex is controlling names of shots/sequences/projects/etc....
        # this should be built from the ground up to handle drag/drop asset/shot creation as well.
        import asset_creator
        dialog = asset_creator.AssetCreator(self, path_dict=self.current_location)
        dialog.exec_()

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

    def on_assets_filter_changed(self):
        filter_ = self.assets.resolutions.currentText()
        self.assets_filter_default = filter_
        self.version = ''
        self.resolution = ''
        self.current_location['task'] = '*'
        self.seq = '*'
        self.shot = '*'
        self.task = '*'
        self.user = filter_
        self.clear_layout(self.task_layout)
        self.clear_layout(self.render_layout)
        self.update_location()
        self.load_assets()

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

    def on_project_changed(self, data):
        self.project = data[0][0]
        # reset the env vars after a project change
        self.seq = '*'
        self.shot = '*'
        self.resolution = ''
        self.version = ''
        self.task = '*'
        # build the asset Widget
        self.clear_layout(self.middle_layout)
        self.assets = AssetWidget(self, title="")
        self.assets.set_title('Project: %s' % self.project)
        self.assets.add_button.show()
        self.radio_publishes.clicked.connect(self.on_assets_filter_changed)

        # update location and display the resulting assets.
        self.update_location()
        self.assets.showall()
        self.assets.hide_button.hide()
        self.middle_layout.addWidget(self.assets)

        self.load_assets()
        self.clear_layout(self.task_layout)
        self.clear_layout(self.render_layout)
        self.assets.data_table.selected.connect(self.on_main_asset_selected)
        self.radio_publishes.show()
        self.radio_everyone.show()
        self.radio_user.show()
        self.radio_everyone.toggled.connect(self.on_assets_filter_changed)
        self.radio_publishes.toggled.connect(self.on_assets_filter_changed)
        self.radio_user.toggled.connect(self.on_assets_filter_changed)

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
            path = data[0][1]
            current = PathObject(str(path))
            current.set_attr(attr='task', value='*')
            current.set_attr(attr='root', value=self.root)

            self.update_location(path_object=current)
            # Get the list of tasks for the selection
            task_list = current.glob_project_element('task')
            for task in task_list:
                if '.' not in task:
                    if task not in self.task_layout.tasks:
                        # version_location = copy.copy(self.current_location)
                        task_widget = AssetWidget(self, task)
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

    # LOAD FUNCTIONS

    def reload_task_widget(self, widget, populate_versions=True):
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
        label = QtWidgets.QLabel('<b>%s: Exports</b>' % renders.task)
        render_widget = AssetWidget(self, 'Output')
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
        filter_ = self.get_asset_filter()
        self.user = filter_
        if self.user == '*':
            widget.users.show()
            widget.users_label.show()
        elif self.user == 'publish':
            index_ = widget.users.findText('publish')
            if index_ != -1:
                widget.users.setCurrentIndex(index_)
                self.user = 'publish'
        elif self.user == self.user_widget.combo.currentText():
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
            self.radio_user.setEnabled(False)
            self.radio_everyone.setEnabled(False)
            self.radio_publishes.setEnabled(False)
            self.radio_label.setEnabled(False)
            self.project_filter.add_button.setText('Create First Project')
        else:
            self.project_filter.search_box.setEnabled(True)
            self.project_filter.data_table.setEnabled(True)
            self.project_filter.add_button.setText('+')
            self.radio_user.setEnabled(True)
            self.radio_everyone.setEnabled(True)
            self.radio_publishes.setEnabled(True)
            self.radio_label.setEnabled(True)
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
        self.assets.data_table.clearSpans()
        current = PathObject(self.current_location)
        items = glob.glob(current.path_root)
        data = []
        temp_ = []
        for each in items:
            obj_ = PathObject(str(each))
            d = obj_.data
            shot_name = '%s:%s' % (d['seq'], d['shot'])
            if shot_name not in temp_:
                temp_.append(shot_name)
                data.append([shot_name, each, ''])
        self.assets.setup(ListItemModel(data, ['Name', 'Path', 'Due Date']))
        self.assets.data_table.hideColumn(1)
        self.assets.data_table.set_draggable(True)
        self.assets.data_table.dropped.connect(self.on_file_dragged_to_assets)
        self.assets.add_button.clicked.connect(self.on_create_asset)

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

    def get_asset_filter(self):
        if self.radio_publishes.isChecked():
            filter_ = 'publish'
        elif self.radio_user.isChecked():
            filter_ = self.user_default
        elif self.radio_everyone.isChecked():
            filter_ = '*'
        return filter_

    def update_location(self, path_object=None):
        if path_object:
            self.current_location_line_edit.setText(path_object.path_root)
            self.current_location = path_object.data
            self.path_root = path_object.path_root
            self.path = path_object.path
            return self.path_root
        else:
            self.current_location = {'company': self.company, 'root': self.root, 'scope': self.scope,
                                     'context': self.context, 'project': self.project, 'seq': self.seq, 'shot': self.shot,
                                     'user': self.user, 'version': self.version, 'task': self.task,
                                     'resolution': self.resolution
                                     }
            path_obj = PathObject(self.current_location)
            self.path_root = path_obj.path_root
            print self.path_root
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
        self.setCentralWidget(CGLumberjackWidget(self))
        self.status_bar = QtWidgets.QStatusBar()
        self.setStatusBar(self.status_bar)
        w = 400
        h = 500
        self.resize(w, h)
        menu_bar = self.menuBar()
        icon = QtGui.QPixmap(":images/'lumberjack.24px.png").scaled(24, 24)
        self.setWindowIcon(icon)
        tools_menu = menu_bar.addMenu('&Tools')
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
    td.setWindowTitle('CG Lumberjack')
    td.show()
    td.raise_()
    app.exec_()
