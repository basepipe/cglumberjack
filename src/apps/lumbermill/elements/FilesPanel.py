import os
import shutil
import logging
import json
import datetime
import glob
from Qt import QtWidgets, QtCore, QtGui
from cglcore.config import app_config
from cglui.widgets.containers.model import ListItemModel
from cglui.widgets.dialog import InputDialog
from cglcore.util import current_user
from cglcore.path import PathObject, CreateProductionData
from cglcore.path import replace_illegal_filename_characters, show_in_folder, seq_from_file, get_frange_from_seq
from cglui.widgets.widgets import AssetWidget, TaskWidget, FileTableModel


class FilesPanel(QtWidgets.QWidget):
    source_selection_changed = QtCore.Signal(object)
    location_changed = QtCore.Signal(object)
    open_signal = QtCore.Signal()
    import_signal = QtCore.Signal()
    new_version_signal = QtCore.Signal()
    review_signal = QtCore.Signal()
    publish_signal = QtCore.Signal()

    def __init__(self, parent=None, path_object=None, user_email='', user_name='', show_import=False, pixmap=False):
        QtWidgets.QWidget.__init__(self, parent)
        # self.setWidgetResizable(True)
        self.work_files = []
        self.high_files = []
        self.render_files = []
        self.version_obj = None
        self.task = path_object.task
        self.task_widgets_dict = {}
        self.show_import = show_import
        self.path_object = path_object
        self.project_management = app_config()['account_info']['project_management']
        self.schema = app_config()['project_management'][self.project_management]['api']['default_schema']
        schema = app_config()['project_management'][self.project_management]['tasks'][self.schema]
        self.proj_man_tasks = schema['long_to_short'][self.path_object.scope]
        self.proj_man_tasks_short_to_long = schema['short_to_long'][self.path_object.scope]

        self.current_location = path_object.data
        self.panel = QtWidgets.QVBoxLayout(self)
        self.tasks = QtWidgets.QHBoxLayout()
        self.in_file_tree = None
        self.user_changed_versions = False
        self.user_email = user_email
        if user_name:
            self.user = user_name
        else:
            self.user = current_user()
        self.project_management = app_config(company=self.path_object.company)['account_info']['project_management']
        self.on_task_selected(self.path_object.data)
        self.panel.addLayout(self.tasks)
        self.panel.addStretch(1)

        self.force_clear = False
        self.auto_publish_tasks = ['plate', 'element']

    def on_task_selected(self, data):
        try:
            current = PathObject(data)
        except IndexError:
            print 'Nothing Selected'
            return
        if data:
            self.clear_layout(self.panel)
            # reset the GUI
            if not current.task:
                current.set_attr(task='*')
            current.set_attr(root=self.path_object.root)
            current.set_attr(user_email=self.user_email)
            self.panel.seq = current.seq
            self.panel.shot = current.shot
            self.update_location(path_object=current)

            self.panel.tasks = []
            try:
                title = self.proj_man_tasks_short_to_long[self.task]
            except KeyError:
                return
            task_widget = TaskWidget(parent=self,
                                     title=title,
                                     path_object=current, show_import=self.show_import)
            task_widget.task = self.task
            task_widget.files_area.export_files_table.hide()
            self.task_widgets_dict[self.task] = task_widget

            # find the version information for the task:
            user = self.populate_users_combo(task_widget, current, self.task)
            version = self.populate_versions_combo(task_widget, current, self.task)
            resolution = self.populate_resolutions_combo(task_widget, current, self.task)
            self.panel.addWidget(task_widget)
            self.panel.tasks.append(self.task)
            self.version_obj = current.copy(task=self.task, user=user, version=version,
                                            resolution=resolution, context='source', filename='*')
            task_widget.files_area.work_files_table.task = self.version_obj.task
            task_widget.files_area.work_files_table.user = self.version_obj.user
            task_widget.files_area.work_files_table.version = self.version_obj.version
            task_widget.files_area.work_files_table.resolution = self.version_obj.resolution

            self.work_files = self.version_obj.glob_project_element('filename', full_path=True)
            # check to see if there are work files for the 'high' version
            self.high_files = self.version_obj.copy(resolution='high').glob_project_element('filename', full_path=True)
            self.render_files = []
            if user != 'publish':
                my_files_label = 'My Work Files'
                if not self.work_files:
                    my_files_label = 'Drag/Drop Work Files'
            else:
                my_files_label = 'Published Work Files'
            logging.debug('Work Files: %s' % self.work_files)
            task_widget.setup(task_widget.files_area.work_files_table,
                              FileTableModel(self.prep_list_for_table(self.work_files, basename=True), [my_files_label]))
            self.load_render_files(task_widget)
            task_widget.create_empty_version.connect(self.new_empty_version_clicked)
            task_widget.files_area.review_button_clicked.connect(self.on_review_clicked)
            task_widget.files_area.publish_button_clicked.connect(self.on_publish_clicked)
            task_widget.copy_latest_version.connect(self.new_version_from_latest)
            task_widget.copy_selected_version.connect(self.version_up_selected_clicked)
            task_widget.files_area.work_files_table.selected.connect(self.on_source_selected)
            task_widget.files_area.export_files_table.selected.connect(self.on_render_selected)
            task_widget.files_area.export_files_table.show_in_folder.connect(self.show_in_folder)
            task_widget.files_area.work_files_table.doubleClicked.connect(self.on_open_clicked)
            task_widget.files_area.open_button.clicked.connect(self.on_open_clicked)
            task_widget.files_area.import_button.clicked.connect(self.on_import_clicked)
            task_widget.versions.currentIndexChanged.connect(self.on_task_info_changed)
            task_widget.users.currentIndexChanged.connect(self.on_task_info_changed)
            task_widget.resolutions.currentIndexChanged.connect(self.on_task_info_changed)
            task_widget.start_task_clicked.connect(self.on_assign_button_clicked)
            task_widget.files_area.work_files_table.dropped.connect(self.on_file_dragged_to_source)
            task_widget.files_area.export_files_table.dropped.connect(self.on_file_dragged_to_render)
            task_widget.files_area.work_files_table.show_in_folder.connect(self.show_in_folder)
            task_widget.files_area.work_files_table.show_in_shotgun.connect(self.show_in_shotgun)
            task_widget.files_area.work_files_table.copy_folder_path.connect(self.copy_folder_path)
            task_widget.files_area.work_files_table.copy_file_path.connect(self.copy_file_path)
            task_widget.files_area.work_files_table.import_version_from.connect(self.import_versions_from)
            task_widget.files_area.work_files_table.push_to_cloud.connect(self.push)
            task_widget.files_area.work_files_table.pull_from_cloud.connect(self.pull)
            task_widget.files_area.work_files_table.share_download_link.connect(self.share_download_link)
            task_widget.empty_state.files_added.connect(self.new_files_dragged)
            if not user:
                task_widget.users_label.hide()
                task_widget.users.hide()
                task_widget.files_area.hide()
                task_widget.versions_label.hide()
                task_widget.versions.hide()
                task_widget.resolutions_label.hide()
                task_widget.resolutions.hide()
                task_widget.empty_state.hide()

    def add_stretch_to_source(self):
        self.panel.addStretch(1)

    def new_files_dragged(self, files):
        data = {}
        to_object = PathObject(self.sender().to_object)
        to_folder = to_object.path_root

        for f in files:
            file_ = os.path.split(f)[-1]
            to_file = os.path.join(to_folder, file_)
            if '.' in file_:
                logging.info('Copying %s to %s' % (f, to_file))
                shutil.copy2(f, to_file)
                CreateProductionData(path_object=to_object)
                self.on_task_selected(self.version_obj)
            else:
                logging.info('Copying directory %s to %s' % (f, to_file))
                shutil.copytree(f, to_file)
                CreateProductionData(path_object=to_object)
                self.on_task_selected(self.version_obj)

    def update_location(self, path_object):
        """
        Method that sends the path object dictionary for anything happening within the Tasks Panel.
        :param path_object:
        :return:
        """
        if path_object:
            self.current_location = path_object.data
            self.path_object = path_object.copy()
            self.location_changed.emit(path_object)

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
            from apps.lumbermill.elements import asset_creator
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
    def populate_versions_combo(task_widget, path_object, task):
        version = path_object.version
        task_widget.versions.show()
        task_widget.versions.clear()
        object_ = path_object.copy(user=task_widget.users.currentText(), task=task, version='*')
        items = object_.glob_project_element('version')
        for each in items:
            task_widget.versions.insertItem(0, each)
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
        items = object_.glob_project_element('resolution')
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
        new_data = []
        object_ = PathObject(self.current_location)
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
        self.update_location(object_)
        for each in data:
            dir_ = os.path.dirname(object_.path_root)
            new_data.append(os.path.join(dir_, each[0]))
        self.source_selection_changed.emit(new_data)
        self.clear_task_selection_except(self.sender().task)
        self.sender().parent().show_tool_buttons(user=object_.user)

    def on_render_selected(self, data):
        if data:
            new_data = []
            object_ = PathObject(self.current_location)
            parent = self.sender().parent()
            object_.set_attr(root=self.path_object.root)
            object_.set_attr(version=parent.parent().versions.currentText())
            object_.set_attr(context='render')
            object_.set_attr(resolution=parent.parent().resolutions.currentText())
            object_.set_attr(user=parent.parent().users.currentText())
            # object_.set_attr(task=self.sender().task)
            try:
                object_.set_attr(filename=data[0][0])
                filename_base, ext = os.path.splitext(data[0][0])
                object_.set_attr(filename_base=filename_base)
                object_.set_attr(ext=ext.replace('.', ''))
            except IndexError:
                # this indicates a selection within the module, but not a specific selected files
                pass
            self.update_location(object_)
            for each in data:
                dir_ = os.path.dirname(object_.path_root)
                new_data.append(os.path.join(dir_, each[0]))
            self.source_selection_changed.emit(new_data)
            # self.clear_task_selection_except(self.sender().task)
            self.sender().parent().show_tool_buttons(user=self.user)
            self.sender().parent().review_button.setEnabled(True)
            self.sender().parent().publish_button.setEnabled(True)
        else:
            logging.debug('No render Files, Drag/Drop them to interface, or create them through software.')

    def new_version_from_latest(self):
        print 'version up_latest'

    def new_empty_version_clicked(self):
        """
        Action when "Empty Version" is clicked
        :return:
        """
        current = PathObject(self.version_obj)
        next_minor = current.new_minor_version_object()
        CreateProductionData(next_minor, create_default_file=True)
        self.on_task_selected(next_minor)

    def version_up_selected_clicked(self):
        current = PathObject(self.current_location)
        # current location needs to have the version in it.
        next_minor = current.new_minor_version_object()
        shutil.copytree(os.path.dirname(current.path_root), os.path.dirname(next_minor.path_root))
        CreateProductionData(next_minor)
        # reselect the original asset.
        self.on_task_selected(current)

    def on_open_clicked(self):
        self.open_signal.emit()

    def on_import_clicked(self):
        self.import_signal.emit()

    def on_review_clicked(self):
        self.review_signal.emit()

    def on_publish_clicked(self):
        self.publish_signal.emit()

    def on_task_info_changed(self):
        """
        This method runs whenever version, user, or resolution is changed in the TaskWidget
        :return:
        """
        files_widget = self.sender().parent().parent()
        version = self.sender().parent().versions.currentText()
        resolution = self.sender().parent().resolutions.currentText()
        user = self.sender().parent().users.currentText()
        self.path_object.set_attr(version=version)
        self.path_object.set_attr(user=user)
        self.path_object.set_attr(resolution=resolution)
        self.current_location = self.path_object.data
        files_widget.on_task_selected(self.path_object.data)

    def on_assign_button_clicked(self, data):
        task = self.sender().task
        dialog = InputDialog(title="%s Task Ownership" % task,
                             combo_box_items=[self.user],
                             message='Who are you assigning this Task?',
                             buttons=['Cancel', 'Start'])
        dialog.exec_()
        if dialog.button == 'Start':
            self.path_object.set_attr(task=task)
            self.path_object.set_attr(user=dialog.combo_box.currentText())
            self.path_object.set_attr(version='000.000')
            self.path_object.set_attr(resolution='high')
            self.path_object.set_attr(shot=data.shot)
            self.path_object.set_attr(seq=data.seq)
            self.path_object.set_attr(filename=None)
            self.path_object.set_attr(ext=None)
            self.path_object.set_attr(filename_base=None)
            self.update_location(self.path_object)

            CreateProductionData(path_object=self.current_location, project_management=self.project_management)
        self.update_location(path_object=self.path_object)

    def show_in_folder(self):
        show_in_folder(self.path_object.path_root)

    def show_in_shotgun(self):
        print 'show in shotgun'

    def copy_folder_path(self):
        clipboard = QtWidgets.QApplication.clipboard()
        clipboard.setText(os.path.dirname(self.path_object.path_root))

    def copy_file_path(self):
        clipboard = QtWidgets.QApplication.clipboard()
        clipboard.setText(self.path_object.path_root)

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
    def on_file_dragged_to_render(self, data):
        logging.debug('Files Dragged to Render %s' % data)
        object_ = PathObject.copy(self.version_obj, context='render')
        self.on_file_dragged(object_, data)

    def on_file_dragged_to_source(self, data):
        object_ = PathObject.copy(self.version_obj, context='source')
        self.on_file_dragged(object_, data)

    def on_file_dragged(self, path_object, data):
        # Only do this if it's dragged into a thing that hasn't been selected
        logging.debug('Path: %s has files added to it' % path_object.path_root)
        if path_object.task in self.auto_publish_tasks:
            dialog = InputDialog(title='Auto-publish files?',
                                 message='Would you like me to publish this %s \n'
                                         'to make it available to other tasks?' % path_object.task,
                                 buttons=['Skip', 'Publish'])
            dialog.exec_()
            if dialog.button == 'Publish':
                print 'Auto Publishing Files'

        self.update_location(path_object)
        self.clear_task_selection_except(path_object.task)
        to_path = path_object.path_root
        if os.path.isfile(to_path):
            to_path = os.path.dirname(to_path)
        elif to_path.endswith('*'):
            to_path = os.path.dirname(to_path)
        for d in data:
            path_, filename_ = os.path.split(d)
            if os.path.isfile(d):
                filename_ = replace_illegal_filename_characters(filename_)
                logging.info('Copying File From %s to %s' % (d, os.path.join(to_path, filename_)))
                shutil.copy2(d, os.path.join(to_path, filename_))
            elif os.path.isdir(d):
                logging.info('Copying Folder From %s to %s' % (d, os.path.join(to_path, filename_)))
                shutil.copytree(d, os.path.join(path_object.path_root, filename_))

        self.on_task_selected(path_object.data)

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
        self.update_location(path_obj)
        list_ = []
        files_ = glob.glob('%s/*' % path_obj.path_root)
        for each in files_:
            list_.append(os.path.basename(each))
        # this is what's doing the loading of the files.
        widget.files_area.clear()
        #widget.setup(widget.files_area.work_files_table, FileTableModel(self.prep_list_for_table(list_), ['Name']))
        #self.on_task_selected(path_obj.data)

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

    def load_render_files(self, widget):
        logging.debug('loading render files')
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
            if not files_:
                render_files_label = 'Drag/Drop Files for Review or Publish'
                widget.files_area.review_button.hide()
                widget.files_area.publish_button.hide()
            logging.debug('Published Files for %s' % current.path_root)
            widget.setup(render_table, ListItemModel(self.prep_list_for_table(files_, basename=True),
                                                     [render_files_label]))
            render_table.show()
            widget.files_area.open_button.show()
            widget.empty_state.hide()

    def clear_layout(self, layout=None):
        if not layout:
            layout = self.panel
        while layout.count():
            child = layout.takeAt(0)
            if child.widget() is not None:
                child.widget().deleteLater()
            elif child.layout() is not None:
                self.clear_layout(child.layout())

    @staticmethod
    def prep_list_for_table(list_, path_filter=None, basename=False):
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
        list_.sort()
        file_count = len(list_)
        output_ = []
        dirname = os.path.dirname(list_[0])
        for each in list_:
            if path_filter:
                filtered = PathObject(each).data[path_filter]
                output_.append([filtered])
            else:
                if basename:

                    seq_string = str(seq_from_file(os.path.basename(each)))
                    if file_count == 1:
                        output_.append([os.path.basename(each)])
                    elif seq_string:
                        if [seq_string] not in output_:
                            output_.append([seq_string])
                    else:
                        output_.append([each])
                else:
                    output_.append([each])
        for each in output_:
            if '#' in each[0]:
                frange = get_frange_from_seq(os.path.join(dirname, each[0]))
                if frange:
                    each[0] = '%s %s' % (each[0], frange)
        return output_
