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
        self.radio_filter = radio_filter

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
        self.panel_tasks = TaskPanel(path_object=self.initial_path_object, user_email=self.user_email,
                                     user_name=self.user_name)
        self.panel_center.location_changed.connect(self.panel_tasks.on_main_asset_selected)
        self.render_layout = QtWidgets.QVBoxLayout()

        self.h_layout.addWidget(self.panel_left)
        self.h_layout.addWidget(self.panel_center)
        self.h_layout.addWidget(self.panel_tasks)
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



    # CLEAR/DELETE FUNCTIONS



    def clear_layout(self, layout):
        while layout.count():
            child = layout.takeAt(0)
            if child.widget() is not None:
                child.widget().deleteLater()
            elif child.layout() is not None:
                self.clear_layout(child.layout())

    # CONVENIENCE FUNCTIONS

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
