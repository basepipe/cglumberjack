from Qt import QtWidgets, QtCore, QtGui
from cglcore.config import app_config, UserConfig
from cglui.widgets.base import LJMainWindow
from cglui.widgets.dialog import LoginDialog
from cglcore.path import PathObject, start
from apps.lumbermill.elements.panels import ProjectPanel, ProductionPanel, ScopePanel, CompanyPanel
from apps.lumbermill.elements.IOPanel import IOPanel
from apps.lumbermill.elements.TaskPanel import TaskPanel


class BreadCrumb(QtWidgets.QWidget):
    location_changed = QtCore.Signal(object)

    def __init__(self, parent=None, path_object=None):
        QtWidgets.QWidget.__init__(self, parent)
        self.path_object = path_object
        self.layout = QtWidgets.QHBoxLayout(self)
        self.layout.setSpacing(1)

    def update_buttons(self, path_object=None):
        self.clear_layout()
        if not path_object:
            path_object = self.path_object
        if path_object.company == '*':
            buttons = ['companies']
        elif path_object.project == '*':
            buttons = ['companies']
        elif path_object.scope == 'IO':
            buttons = ['companies', 'projects']
        elif path_object.scope == '*':
            buttons = ['companies', 'projects']
        elif path_object.seq == '*':
            buttons = ['companies', 'projects', path_object.scope]
        elif path_object.type == '*':
            buttons = ['companies', 'projects', path_object.scope]
        else:
            buttons = ['companies', 'projects', path_object.scope]
        brightness = 50
        self.path_object = path_object
        for each in buttons:
            button = QtWidgets.QPushButton(each)
            button.name = each
            if each == 'companies' or each == 'projects' or each == 'assets' or each == 'shots':
                if path_object.company:
                    if path_object.company != '*':
                        button.name = '%s' % each.title()
                        button.setText(button.name)
            if button.name == 'ingest':
                brightness += 50

            button.setStyleSheet("background-color:rgb(%s,%s,%s);"
                                 "color: white" % (brightness, brightness, brightness))
            button.setMaximumHeight(20)
            self.layout.addWidget(button)
            button.clicked.connect(self.update_location)

    def update_location(self):
        if 'Projects' in self.sender().name:
            path = '%s/%s/source/*' % (self.path_object.root, self.path_object.company)
            print path
        elif 'Companies' in self.sender().name:
            print 'setting company'
            path = '%s/%s' % (self.path_object.root, '*')
        new_obj = PathObject(path)
        print new_obj.path_root
        self.location_changed.emit(new_obj)

    def clear_layout(self):
        while self.layout.count():
            child = self.layout.takeAt(0)
            if child.widget() is not None:
                child.widget().deleteLater()
            elif child.layout() is not None:
                self.clear_layout(child.layout())


class PathWidget(QtWidgets.QWidget):
    location_changed = QtCore.Signal(object)

    def __init__(self, parent=None):
        QtWidgets.QWidget.__init__(self, parent)
        self.back_button = QtWidgets.QToolButton()
        self.back_button.setText('<')
        self.current_location_line_edit = QtWidgets.QLineEdit()
        self.current_location_line_edit.setReadOnly(True)

        self.cl_row = QtWidgets.QHBoxLayout(self)
        self.cl_row.addWidget(self.back_button)
        self.cl_row.addWidget(self.current_location_line_edit)
        self.back_button.clicked.connect(self.back_button_pressed)

    def text(self):
        return self.current_location_line_edit.text()

    def set_text(self, text):
        self.current_location_line_edit.setText(text.replace('\\', '/'))
        ## TODO - PYSIDE fix is QtCore instead of QtWidgets for Nuke (Pyside2)
        #try:
        #    fm = QtWidgets.QFontMetrics(self.current_location_line_edit.font())
        #    self.current_location_line_edit.setFixedWidth(fm.boundingRect(text).width() + 25)
        #except AttributeError:
        #    pass
        if self.current_location_line_edit.text():
            path_object = PathObject(self.current_location_line_edit.text())

    def back_button_pressed(self):
        path_object = PathObject(self.current_location_line_edit.text())
        # if i'm a task, show me all the assets or shots
        if path_object.version:
            if path_object.scope == 'IO':
                new_path = '%s/%s' % (path_object.split_after('scope'), path_object.ingest_source)
            else:
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
            if not path_object.context:
                if path_object.context != '*':
                    if path_object.project == '*':
                        new_path = '%s/%s' % (path_object.root, '*')
                    else:
                        new_path = '%s/%s' % (path_object.split_after('context'), '*')
            if path_object.project == '*':
                new_path = '%s/%s' % (path_object.root, '*')
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
        #self.layout.setSpacing(0)
        self.setContentsMargins(0, 0, 0, 0)
        self.layout.setContentsMargins(0, 2, 0, 0)
        if path:
            try:
                self.path_object = PathObject(path)
            except IndexError:
                pass
        self.project = '*'
        self.scope = 'assets'
        self.shot = '*'
        self.seq = '*'
        self.ingest_source = '*'
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
        self.breadcrumb = BreadCrumb(path_object=self.path_object)
        self.breadcrumb.update_buttons()
        self.path_widget = PathWidget()
        self.path_widget.set_text(self.path_object.path_root)

        self.path_widget.location_changed.connect(self.update_location)
        self.breadcrumb.location_changed.connect(self.update_location)
        # TODO - make a path object the currency rather than a dict, makes it easier.
        self.layout.addWidget(self.breadcrumb)
        self.layout.addWidget(self.path_widget)
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
        self.breadcrumb.update_buttons(path_object=path_object)
        last = path_object.get_last_attr()
        shot_attrs = ['seq', 'shot', 'type', 'asset']
        if path_object.scope == 'IO':
            if path_object.version:
                return
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
        if last == 'project':
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
        elif last == 'ingest_source':
            self.panel = IOPanel(path_object=path_object)
        elif last == 'task':
            self.load_task_panel(path_object)
        elif last == 'company':
            self.panel = CompanyPanel(path_object=path_object)
        if self.panel:
            self.panel.location_changed.connect(self.update_location)
            self.layout.addWidget(self.panel)
            to_delete = []
            # Why do i have to do this?!?!?
            for i in range(self.layout.count()):
                if i > 2:
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
        else:
            print 'Opening %s' % self.path_object.path_root
            start(self.path_object.path_root)

    @staticmethod
    def import_clicked():
        print 'import clicked'

    @staticmethod
    def new_version_clicked():
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
            self.setWindowTitle('Lumbermill - Logged in as %s' % self.user_name)
        else:
            self.setWindowTitle("Lumbermill - Log In")
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
                                 current_path=self.centralWidget().path_widget.text())
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
