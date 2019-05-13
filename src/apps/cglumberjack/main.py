import glob
import os
import shutil
import logging
from Qt import QtWidgets, QtCore, QtGui
from cglcore.config import app_config, UserConfig
from cglui.widgets.base import LJMainWindow
from cglui.widgets.containers.model import ListItemModel
from cglui.widgets.dialog import LoginDialog
from cglcore.path import PathObject
from widgets import TaskWidget, AssetWidget
from panels import CompanyPanel, ProjectPanel, TaskPanel


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
        self.panel = None
        self.radio_filter = radio_filter

        self.layout = QtWidgets.QVBoxLayout(self)
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
        self.layout.addWidget(self.path_widget)
        # TODO - make a path object the currency rather than a dict, makes it easier.
        self.update_location(self.initial_path_object)
        #self.panel_center = ProjectPanel(path_object=self.initial_path_object)
        #self.panel_left.location_changed.connect(self.panel_center.on_project_changed)
        #self.panel_center.location_changed.connect(self.update_location2)

        # Create Empty layouts for tasks as well as renders.
        #self.render_layout = QtWidgets.QVBoxLayout()
        #self.panel_tasks = TaskPanel(path_object=self.initial_path_object, user_email=self.user_email,
        #                             user_name=self.user_name, render_layout=self.render_layout)
        #self.panel_center.location_changed.connect(self.panel_tasks.on_main_asset_selected)
        #self.panel_tasks.location_changed.connect(self.update_location2)


        #self.h_layout.addWidget(self.panel_left)
        #self.h_layout.addWidget(self.panel_center)
        #self.h_layout.addWidget(self.panel_tasks)
        #self.h_layout.addLayout(self.render_layout)


    def update_location(self, data):
        print data
        path_object = None
        if type(data) == dict:
            self.current_location = data
            path_object = PathObject(data)
        elif type(data) == PathObject:
            print 'made it'
            path_object = PathObject(data).copy()
        self.path_root = str(path_object.path_root)
        self.path_widget.set_text(path_object.path_root)
        try:
            clear_layout(self.panel_left)
        except AttributeError:
            pass
        company = path_object.company
        project = path_object.project
        scope = path_object.scope
        seq = path_object.seq
        shot = path_object.shot
        user = path_object.user
        version = path_object.version
        print version
        if scope == 'IO':
            if version:
                print 'adding task panel'
                self.panel = TaskPanel(path_object=self.initial_path_object, user_email=self.user_email,
                                       user_name=self.user_name, render_layout=None)
                #self.panel.location_changed.connect(self.update_location)
                self.layout.addWidget(self.panel)
            else:
                print 'load the asset widget'
        elif scope == 'shots' or scope == 'assets':
            if version:
                self.panel = TaskPanel(path_object=self.initial_path_object, user_email=self.user_email,
                                       user_name=self.user_name, render_layout=None)
                #self.panel.location_changed.connect(self.update_location)
                self.layout.addWidget(self.panel)
            else:
                print 'load the asset widget'
        elif not scope:
            print 'load the company/project widget'
            self.panel = CompanyPanel(path_object=self.initial_path_object)
            self.panel.location_changed.connect(self.update_location)
            self.layout.addWidget(self.panel)
        print company, project, scope, seq, shot, user, version





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


def clear_layout(layout):
    while layout.count():
        child = layout.takeAt(0)
        if child.widget() is not None:
            child.widget().deleteLater()
        elif child.layout() is not None:
            clear_layout(child.layout())


if __name__ == "__main__":
    from cglui.startup import do_gui_init
    app = do_gui_init()
    td = CGLumberjack()
    td.show()
    td.raise_()
    # setup stylesheet
    app.exec_()
