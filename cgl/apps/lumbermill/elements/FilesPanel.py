import os
import logging
import glob
from cgl.plugins.Qt import QtCore, QtWidgets
from cgl.core.config import app_config
from cgl.ui.widgets.dialog import InputDialog
from cgl.core.utils.general import current_user, cgl_copy, clean_file_list
from cgl.ui.widgets.progress_gif import process_method
from cgl.core.path import PathObject, CreateProductionData, lj_list_dir
from cgl.core.path import replace_illegal_filename_characters, show_in_folder
from cgl.ui.widgets.widgets import AssetWidget, TaskWidget, FileTableModel
from cgl.ui.widgets.containers.model import FilesModel
from cgl.apps.lumbermill.elements.panels import clear_layout

# TODO - this appears to be the main offender when it comes to calling the globals through app_config()

CONFIG = app_config()


class FilesPanel(QtWidgets.QWidget):
    source_selection_changed = QtCore.Signal(object)
    location_changed = QtCore.Signal(object)
    render_location_changed = QtCore.Signal(object)
    open_signal = QtCore.Signal()
    import_signal = QtCore.Signal()
    new_version_signal = QtCore.Signal()
    review_signal = QtCore.Signal()
    publish_signal = QtCore.Signal()

    def __init__(self, parent=None, path_object=None, user_email='', machine_user=None, show_import=False):
        QtWidgets.QWidget.__init__(self, parent)
        # self.setWidgetResizable(True)
        self.work_files = []
        self.in_current_folder = False
        self.render_files_widget = None
        self.high_files = []
        self.render_files = []
        self.version_obj = None
        self.task = path_object.task
        self.task_widgets_dict = {}
        self.show_import = show_import
        self.path_object = path_object
        self.project_management = CONFIG['account_info']['project_management']
        self.schema = CONFIG['project_management'][self.project_management]['api']['default_schema']
        schema = CONFIG['project_management'][self.project_management]['tasks'][self.schema]
        self.user_info = CONFIG['project_management'][self.project_management]['users'][current_user()]
        self.proj_man_tasks = schema['long_to_short'][self.path_object.scope]
        self.proj_man_tasks_short_to_long = schema['short_to_long'][self.path_object.scope]

        self.current_location = path_object.data
        self.panel = QtWidgets.QVBoxLayout(self)
        self.tasks = QtWidgets.QHBoxLayout()
        self.in_file_tree = None
        self.user_changed_versions = False
        self.user_email = user_email
        if machine_user:
            self.user = machine_user
        else:
            self.user = current_user()
        self.project_management = CONFIG['account_info']['project_management']
        self.on_task_selected(self.path_object)
        self.panel.addLayout(self.tasks)
        self.panel.addStretch(1)

        self.force_clear = False
        self.auto_publish_tasks = ['plate', 'element']

    def on_task_selected(self, data):
        try:
            if isinstance(data, PathObject):
                current = data.copy()
            elif isinstance(data, dict):
                'its a dict, this sucks'
                current = PathObject(data)
        except IndexError:
            logging.debug('Nothing Selected')
            return
        if data:
            self.clear_layout(self.panel)
            # reset the GUI
            if not current.task:
                current.set_attr(task='*')
            current.set_attr(root=self.path_object.root)
            # current.set_attr(user_email=self.user_email)
            self.panel.seq = current.seq
            self.panel.shot = current.shot
            self.update_task_location(path_object=current)
            self.panel.tasks = []
            try:
                if 'elem' in self.task:
                    title = self.task
                else:
                    title = self.proj_man_tasks_short_to_long[self.task]
            except KeyError:
                return
            task_widget = TaskWidget(parent=self,
                                     title=title,
                                     path_object=current, show_import=self.show_import)
            task_widget.task = self.task
            self.render_files_widget = task_widget.files_area.export_files_table
            task_widget.files_area.export_files_table.hide()
            self.task_widgets_dict[self.task] = task_widget

            # find the version information for the task:
            user = self.populate_users_combo(task_widget, current, self.task)
            self.current_location['user'] = user
            version = self.populate_versions_combo(task_widget, current, self.task)
            self.current_location['version'] = version
            resolution = self.populate_resolutions_combo(task_widget, current, self.task)
            self.current_location['resolution'] = resolution
            self.update_task_location(self.current_location)
            self.panel.addWidget(task_widget)
            self.panel.tasks.append(self.task)
            self.version_obj = current.copy(task=self.task, user=user, version=version,
                                            resolution=resolution, context='source', filename='*')
            task_widget.files_area.work_files_table.task = self.version_obj.task
            task_widget.files_area.work_files_table.user = self.version_obj.user
            task_widget.files_area.work_files_table.version = self.version_obj.version
            task_widget.files_area.work_files_table.resolution = self.version_obj.resolution
            try:
                self.work_files = self.version_obj.glob_project_element('filename', full_path=True)
                self.high_files = self.version_obj.copy(resolution='high').glob_project_element('filename',
                                                                                                full_path=True)
            except ValueError:
                self.work_files = []
                self.high_files = []
            # check to see if there are work files for the 'high' version
            self.render_files = []
            if user != 'publish':
                my_files_label = 'My Work Files'
                if not self.work_files and not self.render_files:
                    my_files_label = 'Drag/Drop Work Files'
                    task_widget.files_area.work_files_table.hide()
            else:
                my_files_label = 'Published Work Files'
            task_widget.setup(task_widget.files_area.work_files_table,
                              FileTableModel(self.prep_list_for_table(self.work_files, basename=True),
                                             [my_files_label]))
            self.load_render_files(task_widget)
            task_widget.create_empty_version.connect(self.new_empty_version_clicked)
            task_widget.files_area.review_button_clicked.connect(self.on_review_clicked)
            task_widget.files_area.publish_button_clicked.connect(self.on_publish_clicked)
            task_widget.files_area.create_edit_clicked.connect(self.on_create_edit_clicked)
            task_widget.copy_latest_version.connect(self.new_version_from_latest)
            task_widget.copy_selected_version.connect(self.version_up_selected_clicked)
            task_widget.files_area.work_files_table.selected.connect(self.on_source_selected)
            task_widget.files_area.export_files_table.selected.connect(self.on_render_selected)
            task_widget.files_area.export_files_table.double_clicked.connect(self.on_render_double_clicked)
            task_widget.files_area.export_files_table.show_in_folder.connect(self.show_selected_in_folder)
            task_widget.files_area.work_files_table.doubleClicked.connect(self.on_open_clicked)
            task_widget.files_area.open_button.clicked.connect(self.on_open_clicked)
            task_widget.files_area.import_button.clicked.connect(self.on_import_clicked)
            task_widget.versions.currentIndexChanged.connect(self.on_task_info_changed)
            task_widget.users.currentIndexChanged.connect(self.on_task_info_changed)
            task_widget.resolutions.currentIndexChanged.connect(self.on_task_info_changed)
            task_widget.start_task_clicked.connect(self.on_assign_button_clicked)
            task_widget.files_area.work_files_table.dropped.connect(self.on_file_dragged_to_source)
            task_widget.files_area.export_files_table.dropped.connect(self.on_file_dragged_to_render)
            task_widget.files_area.work_files_table.show_in_folder.connect(self.show_selected_in_folder)
            task_widget.files_area.work_files_table.copy_folder_path.connect(self.copy_folder_path)
            task_widget.files_area.work_files_table.copy_file_path.connect(self.copy_file_path)
            task_widget.files_area.work_files_table.import_version_from.connect(self.import_versions_from)
            task_widget.empty_state.files_added.connect(self.on_file_dragged_to_source)
            if not user:
                task_widget.users_label.hide()
                task_widget.users.hide()
                task_widget.files_area.hide()
                task_widget.versions_label.hide()
                task_widget.versions.hide()
                task_widget.resolutions_label.hide()
                task_widget.resolutions.hide()
                task_widget.empty_state.hide()
                task_widget.status_button.hide()
            else:
                if task_widget.users.currentText() == current_user():
                    task_widget.refresh_task_info()
                else:
                    task_widget.status_button.hide()

    def add_stretch_to_source(self):
        self.panel.addStretch(1)

    def new_files_dragged(self, files):
        to_object = PathObject(self.sender().to_object)
        to_folder = to_object.path_root

        for f in files:
            file_ = os.path.split(f)[-1]
            to_file = os.path.join(to_folder, file_)
            if '.' in file_:
                logging.info('Copying %s to %s' % (f, to_file))
                cgl_copy(f, to_file)
                CreateProductionData(path_object=to_object)
                self.on_task_selected(self.version_obj)
            else:
                logging.info('Copying directory %s to %s' % (f, to_file))
                cgl_copy(f, to_file)
                CreateProductionData(path_object=to_object)
                self.on_task_selected(self.version_obj)

    def update_task_location(self, path_object):
        """
        Method that sends the path object dictionary for anything happening within the Tasks Panel.
        :param path_object:
        :return:
        """
        if path_object:
            if isinstance(path_object, dict):
                path_object = PathObject(path_object)
            self.current_location = path_object.data
            self.path_object = path_object.copy()
            self.location_changed.emit(self.path_object)

    def on_create_asset(self):
        if self.current_location['scope'] == 'IO':
            dialog = InputDialog(self, title='Create Input Company', message='Enter the CLIENT or name of VENDOR',
                                 combo_box_items=['CLIENT'])
            dialog.exec_()
            self.current_location['ingest_source'] = dialog.combo_box.currentText()
            ingest_source_location = PathObject(self.current_location).path_root
            if ingest_source_location.endswith(dialog.combo_box.currentText()):
                CreateProductionData(self.current_location, json=False)
        else:
            from cgl.apps.lumbermill.elements import asset_creator
            if 'asset' in self.current_location:
                task_mode = True
            else:
                task_mode = False
            dialog = asset_creator.AssetCreator(self, path_dict=self.current_location, task_mode=task_mode)
            dialog.exec_()

    def populate_users_combo(self, widget, path_object, task):
        if path_object.user:
            self.user = path_object.user
        object_ = path_object.copy(user='*', task=task)
        users = object_.glob_project_element('user')
        for each in users:
            widget.users.addItem(each)
        # self.set_user_from_radio_buttons()
        if self.user == 'publish':
            index_ = widget.users.findText('publish')
            if index_ != -1:
                widget.users.setCurrentIndex(index_)
                self.user = 'publish'
        else:
            index_ = widget.users.findText(self.user)
            if index_ != -1:
                widget.users.setCurrentIndex(index_)
        return widget.users.currentText()

    @staticmethod
    def populate_versions_combo(task_widget, path_object, task, set_to_latest=False):
        version = path_object.version
        task_widget.versions.show()
        task_widget.versions.clear()
        object_ = path_object.copy(user=task_widget.users.currentText(), task=task, version='*')
        try:
            items = object_.glob_project_element('version')
        except ValueError:
            items = ['000.000']
        try:
            latest = items[-1]
        except IndexError:
            latest = '000.000'
        if set_to_latest:
            version = latest
        if not version:
            version = latest
        for each in items:
            task_widget.versions.addItem(each)
        task_widget.versions.setEnabled(True)
        index_ = task_widget.versions.findText(version)
        if index_ != -1:
            task_widget.versions.setCurrentIndex(index_)
        else:
            task_widget.versions.setCurrentIndex(0)
        return task_widget.versions.currentText()

    @staticmethod
    def populate_resolutions_combo(task_widget, path_object, task):
        object_ = path_object.copy(user=task_widget.users.currentText(), task=task,
                                   version=task_widget.versions.currentText(),
                                   resolution='*')
        try:
            items = object_.glob_project_element('resolution')
        except ValueError:
            items = ['high']
        for each in items:
            task_widget.resolutions.addItem(each)
        if path_object.resolution:
            index_ = task_widget.resolutions.findText(path_object.resolution)
        else:
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
        reload_render = False
        new_data = []
        temp_ = PathObject(self.current_location)
        if temp_.resolution:
            if temp_.render_pass:
                reload_render = True
            object_ = PathObject(temp_.split_after('resolution'))
        else:
            object_ = temp_
        parent = self.sender().parent()
        object_.set_attr(root=self.path_object.root)
        object_.set_attr(version=parent.parent().versions.currentText())
        object_.set_attr(context='source')
        object_.set_attr(resolution=parent.parent().resolutions.currentText())
        object_.set_attr(user=parent.parent().users.currentText())
        object_.set_attr(task=self.sender().task)
        try:
            object_.set_attr(filename=data[0][0])
            filename_base, ext = os.path.splitext(data[0][0])
            object_.set_attr(filename_base=filename_base)
            object_.set_attr(ext=ext.replace('.', ''))
        except IndexError:
            # this indicates a selection within the module, but not a specific selected files
            pass
        self.update_task_location(object_)
        for each in data:
            dir_ = os.path.dirname(object_.path_root)
            new_data.append(os.path.join(dir_, each[0]))
        self.source_selection_changed.emit(new_data)
        self.clear_task_selection_except(self.sender().task)
        self.sender().parent().show_tool_buttons(user=object_.user)
        if reload_render:
            self.load_render_files(self.task_widgets_dict[object_.task])

    def on_render_double_clicked(self, data):
        if data:
            self.in_current_folder = False
            selected = data[0][0]
            logging.debug(selected)
            if selected == '.':
                logging.debug('going back a folder')
                last = self.path_object.get_last_attr()
                self.path_object.set_attr(last, None)
                logging.debug(self.path_object.path_root)
                self.update_task_location(self.path_object)
                self.enter_render_folder()
                return
            if os.path.splitext(selected)[1]:
                logging.debug(selected, 'is a file')
            else:
                logging.debug(self.path_object.path_root, 'entering folder')
                self.enter_render_folder()

    @staticmethod
    def get_next_path_object_variable(path_object, current=False):
        if '\\' in path_object.path:
            pieces = path_object.path.split('\\')
        else:
            pieces = path_object.path.split('/')
        if current:
            position = len(pieces)-1
        else:
            position = len(pieces)
        selected_variable = path_object.template[position]
        return selected_variable

    def on_render_selected(self, data):

        if data:
            new_data = []
            if self.current_location['context'] == 'source':
                self.current_location['filename'] = ''
                self.current_location['ext'] = ''
                self.current_location['context'] = 'render'
            object_ = PathObject(self.current_location)
            if not self.in_current_folder:
                current_variable = self.get_next_path_object_variable(object_)
                self.in_current_folder = True
            else:
                current_variable = self.get_next_path_object_variable(object_, current=True)
            logging.debug(current_variable, object_.path_root)
            if current_variable != 'filename':
                if object_.filename:
                    object_.set_attr(filename='')
                    object_.set_attr(ext='')
            new_path_object = PathObject(object_).copy()
            new_path_object.set_attr(attr=current_variable, value=data[0][0])
            object_.set_attr(attr=current_variable, value=data[0][0])
            # object_.set_attr(task=self.sender().task)
            if current_variable == 'filename':
                if os.path.splitext(data[0][0]):
                    object_.set_attr(filename=data[0][0])
                    filename_base, ext = os.path.splitext(data[0][0])
                    object_.set_attr(filename_base=filename_base)
                    object_.set_attr(ext=ext.replace('.', ''))
                else:
                    logging.debug('this is a folder i thought was a file')
            self.update_task_location(new_path_object)
            for each in data:
                dir_ = os.path.dirname(object_.path_root)
                new_data.append(os.path.join(dir_, each[0]))
            self.source_selection_changed.emit(new_data)
            # self.clear_task_selection_except(self.sender().task)
            self.sender().parent().show_tool_buttons(user=self.user)
            self.sender().parent().review_button.setEnabled(True)
            self.sender().parent().publish_button.setEnabled(True)
            self.add_context_menu()
        else:
            logging.debug('No render Files, Drag/Drop them to interface, or create them through software.')

    def add_context_menu(self):
        """

        :return:
        """
        from cgl.core.utils.general import load_json
        from cgl.core.project import get_cgl_tools
        # get the current task
        if self.task and 'elem' not in self.task:
            menu_file = '%s/lumbermill/context-menus.cgl' % get_cgl_tools()
            if os.path.exists(menu_file):
                menu_items = load_json('%s/lumbermill/context-menus.cgl' % get_cgl_tools())
                if self.task in menu_items['lumbermill']:
                    for item in menu_items['lumbermill'][self.task]:
                        if item != 'order':
                            button_label = menu_items['lumbermill'][self.task][item]['label']
                            button_command = menu_items['lumbermill'][self.task][item]['module']
                            module = button_command.split()[1]
                            try:
                                loaded_module = __import__(module, globals(), locals(), item, -1)
                            except ValueError:
                                import importlib
                                # Python 3.0
                                loaded_module = importlib.import_module(module, item)
                            widget = self.render_files_widget
                            if widget.item_right_click_menu.action_exists(button_label):
                                widget.item_right_click_menu.create_action(button_label,
                                                                           lambda: loaded_module.run(self.path_object))

    @staticmethod
    def new_version_from_latest():
        logging.debug('version up_latest')

    def new_empty_version_clicked(self):
        """
        Action when "Empty Version" is clicked
        :return:
        """
        current = PathObject(self.version_obj)
        next_minor = current.new_minor_version_object()
        next_minor.set_attr(filename='')
        next_minor.set_attr(ext='')
        CreateProductionData(next_minor, create_default_file=True)
        self.on_task_selected(next_minor)

    def version_up_selected_clicked(self):
        current = PathObject(self.current_location)
        # current location needs to have the version in it.
        next_minor = current.new_minor_version_object()
        next_minor.set_attr(filename='')
        next_minor.set_attr(resolution=self.current_location['resolution'])
        next_minor.set_attr(ext='')
        CreateProductionData(next_minor)
        cgl_copy(os.path.dirname(current.path_root), next_minor.path_root)
        # reselect the original asset.
        self.on_task_selected(next_minor)

    def on_open_clicked(self):
        self.open_signal.emit()

    def on_import_clicked(self):
        self.import_signal.emit()

    def on_review_clicked(self):
        self.review_signal.emit()

    def on_create_edit_clicked(self):
        from robogary.src.plugins.editorial.timeline import editorial_from_template
        filepath = self.path_object.path_root
        if filepath.endswith('.mp4') and 'audio' not in filepath:
            template_edit = self.path_object.copy(context='source', task='template',
                                                  resolution='high', ext='xml')
            dialog = InputDialog(message="Set a Title and a Secondary Title (not required)",
                                 combo_box_items=['Set Title'],
                                 combo_box2_items=['Set Secondary Title (optional)'],
                                 buttons=['Cancel', 'Ok'])
            dialog.exec_()
            if dialog.button == 'Ok':
                title = dialog.combo_box.currentText()
                secondary = dialog.combo_box2.currentText()
                if secondary == 'Set Secondary Title (optional)':
                    secondary = None
                if not os.path.exists(os.path.dirname(template_edit.path_root)):
                    CreateProductionData(template_edit)
                editorial_from_template(filepath, title, secondary, template_edit.path_root)

    def on_publish_clicked(self):
        # from cgl.plugins.preflight.main import Preflight
        # logging.debug('Publishing stuff now')
        # this = Preflight(self, software='lumbermill',
        #                  preflight=self.current_location['task'],
        #                  path_object=self.current_location)
        # this.show()
        # # check for preflights for that task.
        # return
        current = PathObject(self.current_location)
        if current.task == 'tex':
            from cgl.plugins.maya.tex_util import txmake
            txmake(current.path_root)
        current.publish()
        dialog = InputDialog(title='Publish Successful', message='Publish Files at: \n%s' % current.publish_render)
        dialog.exec_()

    def on_task_info_changed(self):
        """
        This method runs whenever version, user, or resolution is changed in the TaskWidget.
        It essentially refreshes the task window.
        :return:
        """

        version = None
        user = self.sender().parent().users.currentText()
        version = self.sender().parent().versions.currentText()
        resolution = self.sender().parent().resolutions.currentText()
        name = None
        if self.sender().name:
            name = self.sender().name
        if name == 'users':
            self.path_object = self.path_object.copy(user=user, latest=True, resolution='high', render_pass=None,
                                                     camera=None, aov=None, filename=None, context='source')
        elif name == 'versions':
            self.path_object = self.path_object.copy(user=user, version=version, resolution='high', render_pass=None,
                                                     camera=None, aov=None, filename=None, context='source')
        else:
            self.path_object = self.path_object.copy(user=user, version=version, resolution=resolution,
                                                     render_pass=None, camera=None, aov=None, filename=None,
                                                     context='source')
        files_widget = self.sender().parent().parent()
        # self.current_location = self.path_object.data
        files_widget.on_task_selected(self.path_object)

    def on_assign_button_clicked(self, data):
        task = self.sender().task
        users_dict = CONFIG['project_management'][self.project_management]['users']
        all_users = []
        for each in users_dict.keys():
            all_users.append(each.lower())
        dialog = InputDialog(title="%s Task Ownership" % task,
                             combo_box_items=users_dict.keys(),
                             message='Who are you assigning this Task?',
                             buttons=['Cancel', 'Start'])
        index = dialog.combo_box.findText(current_user().lower())
        if index != -1:
            dialog.combo_box.setCurrentIndex(index)
        dialog.exec_()
        if dialog.button == 'Start':
            selected_user = dialog.combo_box.currentText()  # this denotes the OS login name of the user
            user_info = CONFIG['project_management'][self.project_management]['users'][selected_user]
            self.path_object.set_attr(task=task)
            self.path_object.set_attr(user=selected_user)
            self.path_object.set_attr(version='000.000')
            self.path_object.set_attr(resolution='high')
            self.path_object.set_attr(shot=data.shot)
            self.path_object.set_attr(seq=data.seq)
            self.path_object.set_attr(filename=None)
            self.path_object.set_attr(ext=None)
            self.path_object.set_attr(filename_base=None)
            CreateProductionData(path_object=self.path_object,
                                 project_management=self.project_management,
                                 user_login=user_info['login'],
                                 force_pm_creation=True)
        self.update_task_location(path_object=self.path_object)

    def show_selected_in_folder(self):
        show_in_folder(self.path_object.path_root)

    def copy_folder_path(self):
        clipboard = QtWidgets.QApplication.clipboard()
        clipboard.setText(os.path.dirname(self.path_object.path_root))

    def copy_file_path(self):
        clipboard = QtWidgets.QApplication.clipboard()
        clipboard.setText(self.path_object.path_root)

    @staticmethod
    def import_versions_from():
        logging.debug('import versions')

    @staticmethod
    def push():
        logging.debug('push')

    @staticmethod
    def pull():
        logging.debug('pull')

    @staticmethod
    def share_download_link():
        logging.debug('download link')

    # LOAD FUNCTIONS
    def on_file_dragged_to_render(self, data):
        object_ = PathObject.copy(self.version_obj, context='render')
        process_method(self.parent().progress_bar, self.on_file_dragged, args=(object_, data),
                       text='Lumber-hacking Files')
        self.on_task_selected(object_)
        # logging.debug('Files Dragged to Render %s' % data)

    def on_file_dragged_to_source(self, data):
        object_ = PathObject.copy(self.version_obj, context='source')
        process_method(self.parent().progress_bar, self.on_file_dragged, args=(object_, data),
                       text='Lumber-hacking Files')
        self.on_task_selected(object_)

    def on_file_dragged(self, path_object, data):
        logging.debug('Path: %s has files added to it' % path_object.path_root)
        self.update_task_location(path_object)
        self.clear_task_selection_except(path_object.task)
        to_path = path_object.path_root
        if os.path.isfile(to_path):
            to_path = os.path.dirname(to_path)
        elif to_path.endswith('*'):
            to_path = os.path.dirname(to_path)
        for d in data:
            filename_ = os.path.split(d)[-1]
            if os.path.isfile(d):
                filename_ = replace_illegal_filename_characters(filename_)
                logging.info('Copying File From %s to %s' % (d, os.path.join(to_path, filename_)))
                cgl_copy(d, os.path.join(to_path, filename_))
            elif os.path.isdir(d):
                logging.info('Copying Folder From %s to %s' % (d, to_path))
                cgl_copy(d, os.path.join(to_path, filename_))
        self.parent().progress_bar.hide()

    def reload_task_widget(self, widget, path_object=None, populate_versions=True):
        if path_object:
            path_obj = PathObject(path_object)
        else:
            path_obj = PathObject(self.current_location)
        path_obj.set_attr(user=widget.users.currentText())
        if populate_versions:
            path_obj.set_attr(version=self.populate_versions_combo(widget, path_obj, widget.label))
        else:
            path_obj.set_attr(version=widget.versions.currentText())
            path_obj.set_attr(resolution=widget.resolutions.currentText())
        path_obj.set_attr(task=widget.task)
        self.update_task_location(path_obj)
        list_ = []
        files_ = glob.glob('%s/*' % path_obj.path_root)
        for each in files_:
            list_.append(os.path.basename(each))
        # this is what's doing the loading of the files.
        widget.files_area.clear()
        # widget.setup(widget.files_area.work_files_table, FileTableModel(self.prep_list_for_table(list_), ['Name']))
        # self.on_task_selected(path_obj.data)

    def clear_task_selection_except(self, task=None):
        layout = self.panel
        i = -1
        while i <= layout.count():
            i += 1
            child = layout.itemAt(i)
            if child:
                if child.widget():
                    if isinstance(child.widget(), AssetWidget):
                        if task:
                            if task != child.widget().files_area.work_files_table.task:
                                child.widget().hide_tool_buttons()
                                child.widget().files_area.work_files_table.clearSelection()
                        else:
                            child.widget().hide_tool_buttons()
                            child.widget().files_area.work_files_table.clearSelection()
        return

    def enter_render_folder(self, render_path=None):
        """

        :param path_object:
        :return:
        """
        if not render_path:
            glob_path = self.path_object.path_root
        else:
            glob_path = render_path
        files_ = glob.glob('%s/*' % glob_path)
        data_ = self.prep_list_for_table(files_, basename=True, length=1, back=True)
        model = FilesModel(data_, ['Ready to Review/Publish'])
        self.render_files_widget.set_item_model(model)

    def load_render_files(self, widget):
        widget.files_area.work_files_table.show()
        render_table = widget.files_area.export_files_table
        current = PathObject(self.version_obj)
        if widget.files_area.work_files_table.user:
            renders = current.copy(context='render', task=widget.task, user=widget.files_area.work_files_table.user,
                                   version=widget.files_area.work_files_table.version,
                                   resolution=widget.files_area.work_files_table.resolution,
                                   filename='*')
            files_ = glob.glob(renders.path_root)
            if current.user == 'publish':
                render_files_label = 'Published Files'
                widget.files_area.publish_button.hide()
                widget.files_area.new_version_button.hide()
            else:
                widget.files_area.new_version_button.show()
                widget.files_area.review_button.show()
                widget.files_area.publish_button.show()
                render_files_label = 'Ready to Review/Publish'
            logging.debug('Published Files for %s' % current.path_root)
            data_ = self.prep_list_for_table(files_, basename=True, length=1)
            model = FilesModel(data_, [render_files_label])
            widget.setup(render_table, model)  # this is somehow replacing the other table for source when there are no files
            render_table.show()
            widget.files_area.open_button.show()
            widget.empty_state.hide()
            if not files_:
                widget.files_area.review_button.hide()
                widget.files_area.publish_button.hide()
                if not self.work_files:
                    render_table.hide()
                    widget.files_area.open_button.hide()
                    widget.files_area.new_version_button.hide()
                    widget.files_area.work_files_table.hide()
                    widget.empty_state.show()

    def clear_layout(self, layout=None):
        clear_layout(self, layout)

    @staticmethod
    def prep_list_for_table(list_, path_filter=None, basename=False, length=None, back=False):
        """
        Allows us to prepare lists for display in LJTables.
        :param list_: list to put into the table.
        :param path_filter: return a specific element from the path rather than the filename.  For instance if you
        wanted to pull out only the "shot" name you'd use 'shot' as a path filter.
        :param basename: if true we only return the os.path.basename() result of the string.
        :return: list of prepared files/items.
        """
        if not list_:
            return
            # return [['No Files Found']]
        list_.sort()

        output_ = []
        dirname = os.path.dirname(list_[0])
        files = lj_list_dir(dirname, path_filter=path_filter, basename=basename)
        for each in files:
            output_.append([each])
        if back:
            output_.insert(0, '.')
        return output_

