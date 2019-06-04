import os
from Qt import QtWidgets, QtCore, QtGui
from cglcore.config import app_config, UserConfig
from cglui.widgets.search import LJSearchEdit
from cglui.widgets.base import LJMainWindow
from cglui.widgets.dialog import LoginDialog
from cglcore.path import PathObject, start, icon_path, font_path, load_style_sheet, image_path, split_sequence_frange
from apps.lumbermill.elements.panels import ProjectPanel, ProductionPanel, ScopePanel, CompanyPanel, VButtonPanel

from apps.lumbermill.elements.FilesPanel import FilesPanel

ICON_WIDTH = 24


class PathWidget(QtWidgets.QFrame):

    def __init__(self, parent=None, path_object=None):
        QtWidgets.QFrame.__init__(self, parent)
        if path_object:
            self.path_object = PathObject(path_object)
            self.path_root = self.path_object.path_root
        else:
            return
        layout = QtWidgets.QHBoxLayout(self)
        self.path_line_edit = QtWidgets.QLineEdit()
        self.path_line_edit.setMinimumHeight(ICON_WIDTH)
        self.text = self.path_object.path_root
        layout.addWidget(self.path_line_edit)

        # add css
        self.setProperty('class', 'light_grey')
        self.path_line_edit.setProperty('class', 'medium_grey')
        ##self.path_line_edit.setObjectName('display_path')

    def update_path(self, path_object):
        if path_object:
            path_object = PathObject(path_object)
            if path_object.filename:
                if '###' in path_object.filename:
                    print path_object.filename
                    try:
                        filename = split_sequence_frange(path_object.filename)[0]
                        path_object.set_attr(filename=filename)
                    except TypeError:
                        print 'passing'

            print 'updating to %s' % path_object.path_root
            self.text = path_object.path_root
            self.path_line_edit.setText(path_object.path_root)


class NavigationWidget(QtWidgets.QFrame):
    location_changed = QtCore.Signal(object)

    def __init__(self, parent=None, path_object=None):
        QtWidgets.QFrame.__init__(self, parent)
        if path_object:
            self.path_object = path_object
        else:
            return
        self.setProperty('class', 'light_grey')
        self.back_button = QtWidgets.QPushButton()
        self.back_button.setToolTip('Go back')
        self.projects_button = QtWidgets.QPushButton()
        self.projects_button.setToolTip('Go to Projects')
        self.companies_button = QtWidgets.QPushButton()
        self.companies_button.setToolTip('Go to Companies')
        self.production_button = QtWidgets.QPushButton()
        self.production_button.setToolTip('Go to Shots')
        self.back_button.setStyleSheet("background: transparent;")
        self.projects_button.setStyleSheet("background: transparent;")
        self.companies_button.setStyleSheet("background: transparent;")
        self.production_button.setStyleSheet("background: transparent;")
        back_icon = os.path.join(icon_path(), 'back24px.png')
        home_icon = os.path.join(icon_path(), 'project24px.png')
        company_icon = os.path.join(icon_path(), 'company24px.png')
        self.shots_icon = os.path.join(icon_path(), 'shots24px.png')
        self.assets_icon = os.path.join(icon_path(), 'flower_40px.png')
        self.back_button.setIcon(QtGui.QIcon(back_icon))
        self.back_button.setIconSize(QtCore.QSize(ICON_WIDTH, ICON_WIDTH))
        self.companies_button.setIcon(QtGui.QIcon(company_icon))
        self.companies_button.setIconSize(QtCore.QSize(ICON_WIDTH, ICON_WIDTH))
        self.projects_button.setIcon(QtGui.QIcon(home_icon))
        self.projects_button.setIconSize(QtCore.QSize(ICON_WIDTH, ICON_WIDTH))
        self.production_button.setIcon(QtGui.QIcon(self.shots_icon))
        self.production_button.setIconSize(QtCore.QSize(ICON_WIDTH, ICON_WIDTH))
        self.current_location_line_edit = QtWidgets.QLineEdit()
        self.current_location_line_edit.setReadOnly(True)
        self.current_location_line_edit.setMinimumHeight(ICON_WIDTH*1.28)
        self.current_location_line_edit.hide()
        self.search_box = LJSearchEdit(self)


        layout = QtWidgets.QVBoxLayout(self)
        self.cl_row = QtWidgets.QHBoxLayout()

        self.cl_row.addWidget(self.back_button)
        self.cl_row.addWidget(self.companies_button)
        self.cl_row.addWidget(self.projects_button)
        self.cl_row.addWidget(self.production_button)
        self.cl_row.addWidget(self.search_box)
        #self.cl_row.addStretch(1)

        layout.addLayout(self.cl_row)
        layout.addWidget(self.current_location_line_edit)

        self.back_button.clicked.connect(self.back_button_pressed)
        self.companies_button.clicked.connect(self.buttons_pressed)
        self.projects_button.clicked.connect(self.buttons_pressed)
        self.set_text(self.path_object.path_root)

    def text(self):
        return self.current_location_line_edit.text()

    def set_text(self, text):
        self.current_location_line_edit.setText(text.replace('\\', '/'))
        if self.current_location_line_edit.text():
            self.path_object = PathObject(self.current_location_line_edit.text())
            
    def show_company(self):
        self.production_button.hide()
        self.companies_button.show()
        self.projects_button.hide()
        
    def show_projects(self):
        self.production_button.hide()
        self.companies_button.show()
        self.projects_button.show()
        
    def show_production(self):
        self.production_button.show()
        self.companies_button.show()
        self.projects_button.show()
        if self.path_object.scope == 'assets':
            self.production_button.setIcon(QtGui.QIcon(self.assets_icon))
            self.production_button.setToolTip('Go to Assets')
        elif self.path_object.scope == 'shots':
            self.production_button.setIcon(QtGui.QIcon(self.shots_icon))
            self.production_button.setToolTip('Go to Shots')

    def show_none(self):
        self.production_button.hide()
        self.companies_button.hide()
        self.projects_button.hide()
            
    def update_buttons(self, path_object=None):
        if not path_object:
            path_object = self.path_object
        if not path_object.company:
            self.show_none()
        elif path_object.company == '*':
            self.show_company()
        elif path_object.project == '*':
            self.show_projects()
        elif path_object.scope == 'IO':
            self.show_projects()
        elif path_object.scope == '*':
            self.show_projects()
        elif path_object.seq == '*':
            self.show_production()
        elif path_object.type == '*':
            self.show_production()
        else:
            self.show_production()

    def buttons_pressed(self):
        if self.sender() == self.projects_button:
            path = '%s/%s/source/*' % (self.path_object.root, self.path_object.company)
        elif self.sender() == self.companies_button:
            path = '%s/%s' % (self.path_object.root, '*')
        elif self.sender() == self.production_button:
            pass
        new_obj = PathObject(path)
        self.location_changed.emit(new_obj)

    def back_button_pressed(self):
        path_object = PathObject(self.current_location_line_edit.text())
        path_object.set_attr(context='source')
        # if i'm a task, show me all the assets or shots
        last = path_object.get_last_attr()

        if last == 'filename':
            last = 'task'
        if last == 'resolution':
            last = 'task'
        if last == 'version':
            if path_object.scope == 'IO':
                last = 'scope'
            else:
                last = 'task'
        if last == 'user':
            last = 'task'
        if last == 'task':
            if path_object.task == '*':
                new_path = self.format_new_path(path_object, 'scope')
            else:
                # send them to the tasks page
                new_path = self.format_new_path(path_object, 'shot')
        elif last == 'seq' or last == 'type':
            if path_object.seq == '*' or path_object.type == '*':
                # send them to the projects page
                new_path = self.format_new_path(path_object, split_after='project')
            else:
                new_path = self.format_new_path(path_object, split_after='scope')
        elif last == 'shot' or last == 'asset':
            print 'Made it to shot or asset, this is rare'
            new_path = self.format_new_path(path_object, split_after='scope')
        elif last == 'scope':
            if path_object.scope == '*':
                # send them to the scope page
                new_path = self.format_new_path(path_object, split_after='context')
            else:
                # send them to the projects page
                new_path = self.format_new_path(path_object, split_after='project')
        elif last == 'project' or last == 'company':
            # send them to the "Companies" page
            new_path = path_object.root
        elif last == 'ingest_source':
            # send them to projects page
            new_path = self.format_new_path(path_object, split_after='project')
        else:
            print path_object.path_root
            print 'Nothing built for %s' % last
            return
        self.path_object = PathObject(new_path)
        self.update_buttons()
        self.location_changed.emit(self.path_object)

    def format_new_path(self, path_object, split_after=None):
        new_path = '%s/%s' % (path_object.split_after(split_after), '*')
        print new_path
        return new_path


class CGLumberjackWidget(QtWidgets.QWidget):

    def __init__(self, parent=None, user_name=None, user_email=None, company=None, path=None, radio_filter=None,
                 show_import=False):
        QtWidgets.QWidget.__init__(self, parent)
        try:
            font_db = QtWidgets.QFontDatabase()
            font_db.addApplicationFont(os.path.join(font_path(), 'ARCADECLASSIC.TTF'))
            font_db.addApplicationFont(os.path.join(font_path(), 'ka1.ttf'))
        except AttributeError:
            print 'Skipping Loading Fonts - possible Pyside2 issue'

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
        self.setMinimumWidth(700)
        self.setMinimumHeight(600)

        self.layout = QtWidgets.QVBoxLayout(self)
        self.setContentsMargins(0, 0, 0, 0)
        self.layout.setContentsMargins(0, 0, 0, 0)
        if path:
            try:
                self.path_object = PathObject(path)
                if self.path_object.context == 'render':
                    self.path_object.set_attr(context='source')
                    self.path_object.set_attr(resolution=None)
                    self.path_object.set_attr(version=None)
                    self.path_object.set_attr(user='')
                    self.path_object.set_attr(task='*')
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
        self.nav_widget = NavigationWidget(path_object=self.path_object)
        self.path_widget = PathWidget(path_object=self.path_object)
        self.nav_widget.update_buttons()
        self.path_widget.update_path(path_object=self.path_object)

        self.nav_widget.location_changed.connect(self.update_location)
        self.nav_widget.location_changed.connect(self.path_widget.update_path)
        self.layout.addWidget(self.nav_widget)
        self.update_location(self.path_object)

    def update_location(self, data):
        print
        try:
            if self.sender().force_clear:
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
        self.nav_widget.set_text(path_object.path_root)
        self.nav_widget.update_buttons(path_object=path_object)
        last = path_object.get_last_attr()
        seq_attrs = ['seq', 'type']
        shot_attrs = ['shot', 'asset']

        try:
            print 'Updating location to: %s' % path_object.path_root
        except AttributeError:
            print 'nothing found'
        if path_object.scope == 'IO':
            if path_object.version:
                if not self.panel:
                    from apps.lumbermill.elements.IOPanel import IOPanel
                    self.panel = IOPanel(parent=self, path_object=path_object)
                    self.setMinimumWidth(1100)
                    self.setMinimumHeight(700)
                    self.panel.location_changed.connect(self.update_location)
                    self.panel.location_changed.connect(self.path_widget.update_path)
                    self.layout.addWidget(self.panel)
                    self.layout.addWidget(self.path_widget)
                return

        if last == 'filename':
            if self.panel:
                # if we already have a panel, and we're getting a filename it means it's a currently selected file
                # and we don't want to reload the panel or it gets into a loop and won't select the file
                return
            else:
                new_path_object = path_object.copy(user=None, resolution='high', filename=None)
                self.load_files_panel(path_object=new_path_object)
        else:
            if self.panel:
                self.panel.clear_layout()
        if last == 'resolution':
            pass
            self.load_files_panel(path_object)
        if last == 'project':
            if path_object.project == '*':
                self.panel = ProjectPanel(path_object=path_object, search_box=self.nav_widget.search_box)
            else:
                self.panel = ProductionPanel(path_object=path_object, search_box=self.nav_widget.search_box)
        if last == 'scope':
            if path_object.scope == '*':
                self.panel = ScopePanel(path_object=path_object)
            elif path_object.scope == 'IO':
                from apps.lumbermill.elements.IOPanel import IOPanel
                self.panel = IOPanel(path_object=path_object)
            else:
                self.panel = ProductionPanel(path_object=path_object, search_box=self.nav_widget.search_box)
        elif last in shot_attrs:
            if path_object.shot == '*' or path_object.asset == '*' or path_object.seq == '*' or path_object.type == '*':
                self.panel = ProductionPanel(path_object=path_object, search_box=self.nav_widget.search_box)
            else:
                self.panel = VButtonPanel(path_object=path_object, element='task')
                self.panel.add_button.connect(self.add_task)
        elif last in seq_attrs:
            if path_object.shot == '*' or path_object.asset == '*' or path_object.seq == '*' or path_object.type == '*':
                self.panel = ProductionPanel(path_object=path_object, search_box=self.nav_widget.search_box)
        elif last == 'ingest_source':
            from apps.lumbermill.elements.IOPanel import IOPanel
            self.panel = IOPanel(path_object=path_object)
        elif last == 'task':
            if path_object.task == '*':
                self.panel = VButtonPanel(path_object=path_object, element='task')
                self.panel.add_button.connect(self.add_task)
            else:
                self.load_files_panel(path_object)
        elif last == 'company':
            self.panel = CompanyPanel(path_object=path_object, search_box=self.nav_widget.search_box)
        if self.panel:
            self.panel.location_changed.connect(self.update_location)
            self.panel.location_changed.connect(self.path_widget.update_path)
            self.layout.addWidget(self.panel)
            to_delete = []
            # Why do i have to do this?!?!?
            for i in range(self.layout.count()):
                if i == 2:
                    child = self.layout.takeAt(i-1)
                    to_delete.append(child)
            for each in to_delete:
                each.widget().deleteLater()
        self.layout.addWidget(self.path_widget)

    def add_task(self, path_object):
        print 'Adding Task'
        from apps.lumbermill.elements import asset_creator
        task_mode = True
        dialog = asset_creator.AssetCreator(self, path_dict=path_object.data, task_mode=task_mode)
        dialog.exec_()
        self.update_location(path_object.data)

    def load_files_panel(self, path_object):
        self.panel = FilesPanel(path_object=path_object, user_email=self.user_email,
                                user_name=self.user_name, show_import=self.show_import)
        self.panel.open_signal.connect(self.open_clicked)
        self.panel.import_signal.connect(self.import_clicked)
        self.panel.new_version_signal.connect(self.new_version_clicked)
        self.panel.source_selection_changed.connect(self.set_source_selection)

    def set_source_selection(self, data):
        self.source_selection = data

    def open_clicked(self):
        if '####' in self.path_widget.path_line_edit.text():
            print 'Nothing set for sequences yet'
        else:
            print 'Opening %s' % self.path_widget.path_line_edit.text()
            start(self.path_widget.path_line_edit.text())

    @staticmethod
    def import_clicked():
        print 'import clicked'

    @staticmethod
    def new_version_clicked():
        print 'New Version Clicked'


class CGLumberjack(LJMainWindow):
    def __init__(self, show_import=False, ):
        LJMainWindow.__init__(self)
        #self.setWindowFlags(QtCore.Qt.FramelessWindowHint)
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
                                                 radio_filter=self.filter,
                                                 show_import=show_import))
        if self.user_name:
            self.setWindowTitle('Lumbermill - Logged in as %s' % self.user_name)
        else:
            self.setWindowTitle("Lumbermill - Log In")
        self.status_bar = QtWidgets.QStatusBar()
        self.setStatusBar(self.status_bar)

        # Load Style Sheet and set up Styles:
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
        open_globals = QtWidgets.QAction('Edit Globals', self)
        settings.setShortcut('Ctrl+,')
        menu_designer = QtWidgets.QAction('Menu Designer', self)
        preflight_designer = QtWidgets.QAction('Preflight Designer', self)
        ingest_dialog = QtWidgets.QAction('Ingest Tool', self)
        # add actions to the file menu
        tools_menu.addAction(settings)
        tools_menu.addAction(open_globals)
        tools_menu.addAction(menu_designer)
        tools_menu.addAction(preflight_designer)
        tools_menu.addAction(ingest_dialog)
        # connect signals and slots
        open_globals.triggered.connect(self.open_company_globals)
        settings.triggered.connect(self.on_settings_clicked)
        menu_designer.triggered.connect(self.on_menu_designer_clicked)
        preflight_designer.triggered.connect(self.on_preflight_designer_clicked)
        login.triggered.connect(self.on_login_clicked)

    def open_company_globals(self):
        # Need a gui for choosing these bad boys
        print app_config()['account_info']['user_directory']
        print self.centralWidget().path_object.company_config
        print self.centralWidget().path_object.project_config
        start(self.centralWidget().path_object.company_config)

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

    def on_preflight_designer_clicked(self):
        from apps.pipeline.preflight_designer import PreflightDesigner
        dialog = PreflightDesigner(self)
        dialog.setMinimumWidth(1200)
        dialog.setMinimumHeight(500)
        dialog.exec_()

    def on_menu_designer_clicked(self):
        from apps.pipeline.menu_designer import MenuDesigner
        dialog = MenuDesigner(self)
        dialog.setMinimumWidth(1200)
        dialog.setMinimumHeight(500)
        dialog.exec_()

    def closeEvent(self, event):
        # set the current path so that it works on the load better.
        user_config = UserConfig(company=self.centralWidget().company,
                                 user_email=self.centralWidget().user_email,
                                 user_name=self.centralWidget().user_name,
                                 current_path=self.centralWidget().path_widget.text)
        user_config.update_all()


if __name__ == "__main__":
    from cglui.startup import do_gui_init
    app = do_gui_init()
    splash_pix = QtGui.QPixmap(image_path('lumbermill.jpg'))
    splash = QtGui.QSplashScreen(splash_pix, QtCore.Qt.WindowStaysOnTopHint)
    splash.setMask(splash_pix.mask())
    splash.show()
    td = CGLumberjack()
    td.show()
    td.raise_()
    # setup stylesheet
    style_sheet = load_style_sheet()
    app.setStyleSheet(style_sheet)
    splash.finish(td)
    app.exec_()
