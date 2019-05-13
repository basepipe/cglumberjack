import glob
import os
import shutil
import logging
from Qt import QtWidgets, QtCore, QtGui
from cglcore.config import app_config
from cglui.widgets.combo import LabelComboRow
from cglui.widgets.containers.model import ListItemModel
from cglui.widgets.dialog import InputDialog
from cglcore.path import PathObject, CreateProductionData, start
from cglcore.path import replace_illegal_filename_characters, show_in_folder, create_project_config
from asset_ingestor_widget import AssetIngestor
from widgets import ProjectWidget, AssetWidget, TaskWidget, IOWidget
from apps.project_buddy.widgets import LJButton


class CompanyPanel(QtWidgets.QWidget):
    location_changed = QtCore.Signal(object)

    def __init__(self, parent=None, path_object=None):
        QtWidgets.QWidget.__init__(self, parent)

        self.company = None
        self.project = '*'
        if path_object.company:
            self.company = path_object.company
        if path_object.project:
            self.project = path_object.project
        self.project_management = app_config(company=self.company)['account_info']['project_management']
        self.root = app_config()['paths']['root']  # Company Specific
        self.user_root = app_config()['cg_lumberjack_dir']
        self.path = ''
        self.path_root = ''
        self.scope = ''
        self.context = 'source'
        self.seq = ''
        self.shot = ''
        self.user = ''
        self.version = ''
        self.task = ''
        self.resolution = ''
        self.user_email = ''
        self.current_location = []
        self.left_column_visibility = True

        # Create the Left Panel
        v_layout = QtWidgets.QVBoxLayout()
        self.company_widget = LabelComboRow('Company')
        self.project_filter = ProjectWidget(title="Projects")

        # TODO - set icon with an arrow

        # assemble the Left filter_panel
        v_layout.addLayout(self.company_widget)
        v_layout.addWidget(self.project_filter)
        v_layout.setSpacing(0)
        v_layout.setContentsMargins(0, 10, 0, 0)

        self.check_default_company_globals()
        self.load_companies()
        if self.company:
            self.load_projects()
        self.setLayout(v_layout)

        #self.visibility_button.clicked.connect(self.toggle_visibility)
        self.project_filter.data_table.selected.connect(self.on_project_changed)
        self.company_widget.add_button.clicked.connect(self.on_create_company)
        self.project_filter.add_button.clicked.connect(self.on_create_project)
        self.company_widget.combo.currentIndexChanged.connect(self.on_company_changed)

    def on_project_changed(self, data):
        self.project = data[0][0]
        self.seq = '*'
        self.shot = '*'
        self.update_location()

    def toggle_visibility(self):
        if self.left_column_visibility:
            self.hide()
        else:
            self.show()

    def hide(self):
        # company widget
        self.company_widget.hide()
        self.project_filter.hide_all()
        # project filter
        self.left_column_visibility = False

    def show(self):
        self.company_widget.show()
        self.project_filter.show_all()
        self.left_column_visibility = True

    def check_default_company_globals(self):
        if self.company:
            if not os.path.exists(os.path.join(self.user_root, 'companies', self.company)):
                os.makedirs(os.path.join(self.user_root, 'companies', self.company))

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
        else:
            print 'Companies Dir does not exist %s' % companies_dir
            return

        self.company_widget.combo.addItem('')
        for each in companies:
            c = os.path.split(each)[-1]
            self.company_widget.combo.addItem(c)
        if not company:
            company = self.company
        index = self.company_widget.combo.findText(company)
        if index == -1:
            self.company_widget.combo.setCurrentIndex(0)
        else:
            self.company_widget.combo.setCurrentIndex(index)
        self.update_location()

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
        self.project_filter.setup(ListItemModel(prep_list_for_table(projects, split_for_file=True), ['Name']))
        if self.project != '*':
            self.project_filter.data_table.select_row_by_text(self.project)
            self.on_project_changed(data=[self.project])
        self.update_location()

    def update_location(self, path_object=None):
        if self.company:
            if path_object:
                self.current_location_line_edit.setText(path_object.path_root)
                self.current_location = path_object.data
                self.path_root = path_object.path_root
                self.path = path_object.path
            else:
                self.current_location = {'company': self.company, 'root': self.root, 'scope': self.scope,
                                         'context': self.context, 'project': self.project
                                         }
                path_obj = PathObject(self.current_location)
                self.path_root = path_obj.path_root
                self.path = path_obj.path
                # self.current_location_line_edit.setText(self.path_root)
            self.location_changed.emit(self.current_location)
            return self.path_root

    def on_company_changed(self):
        self.company = self.company_widget.combo.currentText()
        self.project_management = app_config(company=self.company)['account_info']['project_management']
        self.root = app_config()['paths']['root']  # Company Specific
        self.user_root = app_config()['cg_lumberjack_dir']
        self.load_projects()
        self.update_location()

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
        print 'Creating Company Globals %s' % company
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


class ProjectPanel(QtWidgets.QWidget):
    location_changed = QtCore.Signal(object)

    def __init__(self, parent=None, path_object=None):
        QtWidgets.QWidget.__init__(self, parent)
        # Create the Middle Panel
        self.current_location = {}
        if path_object:
            path_object = path_object
            self.current_location = path_object.data
            self.context = path_object.context
            self.company = path_object.company
            if path_object.scope:
                print path_object.scope, '01234'
                self.scope = path_object.scope
            else:
                self.scope = 'assets'
                self.current_location['scope'] = 'assets'
        else:
            self.current_location['scope'] = 'assets'
            self.context = 'source'
            self.scope = 'assets'
            self.company = ''
            self.project = ''
            self.seq = '*'
            self.shot = '*'
        self.panel_center = QtWidgets.QVBoxLayout(self)
        self.assets = None
        self.assets_filter_default = filter
        self.panel_center.setContentsMargins(10, 0, 10, 0)
        self.root = app_config()['paths']['root']

        self.input_company = '*'
        self.resolution = ''
        self.version = ''
        self.task = ''
        self.user = None
        self.radio_filter = 'Everything'
        self.path = ''
        self.path_root = ''
        self.on_project_changed(self.current_location)

    def on_project_changed(self, data):
        self.current_location = data
        # reset the env vars after a project change
        self.project = self.current_location['project']
        if self.project == '*':
            if not self.project:
                return
            return
        self.company = self.current_location['company']
        self.seq = '*'
        self.shot = '*'
        self.input_company = '*'
        self.resolution = ''
        self.version = ''
        self.task = ''
        self.user = None
        self.root = app_config()['paths']['root']
        self.context = 'source'
        # build the asset Widget
        clear_layout(self.panel_center)
        self.assets = AssetWidget(self, title="")
        if not self.radio_filter:
            self.assets.radio_everything.setChecked(True)
        elif self.radio_filter == 'Everything':
            self.assets.radio_everything.setChecked(True)
        elif self.radio_filter == 'My Assignments':
            self.assets.radio_user.setChecked(True)
        elif self.radio_filter == 'Publishes':
            self.assets.radio_publishes.setChecked(True)

        self.assets.set_title('<b>%s</b>' % self.project)
        self.assets.set_scope_title('<b>%s</b>' % self.scope)
        self.assets.add_button.show()
        self.set_scope_radio()

        # update location and display the resulting assets.
        self.update_location()
        self.panel_center.addWidget(self.assets)

        self.load_assets()
        self.assets.data_table.selected.connect(self.on_main_asset_selected)
        self.assets.shots_radio.clicked.connect(self.on_filter_radio_changed)
        self.assets.assets_radio.clicked.connect(self.on_filter_radio_changed)
        self.assets.io_radio.clicked.connect(self.on_filter_radio_changed)
        self.assets.radio_publishes.clicked.connect(self.on_user_radio_changed)
        self.assets.radio_everything.clicked.connect(self.on_user_radio_changed)
        self.assets.radio_user.clicked.connect(self.on_user_radio_changed)

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
                if d['scope'] != 'IO':
                    shot_name = '%s_%s' % (d['seq'], d['shot'])
                else:
                    shot_name = d['input_company']
                if shot_name not in temp_:
                    temp_.append(shot_name)
                    if d['scope'] == 'assets':
                        data.append([d['seq'], d['shot'], each, '', ''])
                    elif d['scope'] == 'shots':
                        data.append([d['seq'], shot_name, each, '', ''])
                    elif d['scope'] == 'IO':
                        data.append(['', shot_name, each, '', ''])
            if d['scope'] == 'assets':
                self.assets.setup(ListItemModel(data, ['Category', 'Name', 'Path', 'Due Date', 'Status']))
                self.assets.data_table.hideColumn(0)
            elif d['scope'] == 'shots':
                self.assets.setup(ListItemModel(data, ['Seq', 'Shot', 'Path', 'Due Date', 'Status']))
                self.assets.data_table.hideColumn(0)
            elif d['scope'] == 'IO':
                self.assets.setup(ListItemModel(data, ['Seq', 'Company', 'Path', 'Latest Ingest', 'Status']))
                self.assets.data_table.hideColumn(0)
                self.assets.data_table.hideColumn(3)
                self.assets.data_table.hideColumn(4)
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

    def on_main_asset_selected(self, data):
        if data:
            p_o = PathObject(data[0][2])
            self.update_location(p_o)

    def update_location(self, path_object=None):
        if self.company:
            if path_object:
                self.current_location = path_object.data
                self.path_root = path_object.path_root
                self.path = path_object.path
            else:
                self.current_location = {'company': self.company, 'root': self.root, 'scope': self.scope,
                                         'context': self.context, 'project': self.project, 'seq': self.seq,
                                         'shot': self.shot
                                         }
                path_obj = PathObject(self.current_location)
                self.path_root = path_obj.path_root
                self.path = path_obj.path
            self.location_changed.emit(self.current_location)
            return self.path_root

    def set_scope_radio(self):
        if self.scope == 'assets':
            self.assets.assets_radio.setChecked(True)
        elif self.scope == 'shots':
            self.assets.shots_radio.setChecked(True)
        elif self.scope == 'IO':
            self.assets.io_radio.setChecked(True)
        elif self.scope == '':
            self.scope = 'assets'
            self.assets.assets_radio.setChecked(True)

    def on_create_asset(self, set_vars=False):
        if self.current_location['scope'] == 'IO':
            dialog = InputDialog(self, title='Create Input Company', message='Enter the CLIENT or name of VENDOR',
                                 combo_box_items=['CLIENT'])
            dialog.exec_()
            self.current_location['input_company'] = dialog.combo_box.currentText()
            input_company_location = PathObject(self.current_location).path_root
            if input_company_location.endswith(dialog.combo_box.currentText()):
                CreateProductionData(self.current_location, json=False)
        else:
            import asset_creator
            if 'asset' in self.current_location:
                task_mode = True
            else:
                task_mode = False
            dialog = asset_creator.AssetCreator(self, path_dict=self.current_location, task_mode=task_mode)
            dialog.exec_()
            self.on_project_changed(self.current_location['project'])

    def on_file_dragged_to_assets(self, data):
        dialog = AssetIngestor(self, path_dict=self.current_location, current_user=self.user_default)
        dialog.on_files_added(data)
        dialog.exec_()
        self.load_assets()

    def on_filter_radio_changed(self):
        if self.sender().text() == 'Assets':
            self.scope = 'assets'
        elif self.sender().text() == 'Shots':
            self.scope = 'shots'
        elif self.sender().text() == 'IO':
            self.scope = 'IO'
            self.input_company = '*'
            self.current_location['input_company'] = '*'
        self.assets.set_scope_title(self.scope)
        self.current_location['scope'] = self.scope
        self.on_project_changed(self.current_location)

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
        self.input_company = '*'
        clear_layout(self.panel_tasks)
        clear_layout(self.render_layout)
        self.update_location()
        self.load_assets()


class TaskPanel(QtWidgets.QWidget):
    location_changed = QtCore.Signal(object)

    def __init__(self, parent=None, path_object=None, user_email='', user_name='', render_layout=None):
        QtWidgets.QWidget.__init__(self, parent)
        self.path_object = path_object
        self.render_layout = render_layout
        self.current_location = path_object.data
        self.panel_tasks = QtWidgets.QVBoxLayout(self)
        self.panel_tasks.setContentsMargins(0, 10, 0, 0)
        self.in_file_tree = None
        self.user_changed_versions = False
        self.user_email = user_email
        self.user = user_name
        self.user_default = self.user
        self.default_user = user_name
        self.project_management = app_config(company=self.path_object.company)['account_info']['project_management']
        self.on_main_asset_selected(self.path_object.data)

    def on_main_asset_selected(self, data):
        try:
            current = PathObject(data)
        except IndexError:
            print 'Nothing Selected'
            return
        if data:
            # reset the GUI
            self.panel_tasks.tasks = []
            clear_layout(self.panel_tasks)
            print current.path_root
            if current.input_company != '*':
                task_label = QtWidgets.QLabel('<H2>IO</H2>')
                task_add = QtWidgets.QToolButton()
                task_add.setText('+')
                task_label_layout = QtWidgets.QHBoxLayout()
                # task_label_layout.addWidget(task_label)

                self.panel_tasks.addWidget(task_label)
                io_widget = IOWidget(self, 'IN', current)
                self.in_file_tree = io_widget.file_tree
                self.panel_tasks.addWidget(io_widget)
                self.panel_tasks.addItem((QtWidgets.QSpacerItem(0, 0, QtWidgets.QSizePolicy.Minimum,
                                                                QtWidgets.QSizePolicy.Expanding)))
                self.update_location(path_object=current)
                io_widget.add_button.clicked.connect(self.on_add_ingest)
                io_widget.versions_changed.connect(self.on_ingest_versions_changed)
                io_widget.versions.activated.connect(self.user_entered_versions)
                io_widget.file_tree.selected.connect(self.on_client_file_selected)
                self.populate_ingest_versions(io_widget.versions, current)

            else:
                task_label = QtWidgets.QLabel('<H2>Tasks</H2>')
                task_add = QtWidgets.QToolButton()
                task_add.setText('+')
                task_label_layout = QtWidgets.QHBoxLayout()
                # task_label_layout.addWidget(task_label)

                self.panel_tasks.addWidget(task_label)
                self.panel_tasks.addItem((QtWidgets.QSpacerItem(0, 32, QtWidgets.QSizePolicy.Minimum,
                                                                QtWidgets.QSizePolicy.Minimum)))
                self.panel_tasks.addLayout(task_label_layout)

                # set our current location
                current.set_attr(task='*')
                current.set_attr(root=self.path_object.root)
                current.set_attr(user_email=self.user_email)
                self.panel_tasks.seq = current.seq
                self.panel_tasks.shot = current.shot
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
                        if task not in self.panel_tasks.tasks:
                            # version_location = copy.copy(self.current_location)
                            try:
                                title = app_config()['pipeline_steps']['short_to_long'][task]
                            except KeyError:
                                return
                            task_widget = TaskWidget(parent=self,
                                                     title=title,
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
                            self.panel_tasks.addWidget(task_widget)
                            self.panel_tasks.tasks.append(task)
                            version_obj = current.copy(task=task, user=user, version=version,
                                                       resolution=resolution, filename='*')
                            task_widget.data_table.task = version_obj.task
                            task_widget.data_table.user = version_obj.user
                            task_widget.data_table.version = version_obj.version
                            task_widget.data_table.resolution = version_obj.resolution
                            files_ = version_obj.glob_project_element('filename')
                            task_widget.setup(ListItemModel(prep_list_for_table(files_, split_for_file=True),
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
                self.panel_tasks.addItem((QtWidgets.QSpacerItem(0, 0, QtWidgets.QSizePolicy.Minimum,
                                                                QtWidgets.QSizePolicy.Expanding)))

    def update_location(self, path_object):
        if path_object:
            self.current_location = path_object.data
            self.location_changed.emit(self.current_location)
            return path_object.path_root

    def on_client_file_selected(self, data):
        files = []
        for each in data:
            path_, filename_ = os.path.split(each)
            files.append(filename_)
        self.sender().parent().clear_all()
        self.sender().parent().show_tags(files=files)
        self.sender().parent().populate_combos()
        self.sender().parent().show_combo_info(data)
        self.sender().parent().show_line_edit_info(data)

    def on_add_ingest(self):
        path_object = PathObject(self.current_location)
        version = path_object.next_major_version_number()
        path_object.set_attr(version=version)
        if not os.path.exists(path_object.path_root):
            print 'Creating Version at: %s' % path_object.path_root
            os.makedirs(path_object.path_root)
        # TODO refresh the thing
        dir_ = os.path.split(path_object.path_root)[0]
        # data = [['', path_object.input_company, dir_, '', '']]
        clear_layout(self.panel_tasks)
        self.on_main_asset_selected(dir_)

    def populate_ingest_versions(self, combo_box, path_object):
        items = glob.glob('%s/%s' % (path_object.path_root, '*'))
        versions = []
        for each in items:
            versions.append(os.path.split(each)[-1])
        versions = sorted(versions)
        number = len(versions)
        combo_box.addItems(versions)
        combo_box.setCurrentIndex(number-1)
        self.current_location['version'] = combo_box.currentText()
        self.update_location(path_object=PathObject(self.current_location))
        self.user_changed_versions = True
        self.on_ingest_versions_changed(combo_box.currentText())
        self.user_changed_versions = False

    def user_entered_versions(self):
        self.user_changed_versions = True

    def on_ingest_versions_changed(self, version):
        if self.user_changed_versions:
            self.current_location['version'] = version
            self.update_location(path_object=PathObject(self.current_location))
            self.in_file_tree.populate(directory=self.path_object.path_root)

    def on_create_asset(self, set_vars=False):
        if self.current_location['scope'] == 'IO':
            dialog = InputDialog(self, title='Create Input Company', message='Enter the CLIENT or name of VENDOR',
                                 combo_box_items=['CLIENT'])
            dialog.exec_()
            self.current_location['input_company'] = dialog.combo_box.currentText()
            input_company_location = PathObject(self.current_location).path_root
            if input_company_location.endswith(dialog.combo_box.currentText()):
                CreateProductionData(self.current_location, json=False)
        else:
            import asset_creator
            if 'asset' in self.current_location:
                task_mode = True
            else:
                task_mode = False
            dialog = asset_creator.AssetCreator(self, path_dict=self.current_location, task_mode=task_mode)
            dialog.exec_()
            self.on_project_changed(self.current_location['project'])

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

        object_ = path_object.copy(user=task_widget.users.currentText(), task=task,
                                   version=task_widget.versions.currentText(),
                                   resolution='*')
        items = object_.glob_project_element('resolution')
        for each in items:
            task_widget.resolutions.addItem(each)
        index_ = task_widget.resolutions.findText('high')
        if index_:
            task_widget.resolutions.setCurrentIndex(index_)
        return task_widget.resolutions.currentText()

    def set_user_from_radio_buttons(self):
        if self.user == self.path_object.user:
            pass
        elif self.path_object.user == 'publish':
            self.user = 'publish'
        elif self.path_object.user == '*':
            self.user = ''

    def on_source_selected(self, data):
        # clear everything
        object_ = PathObject(self.current_location)
        parent = self.sender().parent()
        object_.set_attr(root=self.path_object.root)
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

    def on_new_version_clicked(self):
        current = PathObject(self.current_location)
        next_minor = current.new_minor_version_object()
        shutil.copytree(os.path.dirname(current.path_root), os.path.dirname(next_minor.path_root))
        CreateProductionData(next_minor)
        # reselect the original asset.
        self.on_main_asset_selected(current)

    def on_open_clicked(self):
        if '####' in self.path_root:
            print 'Nothing set for sequences yet'
            # config = app_config()['paths']
            # settings = app_config()['default']
            # cmd = "%s -framerate %s %s" % (config['ffplay'], settings['frame_rate'],
            # self.path_root.replace('####', '%04d'))
            # subprocess.Popen(cmd)
        else:
            start(self.path_root)


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
            #self.task = task
            #self.user = dialog.combo_box.currentText()
            #self.version = '000.000'
            self.path_object.set_attr(task=task)
            self.path_object.set_attr(user=dialog.combo_box.currentText())
            self.path_object.set_attr(version='000.000')
            self.path_object.set_attr(resolution='high')
            #self.resolution = 'high'
            self.path_object.set_attr(shot=data.shot)
            self.path_object.set_attr(seq=data.seq)
            self.update_location(self.path_object)
            print self.current_location
            print self.path_object.path_root
            CreateProductionData(path_object=self.current_location, project_management=self.project_management)
        self.on_main_asset_selected(self.current_location)

    def show_in_folder(self):
        show_in_folder(self.path_root)

    def show_in_shotgun(self):
        CreateProductionData(path_object=self.current_location, file_system=False,
                             do_scope=False, test=False, json=True)

    def copy_folder_path(self):
        clipboard = QtWidgets.QApplication.clipboard()
        clipboard.setText(os.path.dirname(self.path_root))

    def copy_file_path(self):
        clipboard = QtWidgets.QApplication.clipboard()
        clipboard.setText(self.path_root)

    @staticmethod
    def import_versions_from():
        print 'import versions'

    @staticmethod
    def push():
        print 'push'

    @staticmethod
    def pull():
        print 'pull'

    @staticmethod
    def share_download_link():
        print 'download link'

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
        clear_layout(self.render_layout)

    def clear_task_selection_except(self, task=None):
        layout = self.panel_tasks
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

    def load_render_files(self):
        clear_layout(self.render_layout)
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


class IngestPanel(QtWidgets.QVBoxLayout):
    location_changed = QtCore.Signal(object)

    def __init__(self, parent):
        QtWidgets.QWidget.__init__(self, parent)
        pass


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


def clear_layout(layout):
    while layout.count():
        child = layout.takeAt(0)
        if child.widget() is not None:
            child.widget().deleteLater()
        elif child.layout() is not None:
            clear_layout(child.layout())