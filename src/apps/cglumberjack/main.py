from Qt import QtWidgets, QtCore, QtGui
from cglcore.config import app_config, UserConfig
from cglui.widgets.base import LJMainWindow
from cglui.widgets.dialog import LoginDialog
from cglcore.path import PathObject, start
from panels import ProjectPanel, ProductionPanel, ScopePanel
from IOPanel import IOPanel
from TaskPanel import TaskPanel
from import_main import ImportBrowser


class PathWidget(QtWidgets.QWidget):
    location_changed = QtCore.Signal(object)

    def __init__(self, parent=None):
        QtWidgets.QWidget.__init__(self, parent)
        self.back_button = QtWidgets.QToolButton()
        self.back_button.setText('<')
        self.project_label = QtWidgets.QLabel('<h2>Choose Project</h2>')
        self.current_location_line_edit = QtWidgets.QLineEdit()
        self.current_location_line_edit.setReadOnly(True)
        #self.import_button = QtWidgets.QPushButton('Import')

        self.cl_row = QtWidgets.QHBoxLayout(self)
        self.cl_row.addWidget(self.project_label)
        self.cl_row.addItem((QtWidgets.QSpacerItem(20, 0, QtWidgets.QSizePolicy.Minimum,
                                       QtWidgets.QSizePolicy.Minimum)))
        self.cl_row.addWidget(self.back_button)
        self.cl_row.addWidget(self.current_location_line_edit)
        self.cl_row.addItem((QtWidgets.QSpacerItem(20, 0, QtWidgets.QSizePolicy.MinimumExpanding,
                                       QtWidgets.QSizePolicy.Minimum)))
        #self.cl_row.addWidget(self.import_button)
        self.back_button.clicked.connect(self.back_button_pressed)

    def set_text(self, text):
        self.current_location_line_edit.setText(text.replace('\\', '/'))
        # TODO - PYSIDE fix is QtCore instead of QtWidgets for Nuke (Pyside2)
        try:
            fm = QtWidgets.QFontMetrics(self.current_location_line_edit.font())
            self.current_location_line_edit.setFixedWidth(fm.boundingRect(text).width() + 25)
        except AttributeError:
            pass
        if self.current_location_line_edit.text():
            path_object = PathObject(self.current_location_line_edit.text())
            if path_object.project:
                if path_object.project != '*':
                    self.project_label.setText('<h2>%s</h2>' % path_object.project.title())
                else:
                    self.project_label.setText('<h2>Choose Project</h2>')

    def back_button_pressed(self):
        path_object = PathObject(self.current_location_line_edit.text())
        # if i'm a task, show me all the assets or shots
        if path_object.version:
            new_path = '%s/%s' % (path_object.split_after('scope'), '*')
        elif path_object.task:
            new_path = '%s/%s' % (path_object.split_after('scope'), '*')
        elif path_object.shot:
            new_path = '%s/%s' % (path_object.split_after('scope'), '*')
        elif path_object.scope:
            if path_object.scope == '*':
                new_path = '%s/%s' % (path_object.split_after('context'), '*')
            else:
                new_path = '%s/%s' % (path_object.split_after('project'), '*')
        elif path_object.project:
            new_path = '%s/%s' % (path_object.split_after('context'), '*')
        else:
            new_path = path_object.root
        new_object = PathObject(new_path)
        self.location_changed.emit(new_object)


class CGLumberjackWidget(QtWidgets.QWidget):

    def __init__(self, parent=None, user_name=None, user_email=None, company=None, path=None, radio_filter=None,
                 show_import=False):
        QtWidgets.QWidget.__init__(self, parent)
        # Environment Stuff
        self.show_import = show_import
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
        self.path_object = None
        self.panel = None
        self.radio_filter = radio_filter
        self.source_selection = []

        self.layout = QtWidgets.QVBoxLayout(self)
        if path:
            try:
                self.path_object = PathObject(path)
            except IndexError:
                pass
        self.project = '*'
        self.scope = 'assets'
        self.shot = '*'
        self.seq = '*'
        self.input_company = '*'
        if self.path_object:
            if self.path_object.project:
                self.project = self.path_object.project
            if self.path_object.scope:
                self.scope = self.path_object.scope
            if self.path_object.shot:
                self.shot = self.path_object.shot
            if self.path_object.seq:
                self.seq = self.path_object.seq
        self.user_favorites = ''
        self.task = ''
        self.resolution = ''
        self.in_file_tree = None
        self.path_widget = PathWidget()
        self.path_widget.location_changed.connect(self.update_location)
        self.layout.addWidget(self.path_widget)
        # TODO - make a path object the currency rather than a dict, makes it easier.
        self.update_location(self.path_object)

    def update_location(self, data):
        try:
            if self.sender().force_clear:
                print 'I gotta clear this widget'
                if self.panel:
                    self.panel.clear_layout()
                    self.panel = None
        except AttributeError:
            pass
        path_object = None
        if type(data) == dict:
            path_object = PathObject(data)
        elif type(data) == PathObject:
            path_object = PathObject(data)
        self.path_widget.set_text(path_object.path_root)
        last = path_object.get_last_attr()
        shot_attrs = ['seq', 'shot', 'type', 'asset']

        if last == 'filename':
            if self.panel:
                return
            else:
                # TODO -  This needs to actually display the render panel as well, and reselect the actual filename.
                new_path_object = path_object.copy(user=None, resolution='high', filename=None)
                self.load_task_panel(path_object=new_path_object)
        else:
            if self.panel:
                self.panel.clear_layout()
        if last == 'resolution':
            self.load_task_panel(path_object)
        if last == 'company' or last == 'project':
            if path_object.project == '*':
                self.panel = ProjectPanel(path_object=path_object)
            else:
                self.panel = ProductionPanel(path_object=path_object)
        if last == 'scope':
            if path_object.scope == '*':
                self.panel = ScopePanel(path_object=path_object)
            elif path_object.scope == 'IO':
                self.panel = IOPanel(path_object=path_object)
            else:
                self.panel = ProductionPanel(path_object=path_object)
        elif last in shot_attrs:
            if path_object.shot == '*' or path_object.asset == '*' or path_object.seq == '*' or path_object.type == '*':
                self.panel = ProductionPanel(path_object=path_object)
            else:
                self.load_task_panel(path_object)
        elif last == 'input_company':
            if path_object.input_company == '*':
                self.panel = ProductionPanel(path_object=path_object)
            else:
                self.panel = IOPanel(path_object=path_object, user_email=self.user_email, user_name=self.user_name,
                                     render_layout=None)
        elif last == 'task':
            self.load_task_panel(path_object)

        if self.panel:
            self.panel.location_changed.connect(self.update_location)
            self.layout.addWidget(self.panel)
            to_delete = []
            # Why do i have to do this?!?!?
            for i in range(self.layout.count()):
                if i > 1:
                    child = self.layout.takeAt(i-1)
                    to_delete.append(child)
            for each in to_delete:
                each.widget().deleteLater()

    def load_task_panel(self, path_object):
        self.panel = TaskPanel(path_object=path_object, user_email=self.user_email,
                               user_name=self.user_name, show_import=self.show_import)
        self.panel.open_signal.connect(self.open_clicked)
        self.panel.import_signal.connect(self.import_clicked)
        self.panel.new_version_signal.connect(self.new_version_clicked)
        self.panel.source_selection_changed.connect(self.set_source_selection)

    def set_source_selection(self, data):
        self.source_selection = data

    def open_clicked(self):
        if '####' in self.path_object.path_root:
            print 'Nothing set for sequences yet'
            # config = app_config()['paths']
            # settings = app_config()['default']
            # cmd = "%s -framerate %s %s" % (config['ffplay'], settings['frame_rate'],
            # self.path_root.replace('####', '%04d'))
            # subprocess.Popen(cmd)
        else:
            print 'Opening %s' % self.path_object.path_root
            start(self.path_object.path_root)

    def import_clicked(self):
        print 'import clicked'

    def new_version_clicked(self):
        print 'New Version Clicked'


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
        icon = QtGui.QPixmap(":/images/lumberjack.24px.png").scaled(24, 24)
        self.setWindowIcon(icon)
        login = QtWidgets.QAction('Login', self)
        tools_menu = menu_bar.addMenu('&Tools')
        import_tool = QtWidgets.QAction('Import Files', self)
        self.import_tool = two_bar.addAction(import_tool)
        self.login_menu = two_bar.addAction(login)
        settings = QtWidgets.QAction('Settings', self)
        settings.setShortcut('Ctrl+,')
        menu_designer = QtWidgets.QAction('Menu Designer', self)
        ingest_dialog = QtWidgets.QAction('Ingest Tool', self)
        # add actions to the file menu
        tools_menu.addAction(settings)
        tools_menu.addAction(menu_designer)
        tools_menu.addAction(ingest_dialog)
        # connect signals and slots
        settings.triggered.connect(self.on_settings_clicked)
        menu_designer.triggered.connect(self.on_shelves_clicked)
        login.triggered.connect(self.on_login_clicked)
        import_tool.triggered.connect(self.on_import_clicked)

    def on_import_clicked(self):

        print 'Opening the Import Dialog'
        text = self.centralWidget().path_widget.current_location_line_edit.text()
        import_dialog = ImportBrowser(path_object=PathObject(text))
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
                                 current_path=self.centralWidget().path_object.path_root)
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
