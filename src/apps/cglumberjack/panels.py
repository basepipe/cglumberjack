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
from widgets import ProjectWidget, AssetWidget, TaskWidget
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
        self.panel = QtWidgets.QVBoxLayout(self)
        self.company_widget = LabelComboRow('Company')
        self.project_filter = ProjectWidget(title="Projects")

        # TODO - set icon with an arrow

        # assemble the Left filter_panel
        self.panel.addLayout(self.company_widget)
        self.panel.addWidget(self.project_filter)

        self.check_default_company_globals()
        self.load_companies()
        if self.company:
            self.load_projects()

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
            if self.current_location['project']:
                self.current_location['scope'] = 'assets'
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

    def clear_layout(self, layout=None):
        if not layout:
            layout = self.panel
        while layout.count():
            child = layout.takeAt(0)
            if child.widget() is not None:
                child.widget().deleteLater()
            elif child.layout() is not None:
                self.clear_layout(child.layout())


class ProjectPanel(QtWidgets.QWidget):
    location_changed = QtCore.Signal(object)

    def __init__(self, parent=None, path_object=None):
        QtWidgets.QWidget.__init__(self, parent)
        # Create the Middle Panel
        if path_object:
            self.path_object = path_object.copy(seq='*', shot='*', input_company='*', resolution='', version='',
                                                user=None)
        else:
            return

        self.panel = QtWidgets.QVBoxLayout(self)
        self.assets = None
        self.assets_filter_default = filter
        self.root = app_config()['paths']['root']
        self.radio_filter = 'Everything'
        self.clear_layout()
        self.assets = AssetWidget(self, title="")

        #self.assets.set_title('<b>%s</b>' % self.path_object.project)
        self.assets.set_scope_title('<b>%s</b>' % self.path_object.scope)
        self.assets.add_button.show()
        self.set_scope_radio()
        self.panel.addWidget(self.assets)
        self.load_assets()
        self.assets.data_table.selected.connect(self.on_main_asset_selected)
        self.assets.shots_radio.clicked.connect(self.on_filter_radio_changed)
        self.assets.assets_radio.clicked.connect(self.on_filter_radio_changed)


    def load_assets(self):
        red_palette = QtGui.QPalette()
        red_palette.setColor(self.foregroundRole(), QtGui.QColor(255, 0, 0))
        self.assets.data_table.clearSpans()
        items = glob.glob(self.path_object.path_root)
        data = []
        temp_ = []
        self.assets.add_button.clicked.connect(self.on_create_asset)
        if items:
            self.assets.data_table.show()
            self.assets.search_box.show()
            self.assets.message.hide()
            #self.assets.radio_publishes.show()
            #self.assets.radio_everything.show()
            #self.assets.radio_user.show()
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
            print 'items is %s' % items
            self.assets.scope_title.hide()
            self.assets.data_table.hide()
            self.assets.search_box.hide()
            self.assets.message.setText('No %s Found! \nClick + button to create %s' % (self.path_object.scope.title(),
                                                                                        self.path_object.scope))
            self.assets.message.setPalette(red_palette)
            self.assets.message.show()

    def on_main_asset_selected(self, data):
        if data:
            p_o = PathObject(data[0][2])
            self.update_location(p_o)

    def update_location(self, path_object=None):
        if path_object:
            self.location_changed.emit(path_object.data)
        else:
            self.path_object.set_attr(seq='*')
            self.location_changed.emit(self.path_object.data)

    def set_scope_radio(self):
        if self.path_object.scope == 'assets':
            self.assets.assets_radio.setChecked(True)
        elif self.path_object.scope == 'shots':
            self.assets.shots_radio.setChecked(True)
        elif self.path_object.scope == '':
            self.path_object.scope.set_attr(scope='assets')
            self.assets.assets_radio.setChecked(True)

    def on_create_asset(self, set_vars=False):
        """
        if self.current_location['scope'] == 'IO':
            dialog = InputDialog(self, title='Create Input Company', message='Enter the CLIENT or name of VENDOR',
                                 combo_box_items=['CLIENT'])
            dialog.exec_()
            self.current_location['input_company'] = dialog.combo_box.currentText()
            input_company_location = PathObject(self.current_location).path_root
            if input_company_location.endswith(dialog.combo_box.currentText()):
                CreateProductionData(self.current_location, json=False)
        else:
        """
        import asset_creator
        if self.path_object.scope == 'assets':
            task_mode = True
        else:
            task_mode = False
        dialog = asset_creator.AssetCreator(self, path_dict=self.path_object.data, task_mode=task_mode)
        dialog.exec_()
        self.update_location()

    def on_file_dragged_to_assets(self, data):
        dialog = AssetIngestor(self, path_dict=self.current_location, current_user=self.user_default)
        dialog.on_files_added(data)
        dialog.exec_()
        self.load_assets()

    def on_filter_radio_changed(self):
        if self.sender().text() == 'Assets':
            self.path_object.set_attr(scope='assets')
        elif self.sender().text() == 'Shots':
            self.path_object.set_attr(scope='shots')
        self.assets.set_scope_title(self.path_object.scope)
        self.update_location(self.path_object)

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
        self.clear_layout(self.panel_tasks)
        self.clear_layout(self.render_layout)
        self.update_location()
        self.load_assets()

    def clear_layout(self, layout=None):
        if not layout:
            layout = self.panel
        while layout.count():
            child = layout.takeAt(0)
            if child.widget() is not None:
                child.widget().deleteLater()
            elif child.layout() is not None:
                self.clear_layout(child.layout())


class IOPanel(QtWidgets.QWidget):
    location_changed = QtCore.Signal(object)

    def __init__(self, parent=None, path_object=None, user_email='', user_name='', render_layout=None):
        QtWidgets.QWidget.__init__(self, parent)
        self.path_object = path_object
        self.render_layout = render_layout
        self.current_location = path_object.data
        self.panel = QtWidgets.QVBoxLayout(self)
        # self.panel.setContentsMargins(0, 10, 0, 0)
        self.panel_tasks = QtWidgets.QVBoxLayout(self)
        # self.panel_tasks.setContentsMargins(0, 0, 0, 0)
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
            self.panel.tasks = []
            self.clear_layout(self.panel)
            task_label = QtWidgets.QLabel('<H2>IO</H2>')
            task_add = QtWidgets.QToolButton()
            task_add.setText('+')
            task_label_layout = QtWidgets.QHBoxLayout()
            # task_label_layout.addWidget(task_label)

            self.panel.addWidget(task_label)
            io_widget = IOWidget(self, 'IN', current)
            self.in_file_tree = io_widget.file_tree
            self.panel.addWidget(io_widget)
            self.panel.addItem((QtWidgets.QSpacerItem(0, 0, QtWidgets.QSizePolicy.Minimum,
                                                      QtWidgets.QSizePolicy.Expanding)))
            self.update_location(path_object=current)
            io_widget.add_button.clicked.connect(self.on_add_ingest)
            io_widget.versions_changed.connect(self.on_ingest_versions_changed)
            io_widget.versions.activated.connect(self.user_entered_versions)
            io_widget.file_tree.selected.connect(self.on_client_file_selected)
            self.populate_ingest_versions(io_widget.versions, current)

    def clear_layout(self, layout=None):
        if not layout:
            layout = self.panel
        while layout.count():
            child = layout.takeAt(0)
            if child.widget() is not None:
                child.widget().deleteLater()
            elif child.layout() is not None:
                self.clear_layout(child.layout())

    def update_location(self, path_object):
        if path_object:
            self.current_location = path_object.data
            self.location_changed.emit(self.current_location)
            return path_object.path_root

    def user_entered_versions(self):
        self.user_changed_versions = True

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
        self.clear_layout(self.panel)
        self.on_main_asset_selected(dir_)

    def populate_ingest_versions(self, combo_box, path_object):
        items = glob.glob('%s/%s' % (path_object.path_root, '*'))
        versions = []
        for each in items:
            versions.append(os.path.split(each)[-1])
        versions = sorted(versions)
        number = len(versions)
        combo_box.addItems(versions)
        combo_box.setCurrentIndex(number - 1)
        self.current_location['version'] = combo_box.currentText()
        self.update_location(path_object=PathObject(self.current_location))
        self.user_changed_versions = True
        self.on_ingest_versions_changed(combo_box.currentText())
        self.user_changed_versions = False

    def on_ingest_versions_changed(self, version):
        if self.user_changed_versions:
            self.current_location['version'] = version
            self.update_location(path_object=PathObject(self.current_location))
            self.in_file_tree.populate(directory=self.path_object.path_root)


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