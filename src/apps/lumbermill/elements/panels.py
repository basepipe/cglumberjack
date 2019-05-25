import glob
import os
from Qt import QtWidgets, QtCore, QtGui
from cglcore.config import app_config
from cglui.widgets.combo import LabelComboRow
from apps.lumbermill.elements.widgets import LJListWidget
from cglui.widgets.containers.model import ListItemModel
from cglui.widgets.dialog import InputDialog
from cglcore.path import PathObject, CreateProductionData
from cglcore.path import create_project_config
from apps.lumbermill.elements.widgets import ProjectWidget, AssetWidget, CreateProjectDialog


class CompanyPanel(QtWidgets.QWidget):
    location_changed = QtCore.Signal(object)

    def __init__(self, parent=None, path_object=None):
        QtWidgets.QWidget.__init__(self, parent)
        self.path_object = path_object
        self.panel = QtWidgets.QVBoxLayout(self)
        self.company_widget = LJListWidget('Companies')
        self.company_widget.setMaximumHeight(5000)
        self.company_widget.list.setMaximumHeight(5000)
        self.company_widget.list.setSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.MinimumExpanding)
        self.user_root = app_config()['cg_lumberjack_dir']
        self.panel.addWidget(self.company_widget)
        self.panel.addStretch(1)
        self.load_companies()
        self.project_management = 'lumbermill'

        self.company_widget.add_button.clicked.connect(self.on_create_company)
        self.company_widget.list.clicked.connect(self.on_company_changed)

    def on_company_changed(self):
        self.path_object.set_attr(company=self.company_widget.list.selectedItems()[0].text())
        if self.path_object.company:
            if self.path_object.company != '*':
                self.project_management = app_config(company=self.path_object.company)['account_info']['project_management']
                self.check_default_company_globals()
        self.update_location()

    def on_create_company(self):
        dialog = CreateProjectDialog(parent=None, variable='company')
        dialog.exec_()

        if dialog.button == 'Ok':
            company = dialog.proj_line_edit.text()
            self.path_object.set_attr(company=company)
            self.create_company_globals(company)
            CreateProductionData(self.path_object, project_management=dialog.proj_management_combo.currentText())
            self.load_companies()

    def create_company_globals(self, company):
        print 'Creating Company Globals %s' % company
        dir_ = os.path.join(self.user_root, 'companies', company)
        if not os.path.exists(dir_):
            print '%s doesnt exist, making it' % dir_
            os.makedirs(dir_)

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
        companies = glob.glob(self.path_object.path_root)
        if companies:
            for each in companies:
                c = os.path.basename(each)
                self.company_widget.list.addItem(c)

    def clear_layout(self, layout=None):
        if not layout:
            layout = self.panel
        while layout.count():
            child = layout.takeAt(0)
            if child.widget() is not None:
                child.widget().deleteLater()
            elif child.layout() is not None:
                self.clear_layout(child.layout())

    def update_location(self, path_object=None):
        if not path_object:
          path_object = self.path_object
        path_object.set_attr(context='source')
        path_object.set_attr(project='*')
        self.location_changed.emit(path_object.data)


class ProjectPanel(QtWidgets.QWidget):
    location_changed = QtCore.Signal(object)

    def __init__(self, parent=None, path_object=None):
        QtWidgets.QWidget.__init__(self, parent)

        self.path_object = path_object
        self.project_management = app_config(company=self.path_object.company)['account_info']['project_management']
        self.root = app_config()['paths']['root']  # Company Specific
        self.user_root = app_config()['cg_lumberjack_dir']
        self.left_column_visibility = True

        # Create the Left Panel
        self.panel = QtWidgets.QVBoxLayout(self)
        self.project_filter = ProjectWidget(title="%s Projects" % self.path_object.company.title())

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
            self.project_filter.search_box.setEnabled(False)
            self.project_filter.data_table.setEnabled(False)
            self.project_filter.add_button.setText('Create First Project')
        else:
            self.project_filter.search_box.setEnabled(True)
            self.project_filter.data_table.setEnabled(True)
            self.project_filter.add_button.setText('+')

        self.project_filter.setup(ListItemModel(prep_list_for_table(projects, split_for_file=True), ['Name']))

        self.update_location(self.path_object)

    def update_location(self, path_object=None):
        if not path_object:
            path_object = self.path_object
        self.location_changed.emit(path_object.data)

    def on_create_project(self):
        dialog = CreateProjectDialog(parent=None, variable='project')
        dialog.exec_()

        if dialog.button == 'Ok':
            project_name = dialog.proj_line_edit.text()
            self.path_object.set_attr(project=project_name)
            CreateProductionData(self.path_object, project_management=self.project_management)
            production_management = dialog.proj_management_combo.currentText()
            print 'setting project management to %s' % production_management
            create_project_config(self.path_object.company, self.path_object.project)
        self.path_object.set_attr(project='*')
        self.update_location()

    def clear_layout(self, layout=None):
        if not layout:
            layout = self.panel
        while layout.count():
            child = layout.takeAt(0)
            if child.widget() is not None:
                child.widget().deleteLater()
            elif child.layout() is not None:
                self.clear_layout(child.layout())


class ScopePanel(QtWidgets.QWidget):
    location_changed = QtCore.Signal(object)

    def __init__(self, parent=None, path_object=None):
        QtWidgets.QWidget.__init__(self, parent)
        if path_object:
            self.path_object = path_object.copy(seq=None, shot=None, ingest_source=None, resolution='', version='',
                                                user=None, scope=None)
        else:
            return

        self.panel = QtWidgets.QVBoxLayout(self)
        for each in ['assets', 'shots', 'IO']:
            button = QtWidgets.QPushButton(str(each))
            button.setMinimumHeight(100)
            self.panel.addWidget(button)
            button.clicked.connect(self.on_button_clicked)
        self.panel.addStretch(1)

    def on_button_clicked(self):
        scope = self.sender().text()
        if scope:
            self.path_object.set_attr(scope=scope)
            if scope is not 'IO':
                self.path_object.set_attr(seq='*')
            self.location_changed.emit(self.path_object)

    def clear_layout(self, layout=None):
        if not layout:
            layout = self.panel
        while layout.count():
            child = layout.takeAt(0)
            if child.widget() is not None:
                child.widget().deleteLater()
            elif child.layout() is not None:
                self.clear_layout(child.layout())


class ProductionPanel(QtWidgets.QWidget):
    location_changed = QtCore.Signal(object)

    def __init__(self, parent=None, path_object=None):
        QtWidgets.QWidget.__init__(self, parent)
        # Create the Middle Panel
        if path_object:
            self.path_object = path_object.copy(seq='*', shot='*', ingest_source='*', resolution='', version='',
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
        else:
            print 'items is %s' % items
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
            self.path_object.set_attr(scope='assets')
        elif self.sender().text() == 'Shots':
            self.path_object.set_attr(scope='shots')
        self.update_location(self.path_object)

    def clear_layout(self, layout=None):
        if not layout:
            layout = self.panel
        while layout.count():
            child = layout.takeAt(0)
            if child.widget() is not None:
                child.widget().deleteLater()
            elif child.layout() is not None:
                self.clear_layout(child.layout())


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

