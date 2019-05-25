import os
import shutil
import logging
import json
import datetime
import glob
from Qt import QtWidgets, QtCore
from cglcore.config import app_config
from cglui.widgets.containers.model import ListItemModel
from cglui.widgets.dialog import InputDialog
from cglcore.path import PathObject, CreateProductionData
from cglcore.path import replace_illegal_filename_characters, show_in_folder, seq_from_file, get_frange_from_seq
from apps.lumbermill.elements.widgets import AssetWidget, TaskWidget, FileTableModel


class TaskPanel(QtWidgets.QWidget):
    source_selection_changed = QtCore.Signal(object)
    location_changed = QtCore.Signal(object)
    open_signal = QtCore.Signal()
    import_signal = QtCore.Signal()
    new_version_signal = QtCore.Signal()

    def __init__(self, parent=None, path_object=None, user_email='', user_name='', show_import=False):
        QtWidgets.QWidget.__init__(self, parent)
        # self.setWidgetResizable(True)
        self.task_widgets_dict = {}
        self.show_import = show_import
        self.path_object = path_object
        self.current_location = path_object.data
        self.panel = QtWidgets.QHBoxLayout(self)
        self.render_layout = QtWidgets.QVBoxLayout()
        self.panel_source = QtWidgets.QVBoxLayout()
        self.panel_title = QtWidgets.QHBoxLayout()
        self.tasks = QtWidgets.QVBoxLayout()
        self.in_file_tree = None
        self.user_changed_versions = False
        self.user_email = user_email
        self.user = user_name
        self.user_default = self.user
        self.default_user = user_name
        self.project_management = app_config(company=self.path_object.company)['account_info']['project_management']
        self.on_main_asset_selected(self.path_object.data)
        self.panel_source.addLayout(self.panel_title)
        self.panel_source.addLayout(self.tasks)
        self.panel_source.addStretch(1)
        self.force_clear = False
        self.panel.addLayout(self.panel_source)
        self.panel.addLayout(self.render_layout)
        self.auto_publish_tasks = ['plate', 'element']

    def on_main_asset_selected(self, data):
        try:
            current = PathObject(data)
        except IndexError:
            print 'Nothing Selected'
            return
        if data:
            # reset the GUI
            self.clear_layout(self.panel_source)
            if self.path_object.scope == 'shots':
                task_label = QtWidgets.QLabel('<H2>%s_%s: Tasks</H2>' % (self.path_object.seq, self.path_object.shot))
            else:
                task_label = QtWidgets.QLabel('<H2>%s: Tasks</H2>' % self.path_object.shot.title())
            self.panel_title.addWidget(task_label)
            task_add = QtWidgets.QToolButton()
            task_add.setText('+')
            if not current.task:
                current.set_attr(task='*')
            current.set_attr(root=self.path_object.root)
            current.set_attr(user_email=self.user_email)
            self.panel_source.seq = current.seq
            self.panel_source.shot = current.shot
            task_add.clicked.connect(self.on_create_asset)
            # Get the list of tasks for the selection
            task_list = current.glob_project_element('task')
            self.update_location(path_object=current)
            self.panel_title.addStretch(1)
            self.panel_source.tasks = []
            for task in task_list:
                if '.' not in task:
                    if task not in self.panel_source.tasks:
                        # version_location = copy.copy(self.current_location)
                        try:
                            title = app_config()['pipeline_steps']['short_to_long'][task]
                        except KeyError:
                            return

                        task_widget = TaskWidget(parent=self,
                                                 title=title,
                                                 path_object=current, show_import=self.show_import)
                        task_widget.task = task
                        task_widget.showall()
                        task_widget.hide_button.hide()
                        task_widget.show_button.show()
                        task_widget.data_table2.hide()
                        self.task_widgets_dict[task] = task_widget

                        # find the version information for the task:
                        user = self.populate_users_combo(task_widget, current, task)
                        version = self.populate_versions_combo(task_widget, current, task)
                        resolution = self.populate_resolutions_combo(task_widget, current, task)
                        self.tasks.addWidget(task_widget)
                        self.panel_source.tasks.append(task)
                        version_obj = current.copy(task=task, user=user, version=version,
                                                   resolution=resolution, filename='*')
                        task_widget.data_table.task = version_obj.task
                        task_widget.data_table.user = version_obj.user
                        task_widget.data_table.version = version_obj.version
                        task_widget.data_table.resolution = version_obj.resolution
                        files_ = version_obj.glob_project_element('filename', full_path=True)
                        if files_:
                            task_widget.my_files_label.show()
                        task_widget.setup(task_widget.data_table,
                                          FileTableModel(self.prep_list_for_table(files_, basename=True), ['Name']))
                        self.load_render_files(task_widget)

                        task_widget.create_empty_version.connect(self.new_empty_version_clicked)
                        task_widget.copy_latest_version.connect(self.new_version_from_latest)
                        task_widget.copy_selected_version.connect(self.version_up_selected_clicked)
                        task_widget.data_table.selected.connect(self.on_source_selected)
                        task_widget.data_table2.selected.connect(self.on_render_selected)
                        task_widget.data_table.doubleClicked.connect(self.on_open_clicked)
                        task_widget.open_button.clicked.connect(self.on_open_clicked)
                        task_widget.import_button.clicked.connect(self.on_import_clicked)
                        task_widget.versions.currentIndexChanged.connect(self.on_task_version_changed)
                        task_widget.users.currentIndexChanged.connect(self.on_task_user_changed)
                        task_widget.resolutions.currentIndexChanged.connect(self.on_task_resolution_changed)
                        task_widget.start_task_clicked.connect(self.on_assign_button_clicked)
                        task_widget.data_table.dropped.connect(self.on_file_dragged_to_source)
                        task_widget.data_table.show_in_folder.connect(self.show_in_folder)
                        task_widget.data_table.show_in_shotgun.connect(self.show_in_shotgun)
                        task_widget.data_table.copy_folder_path.connect(self.copy_folder_path)
                        task_widget.data_table.copy_file_path.connect(self.copy_file_path)
                        task_widget.data_table.import_version_from.connect(self.import_versions_from)
                        task_widget.data_table.push_to_cloud.connect(self.push)
                        task_widget.data_table.pull_from_cloud.connect(self.pull)
                        task_widget.data_table.share_download_link.connect(self.share_download_link)
                        task_widget.empty_state.files_added.connect(self.new_files_dragged)
                        if not user:
                            task_widget.users_label.hide()
                            task_widget.users.hide()
                            task_widget.data_table.hide()
                            task_widget.versions.hide()
                            task_widget.show_button.hide()
                            task_widget.start_task_button.show()
                            task_widget.empty_state.hide()
            self.panel_title.addWidget(task_add)

    def add_stretch_to_source(self):
        self.panel_source.addStretch(1)

    def new_files_dragged(self, files):
        data = {}
        to_object = PathObject(self.sender().to_object)
        to_folder = to_object.path_root
        if to_object.task in self.auto_publish_tasks:
            dialog = InputDialog(title='Auto-Export files?',
                                 message='Would you like me to prepare these files\n'
                                         'for review/publish?' % to_object.task,
                                 buttons=['Skip', 'Publish'])
            dialog.exec_()
            if dialog.button == 'Publish':
                d = datetime.datetime.today()
                current_date = d.strftime('%d-%m-%Y %H:%M:%S')
                data[current_date] = {'files added': files,
                                      'to folder': to_folder}
                path_ = os.path.join(to_object.path_root, 'ingest_record.cgl')
                if os.path.exists(path_):
                    with open(path_) as json_file:
                        data = json.load(json_file)
                data[current_date] = {'files added': files,
                                      'to folder': to_folder}
                with open(path_, 'w') as path_:
                    json.dump(data, path_)

                to_object.set_attr(context='render')
                to_folder = to_object.path_root
                print 'Render folder: %s' % to_folder

        for f in files:
            file_ = os.path.split(f)[-1]
            to_file = os.path.join(to_folder, file_)
            if '.' in file_:
                print 'Copying %s to %s' % (f, to_file)
                shutil.copy2(f, to_file)
                # CreateProductionData(path_object=to_object)
                self.on_main_asset_selected(self.current_location)
            else:
                print 'Copying directory %s to %s' % (f, to_file)
                shutil.copytree(f, to_file)
                # CreateProductionData(path_object=to_object)
                self.on_main_asset_selected(self.current_location)

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
        new_data = []
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
        for each in data:
            dir_ = os.path.dirname(object_.path_root)
            new_data.append(os.path.join(dir_, each[0]))
        self.source_selection_changed.emit(new_data)
        self.clear_task_selection_except(self.sender().task)
        self.sender().parent().show_tool_buttons()

    def on_render_selected(self, data):
        print data
        widget = self.sender().parent()
        print widget
        widget.review_button.setEnabled(True)
        widget.publish_button.setEnabled(True)

    def new_version_from_latest(self):
        print 'version up_latest'

    def new_empty_version_clicked(self):
        print 'new empty version'

    def version_up_selected_clicked(self):
        current = PathObject(self.current_location)
        next_minor = current.new_minor_version_object()
        shutil.copytree(os.path.dirname(current.path_root), os.path.dirname(next_minor.path_root))
        CreateProductionData(next_minor)
        # reselect the original asset.
        self.on_main_asset_selected(current)

    def on_open_clicked(self):
        self.open_signal.emit()

    def on_import_clicked(self):
        self.import_signal.emit()

    def on_task_version_changed(self):
        self.reload_task_widget(self.sender().parent(), populate_versions=False)

    def on_task_user_changed(self):
        self.reload_task_widget(self.sender().parent())

    def on_task_resolution_changed(self):
        print 'resolution changed %s' % self.sender().currentText()

    def on_assign_button_clicked(self, data):
        task = self.sender().task
        dialog = InputDialog(title="%s Task Ownership" % task,
                             combo_box_items=[self.default_user],
                             message='Who is Starting this Task?',
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
        CreateProductionData(path_object=self.current_location, file_system=False,
                             do_scope=False, test=False, json=True)

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
    def on_file_dragged_to_source(self, data):

        # Only do this if it's dragged into a thing that hasn't been selected
        object_ = PathObject(self.current_location)
        if object_.task in self.auto_publish_tasks:
            dialog = InputDialog(title='Auto-publish files?',
                                 message='Would you like me to publish this %s \n'
                                         'to make it available to other tasks?' % object_.task,
                                 buttons=['Skip', 'Publish'])
            dialog.exec_()
            if dialog.button == 'Publish':
                print 'Auto Publishing Files'

        parent = self.sender().parent()
        object_.set_attr(version=parent.versions.currentText())
        object_.set_attr(context='source')
        object_.set_attr(resolution=parent.resolutions.currentText())
        object_.set_attr(user=parent.users.currentText())
        object_.set_attr(task=self.sender().task)
        # object_.set_attr(ext=None)
        self.update_location(object_)
        self.clear_task_selection_except(self.sender().task)
        to_path = object_.path_root
        if os.path.isfile(to_path):
            to_path = os.path.dirname(to_path)
        for d in data:
            path_, filename_ = os.path.split(d)
            if os.path.isfile(d):
                filename_ = replace_illegal_filename_characters(filename_)
                logging.info('Copying File From %s to %s' % (d, os.path.join(to_path, filename_)))
                shutil.copy2(d, os.path.join(to_path, filename_))
            elif os.path.isdir(d):
                logging.info('Copying Folder From %s to %s' % (d, os.path.join(to_path, filename_)))
                shutil.copytree(d, os.path.join(object_.path_root, filename_))

        self.on_main_asset_selected(object_.data)

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
        files_ = path_obj.glob_project_element('filename', full_path=True)
        widget.setup(widget.data_table, ListItemModel(self.prep_list_for_table(files_), ['Name']))
        self.clear_layout(self.render_layout)

    def clear_task_selection_except(self, task=None):
        layout = self.panel_source
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

    def load_render_files(self, widget):
        render_table = widget.data_table2
        self.clear_layout(self.render_layout)
        current = PathObject(self.current_location)
        if widget.data_table.user:
            renders = current.copy(context='render', task=widget.task, user=widget.data_table.user,
                                   version=widget.data_table.version, resolution=widget.data_table.resolution,
                                   filename='*')
            files_ = glob.glob(renders.path_root)
            if files_:
                widget.setup(render_table, ListItemModel(self.prep_list_for_table(files_, basename=True), ['Name']))
                render_table.show()
                widget.open_button.show()
                widget.new_version_button.show()
                widget.export_label.show()
                widget.publish_button.show()
                widget.publish_button.setEnabled(False)
                widget.review_button.show()
                widget.review_button.setEnabled(False)
            else:
                widget.export_label.hide()
                render_table.hide()
                print 'No Published Files for %s' % current.path_root

    def clear_layout(self, layout=None):
        if not layout:
            layout = self.panel_source
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
        output_ = []
        dirname = os.path.dirname(list_[0])
        for each in list_:
            if path_filter:
                filtered = PathObject(each).data[path_filter]
                output_.append([filtered])
            else:
                if basename:
                    seq_string = str(seq_from_file(os.path.basename(each)))
                    if seq_string:
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
