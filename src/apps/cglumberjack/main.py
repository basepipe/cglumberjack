import glob
import os
import shutil
import logging
from Qt import QtWidgets, QtCore, QtGui
from cglcore.config import app_config, UserConfig
from cglui.widgets.combo import LabelComboRow
from cglui.widgets.base import LJMainWindow
from cglui.widgets.containers.model import ListItemModel
from cglui.widgets.dialog import InputDialog, LoginDialog
from cglcore.path import PathObject, CreateProductionData, start
from cglcore.path import replace_illegal_filename_characters, show_in_folder, create_project_config
from asset_ingestor_widget import AssetIngestor
from widgets import IOWidget, TaskWidget, ProjectWidget, AssetWidget
from panels import CompanyPanel, ProjectPanel, TaskPanel, IngestPanel


class PathWidget(QtWidgets.QWidget):
    def __init__(self, parent=None, path=None):
        QtWidgets.QWidget.__init__(self, parent)
        self.current_location_label = QtWidgets.QLabel('Current Location')
        self.current_location_line_edit = QtWidgets.QLineEdit()
        self.current_location_line_edit.setReadOnly(True)
        self.cl_row = QtWidgets.QHBoxLayout(self)
        self.cl_row.addWidget(self.current_location_label)
        self.cl_row.addWidget(self.current_location_line_edit)
        if path:
            self.set_text(path)

    def set_text(self, text):
        self.current_location_line_edit.setText(text)


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
        self.project_management = app_config(company=self.company)['account_info']['project_management']
        self.root = app_config()['paths']['root']  # Company Specific
        self.user_root = app_config()['cg_lumberjack_dir']
        self.user = None
        self.context = 'source'
        self.initial_path_object = None
        self.radio_filter = radio_filter
        self.user_changed_versions = False

        layout = QtWidgets.QVBoxLayout(self)
        self.h_layout = QtWidgets.QHBoxLayout()
        if path:
            try:
                self.initial_path_object = PathObject(path)
            except IndexError:
                pass
        self.project = '*'
        self.scope = 'assets'
        self.shot = '*'
        self.seq = '*'
        self.input_company = '*'
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
        self.in_file_tree = None

        self.path_widget = PathWidget(path=self.initial_path_object.path_root)
        self.panel_left = CompanyPanel(path_object=self.initial_path_object)
        self.panel_left.location_changed.connect(self.update_location2)

        self.panel_center = ProjectPanel(path_object=self.initial_path_object)
        self.panel_left.location_changed.connect(self.panel_center.on_project_changed)
        self.panel_center.location_changed.connect(self.update_location2)

        # Create Empty layouts for tasks as well as renders.
        self.panel_tasks = QtWidgets.QVBoxLayout()
        self.panel_tasks.setContentsMargins(0, 10, 0, 0)
        self.render_layout = QtWidgets.QVBoxLayout()

        self.h_layout.addWidget(self.panel_left)
        self.h_layout.addWidget(self.panel_center)
        self.h_layout.addLayout(self.panel_tasks)
        self.h_layout.addLayout(self.render_layout)

        self.h_layout.addStretch()
        self.h_layout.setSpacing(0)
        layout.addWidget(self.path_widget)
        layout.addLayout(self.h_layout)

    def update_location2(self, data):
        self.current_location = data
        path_object = PathObject(data)
        self.path_root = str(path_object.path_root)
        self.path_widget.set_text(path_object.path_root)

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

    def on_main_asset_selected(self, data):
        # data format: ['Project', 'Seq', 'Shot', 'Task', 'User', 'Path']
        try:
            current = PathObject(data[0][2])
        except IndexError:
            print 'Nothing Selected'
            return
        if data:
            # reset the GUI
            self.panel_tasks.tasks = []
            self.clear_layout(self.panel_tasks)
            self.clear_layout(self.render_layout)
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
                current.set_attr(root=self.root)
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
                            self.panel_tasks.addWidget(task_widget)
                            self.panel_tasks.tasks.append(task)
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
                self.panel_tasks.addItem((QtWidgets.QSpacerItem(0, 0, QtWidgets.QSizePolicy.Minimum,
                                                                QtWidgets.QSizePolicy.Expanding)))

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
        data = [['', path_object.input_company, dir_, '', '']]
        self.clear_layout(self.panel_tasks)
        self.on_main_asset_selected(data)

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
            # cmd = "%s -framerate %s %s" % (config['ffplay'], settings['frame_rate'],
            # self.path_root.replace('####', '%04d'))
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
            self.in_file_tree.populate(directory=self.path_root)

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

    # CLEAR/DELETE FUNCTIONS

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
        print self.centralWidget().path_root, ' this'
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
