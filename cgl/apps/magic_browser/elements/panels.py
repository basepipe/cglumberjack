import glob
import os
import logging
from cgl.plugins.Qt import QtCore, QtGui, QtWidgets
from cgl.ui.widgets.widgets import LJButton, LJTableWidget
from cgl.ui.widgets.dialog import InputDialog
from cgl.ui.widgets.containers.model import ListItemModel
from cgl.core.path import PathObject, CreateProductionData
from cgl.ui.widgets.widgets import ProjectWidget, AssetWidget, CreateProjectDialog
from cgl.core.utils.general import current_user, clean_file_list
from cgl.ui.widgets.progress_gif import process_method
from cgl.core.config.config import ProjectConfig, get_root, copy_config, paths


class CompanyPanel(QtWidgets.QWidget):
    location_changed = QtCore.Signal(object)
    user_root = None
    project_management = 'magic_browser'

    def __init__(self, parent=None, path_object=None, search_box=None, cfg=None):
        QtWidgets.QWidget.__init__(self, parent)
        self.path_object = path_object
        if cfg:
            self.cfg = cfg
        else:
            print(CompanyPanel)
            self.cfg = ProjectConfig(self.path_object)
        self.set_stuff_from_globals()
        self.search_box = search_box
        self.panel = QtWidgets.QVBoxLayout(self)
        pixmap = QtGui.QPixmap(self.cfg.icon_path('company24px.png'))
        #self.company_widget = LJListWidget('Companies', pixmap=pixmap, search_box=search_box)
        self.data_table = LJTableWidget(self, path_object=self.path_object)
        self.company_widget.add_button.setText('add company')
        self.company_widget.list.setSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.Expanding)
        self.panel.addWidget(self.company_widget)
        self.panel.addStretch(0)
        self.load_companies()
        self.company_widget.add_button.clicked.connect(self.on_create_company)
        self.company_widget.list.itemDoubleClicked.connect(self.on_company_changed)

    def set_stuff_from_globals(self):
        cfg = ProjectConfig(self.path_object)
        self.user_root = cfg.project_config['cg_lumberjack_dir']
        self.project_management = cfg.project_config['account_info']['project_management']

    def on_company_changed(self):
        self.path_object.set_attr(company=self.company_widget.list.selectedItems()[0].text())
        if self.path_object.company:
            if self.path_object.company != '*':
                self.set_stuff_from_globals()
                self.check_default_company_globals()
        self.update_location()

    def on_create_company(self):
        dialog = InputDialog(title='Create Company', message='Enter the name for the company:', line_edit=True)
        dialog.exec_()

        if dialog.button == 'Ok':
            company = dialog.line_edit.text()
            self.path_object.set_attr(company=company)
            CreateProductionData(self.path_object, project_management='magic_browser')
            self.load_companies()

    def create_company_globals(self, company, proj_management):
        logging.debug('Creating Company Globals %s' % company)
        print('this function must be re-written')
        # dir_ = os.path.join(self.user_root, 'companies', company)
        # if not os.path.exists(dir_):
        #     logging.debug('%s doesnt exist, making it' % dir_)
        #     os.makedirs(dir_)
        #     app_config(company=company, proj_management=proj_management)
            # set the config stuff according to what's up

    def check_default_company_globals(self):
        """
        ensures there are globals directories in the right place, this should really have a popup if it's not
        successful.
        :return:
        """
        self.path_object.set_project_config_paths()
        if self.path_object.company:
            if self.path_object.company != '*':
                dir_ = os.path.dirname(self.path_object.company_config)
                if not os.path.exists(dir_):
                    logging.debug('Creating Directory for Company Config File %s' % dir_)
                    os.makedirs(dir_)

    def load_companies(self):
        self.company_widget.list.clear()
        companies_loc = '%s/*' % self.path_object.root
        companies = glob.glob(companies_loc)
        clean_companies = clean_file_list(companies, self.path_object, cfg=self.cfg)
        if clean_companies:
            for each in companies:
                c = os.path.basename(each)
                self.company_widget.list.addItem(c)

    def clear_layout(self, layout=None):
        clear_layout(self, layout=layout)

    def update_location(self, path_object=None):
        if not path_object:
            path_object = self.path_object
        path_object.set_attr(context='source')
        path_object.set_attr(project='*')
        self.location_changed.emit(path_object.data)


class ProjectPanel(QtWidgets.QWidget):
    location_changed = QtCore.Signal(object)

    def __init__(self, parent=None, path_object=None, search_box=None, title='Projects', cfg=None):
        QtWidgets.QWidget.__init__(self, parent)
        if cfg:
            self.cfg = cfg
        else:
            self.cfg = ProjectConfig(path_object)
        self.path_object = path_object
        self.project_management = self.cfg.project_config['account_info']['project_management']
        self.user_email = self.cfg.project_config['project_management'][self.project_management]['users'][current_user()]
        self.root = paths()['root']  # Company Specific
        self.user_root = self.cfg.cookbook_folder
        self.left_column_visibility = True
        self.title = title
        # Create the Left Panel
        self.panel = QtWidgets.QVBoxLayout(self)
        if title == 'Projects':
            pixmap = QtGui.QPixmap(self.cfg.icon_path('project24px.png'))
        elif title == 'Companies':
            pixmap = QtGui.QPixmap(self.cfg.icon_path('company24px.png'))
        self.project_filter = ProjectWidget(title=title, pixmap=pixmap,
                                            search_box=search_box, path_object=self.path_object, cfg=self.cfg)

        self.panel.addWidget(self.project_filter)
        if title == 'Projects':
            self.load_projects()
        elif title == 'Companies':
            self.load_companies()

        self.project_filter.data_table.doubleClicked.connect(self.on_project_changed)
        self.project_filter.add_button.clicked.connect(self.on_create_project)

    def on_project_changed(self, data):
        data = self.project_filter.data_table.items_
        logging.debug(data)
        if self.title == 'Projects':
            self.path_object.set_attr(project=data[0][0])
            self.path_object.set_attr(scope='*')
            self.update_location(self.path_object)
        elif self.title == 'Companies':
            self.path_object.set_attr(company=data[0][0], context='source', project='*')
            # self.path_object.set_path(bob=True)
            self.update_location(self.path_object)

    def toggle_visibility(self):
        if self.left_column_visibility:
            self.hide()
        else:
            self.show()

    def hide(self):
        self.project_filter.hide_all()
        # project filter
        self.left_column_visibility = False

    def show(self):
        self.project_filter.show_all()

    def load_projects(self):
        self.path_object.set_attr(project='*')
        projects = self.path_object.glob_project_element('project')
        projects = clean_file_list(projects, self.path_object, cfg=self.cfg)
        if not projects:
            logging.debug('no projects for %s' % self.path_object.company)
            self.project_filter.data_table.setEnabled(False)
            self.project_filter.add_button.setText('Create First Project')
        else:
            self.project_filter.data_table.setEnabled(True)
            self.project_filter.add_button.setText('Add Project')
        self.project_filter.setup(ListItemModel(prep_list_for_table(projects,
                                                                    split_for_file=True,
                                                                    size_path=self.path_object.path_root,
                                                                    cfg=self.cfg), ['Name', 'Size']))

        self.update_location(self.path_object)

    def load_companies(self):
        companies_loc = '%s/*' % self.path_object.root
        logging.debug(companies_loc)
        companies = glob.glob(companies_loc)
        clean_companies = []
        for c in companies:
            if '_config' not in c:
                clean_companies.append(c)
        if not clean_companies:
            logging.debug('no companies')
            self.project_filter.data_table.setEnabled(False)
            self.project_filter.add_button.setText('Create First Company')
        else:
            self.project_filter.data_table.setEnabled(True)
            self.project_filter.add_button.setText('Add Company')
        self.project_filter.setup(ListItemModel(prep_list_for_table(clean_companies,
                                                                    split_for_file=True,
                                                                    cfg=self.cfg), ['Name']))
        self.update_location(self.path_object)

    def update_location(self, path_object=None):
        if not path_object:
            path_object = self.path_object
        self.location_changed.emit(path_object.data)

    def on_create_project(self):
        if self.title == 'Projects':
            progress_bar = self.parent().progress_bar
            dialog = CreateProjectDialog(parent=None, company=self.path_object.company, variable='project')
            dialog.exec_()
            if dialog.button == 'Ok':
                project_name = dialog.proj_line_edit.text()
                self.path_object.set_attr(project=project_name)
                production_management = dialog.proj_management_combo.currentText()
                logging.debug(self.path_object.path_root)
                logging.debug(production_management)
                process_method(progress_bar,
                               self.do_create_project,
                               args=(progress_bar, self.path_object, production_management),
                               text='Creating Project')
                self.path_object.set_attr(project='*')
                self.update_location()
        elif self.title == 'Companies':
            dialog = InputDialog(title='Create Company', message='Enter the name for the company:', line_edit=True)
            dialog.exec_()

            if dialog.button == 'Ok':
                company = dialog.line_edit.text()
                self.path_object.set_attr(company=company)
                CreateProductionData(self.path_object, project_management='magic_browser')
                self.load_companies()

    def do_create_project(self, progress_bar, path_object, production_management):
        CreateProductionData(path_object=path_object.path_root, file_system=True,
                             project_management=production_management, cfg=self.cfg)
        logging.debug('setting project management to %s' % production_management)
        progress_bar.hide()

    def clear_layout(self, layout=None):
        clear_layout(self, layout=layout)


class TaskPanel(QtWidgets.QWidget):
    """
    Vertical Button Panel - built to display tasks in a vertical line.  This is essentially the Task Panel
    """
    add_button = QtCore.Signal(object)
    location_changed = QtCore.Signal(object)

    def __init__(self, parent=None, path_object=None, element='task', pixmap=None, cfg=None):
        QtWidgets.QWidget.__init__(self, parent)
        self.element = element
        if path_object:
            self.path_object = path_object
            elements = self.path_object.glob_project_element(element)

        else:
            return
        if cfg:
            self.cfg = cfg
        else:
            self.cfg = ProjectConfig(self.path_object)
        elements = clean_file_list(elements, path_object, self.cfg)
        self.project_management = self.cfg.project_config['account_info']['project_management']
        self.schema = self.cfg.project_config['project_management'][self.project_management]['api']['default_schema']
        schema = self.cfg.project_config['project_management'][self.project_management]['tasks'][self.schema]
        self.proj_man_tasks = schema['long_to_short'][self.path_object.scope]
        self.proj_man_tasks_short_to_long = schema['short_to_long'][self.path_object.scope]
        self.panel = QtWidgets.QVBoxLayout(self)
        self.title_layout = QtWidgets.QHBoxLayout()
        self.task_button = QtWidgets.QToolButton()
        self.task_button.setText('add %s' % element)
        self.task_button.setProperty('class', 'add_button')
        if pixmap:
            self.icon = QtWidgets.QLabel()
            self.icon.setPixmap(pixmap)
            self.h_layout.addWidget(self.icon)
            self.title_layout.addWidget(pixmap)
        self.title = QtWidgets.QLabel('%ss' % element.title())
        self.title.setProperty('class', 'ultra_title')
        self.title_layout.addWidget(self.title)
        self.title_layout.addStretch(1)
        self.title_layout.addWidget(self.task_button)

        self.panel.addLayout(self.title_layout)
        self.task_button.clicked.connect(self.add_button_clicked)
        for each in elements:
            if 'elem' in each:
                task = each
            else:
                try:
                    task = self.proj_man_tasks_short_to_long[each]
                except KeyError:
                    logging.debug('%s not found in short_to_long' % each)
                    task = each
            button = LJButton(str(task))
            # button.setIcon(QtGui.QIcon(QtGui.QPixmap(os.path.join(icon_path(), image_name))))
            # button.setIconSize(QtCore.QSize(50, 50))
            button.setProperty('class', 'ultra_button')
            self.panel.addWidget(button)
            button.clicked.connect(self.on_button_clicked)
        self.panel.addStretch(1)

    def add_button_clicked(self):
        self.add_button.emit(self.path_object)

    def on_button_clicked(self):
        text = self.sender().text()
        if text:
            if 'elem' in text:
                short = text
            else:
                logging.debug(self.proj_man_tasks)
                short = self.proj_man_tasks[text]
            self.path_object.__dict__[self.element] = short
            self.path_object.data[self.element] = short
            self.path_object.set_path()
            self.location_changed.emit(self.path_object)

    def clear_layout(self, layout=None):
        clear_layout(self, layout=layout)


class ScopePanel(QtWidgets.QWidget):
    location_changed = QtCore.Signal(object)

    def __init__(self, parent=None, path_object=None, cfg=None):
        QtWidgets.QWidget.__init__(self, parent)
        if path_object:
            self.path_object = path_object.copy(seq=None, shot=None, ingest_source=None, resolution='', version='',
                                                user=None, scope=None)
        else:
            return
        if cfg:
            self.cfg = cfg
        else:
            print(ScopePanel)
            self.cfg = ProjectConfig(self.path_object)
        self.panel = QtWidgets.QVBoxLayout(self)
        for each in ['assets', 'shots']:
            if each == 'assets':
                image_name = 'flower_80px.png'
            elif each == 'shots':
                image_name = 'shots96px.png'
            elif each == 'my tasks':
                image_name = 'star96px.png'
            else:
                image_name = 'ingest96px.png'
            button = LJButton(str(each))
            button.setIcon(QtGui.QIcon(QtGui.QPixmap(self.cfg.icon_path(image_name))))
            button.setIconSize(QtCore.QSize(50, 50))
            button.setProperty('class', 'ultra_button')
            self.panel.addWidget(button)
            button.clicked.connect(self.on_button_clicked)
        self.panel.addStretch(1)

    def on_button_clicked(self):
        if self.sender().text() == 'ingest':
            self.path_object.set_attr(scope='IO')
        elif self.sender().text() == 'my tasks':
            self.path_object.set_attr(scope='my_tasks', seq='*')
        else:
            scope = self.sender().text()
            self.path_object.set_attr(scope=scope)
            self.path_object.set_attr(seq='*')
        self.location_changed.emit(self.path_object)

    def clear_layout(self, layout=None):
        clear_layout(self, layout=layout)


class ProductionPanel(QtWidgets.QWidget):
    location_changed = QtCore.Signal(object)

    def __init__(self, parent=None, path_object=None, search_box=None, my_tasks=False, cfg=None):
        QtWidgets.QWidget.__init__(self, parent)
        # Create the Middle Panel
        if not cfg:
            print('ProductionPanel')
            self.cfg = ProjectConfig(path_object)
        else:
            self.cfg = cfg
        if path_object:
            self.path_object = path_object.copy(seq='*', shot='*', ingest_source='*', resolution='', version='',
                                                user=None)
        else:
            return
        self.my_tasks = my_tasks
        self.panel = QtWidgets.QVBoxLayout(self)
        self.assets = None
        self.assets_filter_default = filter
        self.root = get_root()
        self.radio_filter = 'Everything'
        self.clear_layout()
        self.assets = AssetWidget(self, title="", path_object=self.path_object, search_box=search_box, cfg=self.cfg)

        self.assets.add_button.show()
        self.set_scope_radio()
        self.panel.addWidget(self.assets)
        self.load_assets()
        self.assets.data_table.selected.connect(self.on_main_asset_selected)
        self.assets.shots_radio.clicked.connect(self.on_filter_radio_changed)
        self.assets.assets_radio.clicked.connect(self.on_filter_radio_changed)
        self.assets.tasks_radio.clicked.connect(self.load_tasks)

    def load_tasks(self):
        # TODO - figure out how to add the progress bar to this.
        self.assets.add_button.setEnabled(False)
        self.assets.data_table.clearSpans()
        data = []
        proj_man = self.cfg.project_config['account_info']['project_management']
        login = self.cfg.project_config['project_management'][proj_man]['users'][current_user()]['login']
        if proj_man == 'ftrack':
            # ideally we load from a .csv file and run this in the background only to update the .csv file.
            from cgl.plugins.project_management.ftrack.main import find_user_assignments
            process_method(self.parent().progress_bar, find_user_assignments, args=(self.path_object, login),
                           text='Finding Your Tasks')
            try:
                company_json = self.cfg.user_config['my_tasks'][self.path_object.company]
            except KeyError:
                logging.debug('Couldnt find company %s in company_json tasks file.' % self.path_object.company)
                self.parent().progress_bar.hide()
                return
            if self.path_object.project in company_json:
                project_tasks = company_json[self.path_object.project]
                if project_tasks:
                    for task in project_tasks:
                        data.append([project_tasks[task]['seq'],
                                     project_tasks[task]['shot_name'],
                                     project_tasks[task]['filepath'],
                                     project_tasks[task]['due_date'],
                                     project_tasks[task]['status'],
                                     project_tasks[task]['task_type']])
                    if data:
                        self.assets.data_table.show()
                        self.assets.search_box.show()
                        self.assets.message.setText('')
                        self.assets.setup(ListItemModel(data, ['Category', 'Name', 'Path', 'Due Date', 'Status', 'Task']))
                        self.assets.data_table.hideColumn(0)
                        self.assets.data_table.hideColumn(2)
                        self.assets.data_table.hideColumn(3)
                    else:
                        self.assets.data_table.hide()
                        self.assets.message.setText('No Tasks for %s Found!' % login)
                        self.assets.message.show()
                    self.parent().progress_bar.hide()
                    return True
                else:
                    logging.debug('No Tasks Assigned for %s' % self.path_object.project)
                    self.parent().progress_bar.hide()
                    return False
            else:
                self.parent().progress_bar.hide()
                return False

    def load_assets(self):
        red_palette = QtGui.QPalette()
        red_palette.setColor(self.foregroundRole(), QtGui.QColor(255, 0, 0))
        self.assets.data_table.clearSpans()
        items = glob.glob(self.path_object.path_root)
        items = clean_file_list(items, self.path_object, cfg=self.cfg)
        data = []
        temp_ = []
        self.assets.add_button.clicked.connect(self.on_create_asset)
        d = None
        if items:
            self.assets.data_table.show()
            self.assets.search_box.show()
            self.assets.message.hide()
            self.assets.message.setText('')
            for each in items:
                obj_ = PathObject(str(each), self.cfg)
                d = obj_.data
                shot_name = '%s_%s' % (d['seq'], d['shot'])
                if shot_name not in temp_:
                    temp_.append(shot_name)
                    if d['scope'] == 'assets':
                        data.append([d['seq'], d['shot'], each, '', '', ''])
                    elif d['scope'] == 'shots':
                        data.append([d['seq'], shot_name, each, '', '', ''])
            if d['scope'] == 'assets':
                self.assets.setup(ListItemModel(data, ['Category', 'Name', 'Path', 'Due Date', 'Status', 'Task']))
            elif d['scope'] == 'shots':
                self.assets.setup(ListItemModel(data, ['Seq', 'Shot', 'Path', 'Due Date', 'Status', 'Task']))
            self.assets.data_table.hideColumn(0)
            self.assets.data_table.hideColumn(2)
            self.assets.data_table.hideColumn(3)
            self.assets.data_table.hideColumn(5)
        else:
            self.assets.data_table.hide()
            self.assets.message.setText('No %s Found! \nClick + button to create %s' % (self.path_object.scope.title(),
                                                                                        self.path_object.scope))
            self.assets.message.setPalette(red_palette)
            self.assets.message.show()

    def on_main_asset_selected(self, data):
        if data:
            path_object = PathObject(data[0][2], self.cfg)
            if not path_object.task:
                path_object.set_attr(task='*')
            else:
                path_object.set_attr(user=None)
            self.update_location(path_object)

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

    def on_create_asset(self):
        from cgl.apps.magic_browser.elements import asset_creator
        if self.path_object.scope == 'assets':
            task_mode = True
        else:
            task_mode = False
        dialog = asset_creator.AssetCreator(self, path_dict=self.path_object.data, task_mode=task_mode, cfg=self.cfg)
        dialog.exec_()
        self.update_location()

    def on_filter_radio_changed(self):
        if self.sender().text() == 'Assets':
            self.assets.add_button.setEnabled(True)
            self.path_object.set_attr(scope='assets')
            self.sender().parent().set_icon('assets')
            self.path_object.data['my_tasks'] = False
        elif self.sender().text() == 'Shots':
            self.assets.add_button.setEnabled(True)
            self.path_object.set_attr(scope='shots')
            self.sender().parent().set_icon('shots')
            self.path_object.data['my_tasks'] = False
        elif self.sender().text() == 'My Tasks':
            self.path_object.data['my_tasks'] = True
        self.update_location(self.path_object)

    def clear_layout(self, layout=None):
        clear_layout(self, layout=layout)


def prep_list_for_table(list_, path_filter=None, split_for_file=False, size_path=False, cfg=None):
    from cgl.core.cgl_info import get_cgl_info_size
    list_.sort()
    output_ = []
    total_size = 0
    render_size = ''
    source_size = ''
    for each in list_:
        if size_path:
            temp_obj = PathObject(size_path, cfg).copy(project=each)
            total_size = get_cgl_info_size(temp_obj.path_root, source=True, render=True)
            source_size = get_cgl_info_size(temp_obj.path_root, source=True, render=False)
            render_size = get_cgl_info_size(temp_obj.path_root, source=False, render=True)
            if not total_size:
                total_size = 'Not Calculated'
            else:
                total_size = total_size
        if path_filter:
            filtered = PathObject(each, cfg).data[path_filter]
            to_append = [filtered]
            if size_path:
                to_append = [filtered, total_size]
            output_.append(to_append)
        else:
            if split_for_file:
                each = os.path.basename(each)
            to_append = [each]
            if size_path:
                to_append = [each, total_size, source_size, render_size]
            output_.append(to_append)
    return output_


def clear_layout(to_clear, layout=None):
    if not layout:
        layout = to_clear.panel
    while layout.count():
        child = layout.takeAt(0)
        if child.widget() is not None:
            child.widget().deleteLater()
        elif child.layout() is not None:
            to_clear.clear_layout(child.layout())

