from Qt import QtWidgets, QtCore, QtGui
from cglcore.config import app_config, UserConfig
from cglui.widgets.base import LJMainWindow
from cglui.widgets.dialog import LoginDialog
from import_main import ImportBrowser
from cglcore.path import PathObject
from panels import CompanyPanel, ProjectPanel, TaskPanel, IOPanel


class PathWidget(QtWidgets.QWidget):
    location_changed = QtCore.Signal(object)

    def __init__(self, parent=None, path=None):
        QtWidgets.QWidget.__init__(self, parent)
        self.back_button = QtWidgets.QToolButton()
        self.back_button.setText('<')
        self.current_location_label = QtWidgets.QLabel('Current Location')
        self.current_location_line_edit = QtWidgets.QLineEdit()
        self.current_location_line_edit.setReadOnly(True)
        #self.import_button = QtWidgets.QPushButton('Import')

        self.cl_row = QtWidgets.QHBoxLayout(self)
        self.cl_row.addWidget(self.back_button)
        self.cl_row.addWidget(self.current_location_label)
        self.cl_row.addWidget(self.current_location_line_edit)
        #self.cl_row.addWidget(self.import_button)
        self.back_button.clicked.connect(self.back_button_pressed)

    def set_text(self, text):
        self.current_location_line_edit.setText(text.replace('\\', '/'))

    def back_button_pressed(self):
        path_object = PathObject(self.current_location_line_edit.text())
        # if i'm a task, show me all the assets or shots
        if path_object.version:
            new_path = '%s/%s' % (path_object.split_after('scope'), '*')
        elif path_object.task:
            new_path = '%s/%s' % (path_object.split_after('scope'), '*')
        elif path_object.shot:
            new_path = '%s/%s' % (path_object.split_after('scope'), '*')
        elif path_object.project:
            new_path = '%s/%s' % (path_object.split_after('context'), '*')
        else:
            new_path = path_object.root
        new_object = PathObject(new_path)
        #if new_object.path_root.replace('\\', '/') == self.current_location_line_edit.text():
        #    return
        self.location_changed.emit(new_object)


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
        self.path_widget.location_changed.connect(self.update_location)
        self.layout.addWidget(self.path_widget)
        # TODO - make a path object the currency rather than a dict, makes it easier.
        self.update_location(self.initial_path_object)

    def update_location(self, data):
        if self.panel:
           self.panel.clear_layout()
        path_object = None
        if type(data) == dict:
            self.current_location = data
            path_object = PathObject(data)
        elif type(data) == PathObject:
            path_object = PathObject(data)
        self.path_root = str(path_object.path_root)
        self.path_widget.set_text(path_object.path_root)
        last = path_object.get_last_attr()
        shot_attrs = ['seq', 'shot', 'type', 'asset']
        if last == 'company' or last == 'project':
            if path_object.project == '*':
                self.panel = CompanyPanel(path_object=path_object)
            else:
                self.panel = ProjectPanel(path_object=path_object)
        elif last in shot_attrs:
            if path_object.shot == '*' or path_object.asset == '*' or path_object.seq == '*' or path_object.type == '*':
                self.panel = ProjectPanel(path_object=path_object)
            else:
                self.panel = TaskPanel(path_object=path_object, user_email=self.user_email,
                                       user_name=self.user_name, render_layout=None)
        elif last == 'input_company':
            if path_object.input_company == '*':
                self.panel = ProjectPanel(path_object=path_object)
            else:
                self.panel = IOPanel(path_object=path_object, user_email=self.user_email, user_name=self.user_name,
                                     render_layout=None)
        elif last == 'task':
            self.panel = TaskPanel(path_object=path_object, user_email=self.user_email,
                                   user_name=self.user_name, render_layout=None)

        if self.panel:
            self.panel.location_changed.connect(self.update_location)
            self.layout.addWidget(self.panel)
            to_delete = []
            # Why do i have to do this?!?!?
            for i in range(self.layout.count()):
                if i > 1:
                    print i-1, self.layout.count()
                    child = self.layout.takeAt(i-1)
                    to_delete.append(child)
            for each in to_delete:
                each.widget().deleteLater()


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
        import_tool = QtWidgets.QAction('Import Files', self)
        self.import_tool = two_bar.addAction(import_tool)
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
        import_tool.triggered.connect(self.on_import_clicked)

    def on_import_clicked(self):
        print 'Opening the Import Dialog'
        import_dialog = ImportBrowser()
        import_dialog.exec_()

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
