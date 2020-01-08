import glob
import os
from PySide import QtCore, QtGui
from cgl.core.config import app_config
from cgl.ui.widgets.widgets import LJListWidget, LJButton
from cgl.ui.widgets.dialog import InputDialog
from cgl.ui.widgets.containers.model import ListItemModel
from cgl.core.path import PathObject, CreateProductionData, icon_path
from cgl.core.project import create_project_config
from cgl.ui.widgets.widgets import ProjectWidget, AssetWidget, CreateProjectDialog
from cgl.core.util import current_user
from cgl.ui.widgets.progress_gif import process_method


class CompanyPanel(QtGui.QWidget):
    location_changed = QtCore.Signal(object)

    def __init__(self, parent=None, path_object=None, search_box=None):
        QtGui.QWidget.__init__(self, parent)
        self.search_box = search_box
        self.path_object = path_object
        self.panel = QtGui.QVBoxLayout(self)
        pixmap = QtGui.QPixmap(icon_path('company24px.png'))
        self.company_widget = LJListWidget('Companies', pixmap=pixmap)
        self.company_widget.add_button.setText('add company')
        self.company_widget.list.setSizePolicy(QtGui.QSizePolicy.MinimumExpanding, QtGui.QSizePolicy.Expanding)
        self.user_root = app_config()['cg_lumberjack_dir']
        self.panel.addWidget(self.company_widget)
        self.panel.addStretch(0)
        self.load_companies()
        self.project_management = 'lumbermill'

        self.company_widget.add_button.clicked.connect(self.on_create_company)
        self.company_widget.list.clicked.connect(self.on_company_changed)

    def on_company_changed(self):
        self.path_object.set_attr(company=self.company_widget.list.selectedItems()[0].text())
        if self.path_object.company:
            if self.path_object.company != '*':
                self.project_management = app_config()['account_info']['project_management']
                self.check_default_company_globals()
        self.update_location()

    def on_create_company(self):
        dialog = InputDialog(title='Create Company', message='Enter the name for the company:', line_edit=True)
        dialog.exec_()

        if dialog.button == 'Ok':
            company = dialog.line_edit.text()
            self.path_object.set_attr(company=company)
            CreateProductionData(self.path_object, project_management='lumbermill')
            self.load_companies()

    def create_company_globals(self, company, proj_management):
        print 'Creating Company Globals %s' % company
        dir_ = os.path.join(self.user_root, 'companies', company)
        if not os.path.exists(dir_):
            print '%s doesnt exist, making it' % dir_
            os.makedirs(dir_)
            app_config(company=company, proj_management=proj_management)
            # set the config stuff according to what's up

    def check_default_company_globals(self):
        """
        ensures there are globals directories in the right place, this should really have a popup if it's not
        successful.
        :return:
        """
        self.path_object.set_project_config()
        if self.path_object.company:
            if self.path_object.company != '*':
                dir_ = os.path.dirname(self.path_object.company_config)
                if not os.path.exists(dir_):
                    print 'Creating Directory for Company Config File %s' % dir_
                    os.makedirs(dir_)

    def load_companies(self):
        self.company_widget.list.clear()
        companies_loc = '%s/*' % self.path_object.root
        companies = glob.glob(companies_loc)
        if companies:
            for each in companies:
                if '_config' not in each:
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


class ProjectPanel(QtGui.QWidget):
    location_changed = QtCore.Signal(object)

    def __init__(self, parent=None, path_object=None, search_box=None):
        QtGui.QWidget.__init__(self, parent)
        self.path_object = path_object
        self.project_management = app_config()['account_info']['project_management']
        self.user_email = app_config()['project_management'][self.project_management]['users'][current_user()]
        self.root = app_config()['paths']['root']  # Company Specific
        self.user_root = app_config()['cg_lumberjack_dir']
        self.left_column_visibility = True

        # Create the Left Panel
        self.panel = QtGui.QVBoxLayout(self)

        self.project_filter = ProjectWidget(title="Projects", pixmap=QtGui.QPixmap(icon_path('project24px.png')),
                                            search_box=search_box)

        self.panel.addWidget(self.project_filter)
        self.load_projects()

        self.project_filter.data_table.selected.connect(self.on_project_changed)
        self.project_filter.add_button.clicked.connect(self.on_create_project)

    def on_project_changed(self, data):
        self.path_object.set_attr(project=data[0][0])
        self.path_object.set_attr(scope='*')
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
        if not projects:
            print 'no projects for %s' % self.path_object.company
            self.project_filter.data_table.setEnabled(False)
            self.project_filter.add_button.setText('Create First Project')
        else:
            self.project_filter.data_table.setEnabled(True)
            self.project_filter.add_button.setText('Add Project')

        self.project_filter.setup(ListItemModel(prep_list_for_table(projects, split_for_file=True), ['Name']))

        self.update_location(self.path_object)

    def update_location(self, path_object=None):
        if not path_object:
            path_object = self.path_object
        self.location_changed.emit(path_object.data)

    def on_create_project(self):

        progress_bar = self.parent().progress_bar
        dialog = CreateProjectDialog(parent=None, variable='project')
        dialog.exec_()
        if dialog.button == 'Ok':
            project_name = dialog.proj_line_edit.text()
            self.path_object.set_attr(project=project_name)
            production_management = dialog.proj_management_combo.currentText()
            print self.path_object.path_root
            print production_management
            process_method(progress_bar,
                           self.do_create_project,
                           args=(progress_bar, self.path_object, production_management),
                           text='Creating Project')
            self.path_object.set_attr(project='*')
            self.update_location()

    @staticmethod
    def do_create_project(progress_bar, path_object, production_management):
        CreateProductionData(path_object=path_object.path_root, file_system=True, project_management=production_management)
        print 'setting project management to %s' % production_management
        create_project_config(path_object.company, path_object.project)
        progress_bar.hide()

    def clear_layout(self, layout=None):
        clear_layout(self, layout=layout)


class TaskPanel(QtGui.QWidget):
    """
    Vertical Button Panel - built to display tasks in a vertical line.  This is essentially the Task Panel
    """
    add_button = QtCore.Signal(object)
    location_changed = QtCore.Signal(object)

    def __init__(self, parent=None, path_object=None, element='task', pixmap=None):
        QtGui.QWidget.__init__(self, parent)
        self.element = element
        if path_object:
            self.path_object = path_object
            elements = self.path_object.glob_project_element(element)
        else:
            return
        self.project_management = app_config()['account_info']['project_management']
        self.schema = app_config()['project_management'][self.project_management]['api']['default_schema']
        schema = app_config()['project_management'][self.project_management]['tasks'][self.schema]
        self.proj_man_tasks = schema['long_to_short'][self.path_object.scope]
        self.proj_man_tasks_short_to_long = schema['short_to_long'][self.path_object.scope]
        self.panel = QtGui.QVBoxLayout(self)
        self.title_layout = QtGui.QHBoxLayout()
        self.task_button = QtGui.QToolButton()
        self.task_button.setText('add %s' % element)
        self.task_button.setProperty('class', 'add_button')
        if pixmap:
            self.icon = QtGui.QLabel()
            self.icon.setPixmap(pixmap)
            self.h_layout.addWidget(self.icon)
            self.title_layout.addWidget(pixmap)
        self.title = QtGui.QLabel('%ss' % element.title())
        self.title.setProperty('class', 'ultra_title')
        self.title_layout.addWidget(self.title)
        self.title_layout.addStretch(1)
        self.title_layout.addWidget(self.task_button)

        self.panel.addLayout(self.title_layout)
        self.task_button.clicked.connect(self.add_button_clicked)
        for each in elements:
            task = self.proj_man_tasks_short_to_long[each]
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
            short = self.proj_man_tasks[text]
            self.path_object.__dict__[self.element] = short
            self.path_object.data[self.element] = short
            self.path_object.set_path()
            self.location_changed.emit(self.path_object)

    def clear_layout(self, layout=None):
        clear_layout(self, layout=layout)


class ScopePanel(QtGui.QWidget):
    location_changed = QtCore.Signal(object)

    def __init__(self, parent=None, path_object=None):
        QtGui.QWidget.__init__(self, parent)
        if path_object:
            self.path_object = path_object.copy(seq=None, shot=None, ingest_source=None, resolution='', version='',
                                                user=None, scope=None)
        else:
            return
        self.panel = QtGui.QVBoxLayout(self)
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
            button.setIcon(QtGui.QIcon(QtGui.QPixmap(os.path.join(icon_path(), image_name))))
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


class ProductionPanel(QtGui.QWidget):
    location_changed = QtCore.Signal(object)

    def __init__(self, parent=None, path_object=None, search_box=None, my_tasks=False):
        QtGui.QWidget.__init__(self, parent)
        # Create the Middle Panel
        if path_object:
            self.path_object = path_object.copy(seq='*', shot='*', ingest_source='*', resolution='', version='',
                                                user=None)
        else:
            return
        self.my_tasks = my_tasks
        self.panel = QtGui.QVBoxLayout(self)
        self.assets = None
        self.assets_filter_default = filter
        self.root = app_config()['paths']['root']
        self.radio_filter = 'Everything'
        self.clear_layout()
        self.assets = AssetWidget(self, title="", search_box=search_box)

        self.assets.add_button.show()
        self.set_scope_radio()
        self.panel.addWidget(self.assets)
        self.load_assets()
        self.assets.data_table.selected.connect(self.on_main_asset_selected)
        self.assets.shots_radio.clicked.connect(self.on_filter_radio_changed)
        self.assets.assets_radio.clicked.connect(self.on_filter_radio_changed)
        self.assets.tasks_radio.clicked.connect(self.load_tasks)

    def load_tasks(self):
        from cgl.core.config import UserConfig
        # TODO - figure out how to add the progress bar to this.
        self.assets.add_button.setEnabled(False)
        self.assets.data_table.clearSpans()
        data = []
        proj_man = app_config()['account_info']['project_management']
        login = app_config()['project_management'][proj_man]['users'][current_user()]['login']
        if proj_man == 'ftrack':
            # ideally we load from a .csv file and run this in the background only to update the .csv file.
            from plugins.project_management.ftrack.main import find_user_assignments
            process_method(self.parent().progress_bar, find_user_assignments, args=(self.path_object, login),
                           text='Finding Your Tasks')
            try:
                company_json = UserConfig().d['my_tasks'][self.path_object.company]
            except KeyError:
                print 'Couldnt find company %s in company_json tasks file.' % self.path_object.company
                self.parent().progress_bar.hide()
                return
            if self.path_object.project in company_json:
                project_tasks = company_json[self.path_object.project]
                if project_tasks:
                    print 1
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
                    print 'No Tasks Assigned for %s' % self.path_object.project
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
                obj_ = PathObject(str(each))
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
        print 'selecting'
        if data:
            print data[0][2]
            path_object = PathObject(data[0][2])
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
        from apps.lumbermill.elements import asset_creator
        if self.path_object.scope == 'assets':
            task_mode = True
        else:
            task_mode = False
        dialog = asset_creator.AssetCreator(self, path_dict=self.path_object.data, task_mode=task_mode)
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


def prep_list_for_table(list_, path_filter=None, split_for_file=False):
    list_.sort()
    output_ = []
    for each in list_:
        if path_filter:
            filtered = PathObject(each).data[path_filter]
            output_.append([filtered])
        else:
            if split_for_file:
                each = os.path.basename(each)
            output_.append([each])
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

