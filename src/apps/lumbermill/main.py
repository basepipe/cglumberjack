import os
import time
import logging
import shutil
from Qt import QtWidgets, QtCore, QtGui
from cglcore.config import app_config, UserConfig
from cglui.widgets.search import LJSearchEdit
from cglui.widgets.base import LJMainWindow
from cglui.widgets.dialog import LoginDialog, InputDialog
from cglcore.path import PathObject, start, icon_path, font_path, load_style_sheet, split_sequence_frange, start_url
from cglui.widgets.progress_gif import ProgressDialog
from apps.lumbermill.elements.panels import ProjectPanel, ProductionPanel, ScopePanel, CompanyPanel, TaskPanel
from apps.lumbermill.elements.FilesPanel import FilesPanel
try:
    import apps.lumbermill.elements.IOPanel as IOP
    DO_IOP = True
except ImportError:
    DO_IOP = False

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
                    try:
                        filename = split_sequence_frange(path_object.filename)[0]
                        path_object.set_attr(filename=filename)
                    except TypeError:
                        logging.error('passing update_path due to exeption')
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
        self.shots_button = QtWidgets.QPushButton()
        self.shots_button.setToolTip('Go to Shots')
        self.back_button.setStyleSheet("background: transparent;")
        self.projects_button.setStyleSheet("background: transparent;")
        self.companies_button.setStyleSheet("background: transparent;")
        self.shots_button.setStyleSheet("background: transparent;")
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
        self.shots_button.setIcon(QtGui.QIcon(self.shots_icon))
        self.shots_button.setIconSize(QtCore.QSize(ICON_WIDTH, ICON_WIDTH))
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
        self.cl_row.addWidget(self.shots_button)
        self.cl_row.addWidget(self.search_box)
        self.cl_row.addStretch(1)

        layout.addLayout(self.cl_row)
        layout.addWidget(self.current_location_line_edit)

        self.back_button.clicked.connect(self.back_button_pressed)
        self.companies_button.clicked.connect(self.buttons_pressed)
        self.projects_button.clicked.connect(self.buttons_pressed)
        self.shots_button.clicked.connect(self.buttons_pressed)
        self.set_text(self.path_object.path_root)

    def text(self):
        return self.current_location_line_edit.text()

    def set_text(self, text):
        self.current_location_line_edit.setText(text.replace('\\', '/'))
        if self.current_location_line_edit.text():
            self.path_object = PathObject(self.current_location_line_edit.text())
            
    def show_company(self):
        self.shots_button.hide()
        self.companies_button.show()
        self.projects_button.hide()
        
    def show_projects(self):
        self.shots_button.hide()
        self.companies_button.show()
        self.projects_button.show()
        
    def show_production(self):
        self.shots_button.show()
        self.companies_button.show()
        self.projects_button.show()
        if self.path_object.scope == 'assets':
            self.shots_button.setIcon(QtGui.QIcon(self.assets_icon))
            self.shots_button.setToolTip('Go to Assets')
        elif self.path_object.scope == 'shots':
            self.shots_button.setIcon(QtGui.QIcon(self.shots_icon))
            self.shots_button.setToolTip('Go to Shots')

    def show_none(self):
        self.shots_button.hide()
        self.companies_button.hide()
        self.projects_button.hide()
            
    def update_buttons(self, path_object=None):
        if not path_object:
            if self.path_object:
                path_object = self.path_object
            else:
                return
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
        elif self.sender() == self.shots_button:
            path = '%s/%s/source/%s/%s/*' % (self.path_object.root, self.path_object.company, self.path_object.project,
                                             self.path_object.scope)
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
            logging.debug(path_object.path_root)
            logging.debug('Nothing built for %s' % last)
            return
        self.path_object = PathObject(new_path)
        self.update_buttons()
        self.location_changed.emit(self.path_object)

    def format_new_path(self, path_object, split_after=None):
        new_path = '%s/%s' % (path_object.split_after(split_after), '*')
        return new_path


class CGLumberjackWidget(QtWidgets.QWidget):

    def __init__(self, parent=None, project_management=None, user_name=None, user_email=None, company=None, path=None, radio_filter=None,
                 show_import=False):
        QtWidgets.QWidget.__init__(self, parent)
        try:
            font_db = QtWidgets.QFontDatabase()
            font_db.addApplicationFont(os.path.join(font_path(), 'ARCADECLASSIC.TTF'))
            font_db.addApplicationFont(os.path.join(font_path(), 'ka1.ttf'))
        except AttributeError:
            logging.error('Skipping Loading Fonts - possible Pyside2 issue')

        # Environment Stuff
        self.show_import = show_import
        self.user = user_name
        self.default_user = user_name
        self.user_email = user_email
        self.user_name = user_name
        self.company = company
        self.user_default = self.user
        self.project_management = project_management
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
        self.frange = None

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
                    if not self.path_object.task:
                        self.path_object.set_attr(task='*')
                    self.path_object.set_attr(filename='')
                    self.path_object.set_attr(ext='')
            except IndexError:
                logging.error('Path is not set')
                pass
        else:
            self.path_object = PathObject(self.root)
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
        # self.nav_widget.update_buttons()
        self.path_widget.update_path(path_object=self.path_object)

        self.nav_widget.location_changed.connect(self.update_location)
        self.nav_widget.location_changed.connect(self.path_widget.update_path)
        self.layout.addWidget(self.nav_widget)
        self.update_location(self.path_object)

    def update_location(self, data):
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
        if path_object.frange:
            self.frange = path_object.frange
        self.nav_widget.set_text(path_object.path_root)
        self.nav_widget.update_buttons(path_object=path_object)
        last = path_object.get_last_attr()
        seq_attrs = ['seq', 'type']
        shot_attrs = ['shot', 'asset']

        if DO_IOP:
            if path_object.scope == 'IO':
                if path_object.version:
                    if not self.panel:
                        self.panel = IOP.IOPanel(parent=self, path_object=path_object)
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
                if DO_IOP:
                    self.panel = IOP.IOPanel(path_object=path_object)
            else:
                self.panel = ProductionPanel(path_object=path_object, search_box=self.nav_widget.search_box)
        elif last in shot_attrs:
            if path_object.shot == '*' or path_object.asset == '*' or path_object.seq == '*' or path_object.type == '*':
                self.panel = ProductionPanel(path_object=path_object, search_box=self.nav_widget.search_box)
            else:
                self.panel = TaskPanel(path_object=path_object, element='task')
                self.panel.add_button.connect(self.add_task)
        elif last in seq_attrs:
            if path_object.shot == '*' or path_object.asset == '*' or path_object.seq == '*' or path_object.type == '*':
                self.panel = ProductionPanel(path_object=path_object, search_box=self.nav_widget.search_box)
        elif last == 'ingest_source':
            if DO_IOP:
                self.panel = IOP.IOPanel(path_object=path_object)
        elif last == 'task':
            if path_object.task == '*':
                self.panel = TaskPanel(path_object=path_object, element='task')
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
        #self.panel.new_version_signal.connect(self.new_version_clicked)
        self.panel.review_signal.connect(self.review_clicked)
        self.panel.publish_signal.connect(self.publish_clicked)
        self.panel.source_selection_changed.connect(self.set_source_selection)

    def set_source_selection(self, data):
        self.source_selection = data

    def open_clicked(self):
        if '####' in self.path_widget.path_line_edit.text():
            logging.error('Nothing set for sequences yet')
        else:
            logging.info('Opening %s' % self.path_widget.path_line_edit.text())
            start(self.path_widget.path_line_edit.text())

    @staticmethod
    def import_clicked():
        print 'import clicked'

    def review_clicked(self, filepath=None):
        from cglcore.convert import create_hd_proxy, create_mov
        if not filepath:
            selection = PathObject(self.path_widget.path_line_edit.text())
        else:
            selection = PathObject(filepath)
        if selection.context == 'render':
            lin_images = ['exr', 'dpx']
            # LUMBERMILL REVIEWS
            if self.project_management == 'lumbermill':
                # do this for movies
                print 'Lumbermill Not connectect to review features'
            # FTRACK REVIEWS
            elif self.project_management == 'ftrack':
                hd_proxy = selection.path_root
                if selection.file_type == 'sequence':
                    if selection.ext in lin_images:
                        hd_proxy = create_hd_proxy(selection.path_root, start_frame=self.frange.split('-')[0])
                    create_mov(hd_proxy)
                elif selection.file_type == 'movie':
                    create_mov(hd_proxy)
                elif selection.file_type == 'image':
                    hd_proxy = create_hd_proxy(selection.path_root, review=True)
                else:
                    print 'Have not built anything for reviews of type: %s' % selection.file_type
            elif self.project_management == 'shotgun':
                print 'Shotgun Reviews not connected yet'
            selection.set_attr(filename='')
            selection.set_attr(ext='')
            print 'updating_location %s %s' % (selection.path_root, selection.data)
            self.update_location(data=selection.data)
        else:
            dialog = InputDialog(title="Prep for Review", message="Move or copy files to review area?",
                                 buttons=['Move', 'Copy'])
            dialog.exec_()
            move = False
            if dialog.button == 'Move':
                move = True
            if selection.file_type == 'sequence':
                sequence_name = selection.filename
                from_path = os.path.dirname(selection.path_root)
                to_object = PathObject(from_path)
                to_object.set_attr(context='render')
                for each in os.listdir(from_path):
                    from_file = os.path.join(from_path, each)
                    to_file = os.path.join(to_object.path_root, each)
                    if move:
                        shutil.move(from_file, to_file)
                    else:
                        shutil.copyfile(from_file, to_file)
                selection.set_attr(filename='')
                selection.set_attr(ext='')
                print 'updating_location %s %s' % (selection.path_root, selection.data)
                self.update_location(data=selection.data)
            else:
                to_object = PathObject.copy(selection, context='render')
                print 'Copying %s to %s' % (selection.path_root, to_object.path_root)
                if move:
                    shutil.move(selection.path_root, to_object.path_root)
                else:
                    shutil.copyfile(selection.path_root, to_object.path_root)
                selection.set_attr(filename='')
                selection.set_attr(ext='')
                self.update_location(data=selection.data)


    def publish_clicked(self):
        from plugins.preflight.launch import launch_
        selection = PathObject(self.path_widget.path_line_edit.text())
        task = selection.task
        launch_(self, task, selection)


class CGLumberjack(LJMainWindow):
    def __init__(self, show_import=False):
        LJMainWindow.__init__(self)
        #self.setWindowFlags(QtCore.Qt.FramelessWindowHint)
        # Check Globals first off:
        # Do i have a default company?
        # What is the default project management?
        # if not lumbermill do i have my proj_management settings?
        # what do i do if i'm not connect to the internet and i am using a project management service?

        user_config = UserConfig().d
        self.proj_man_user_name = user_config['proj_man_user_name']
        self.proj_man_user_email = user_config['proj_man_user_email']
        self.company = ''
        self.previous_path = user_config['previous_path']
        self.filter = 'Everything'
        self.previous_paths = user_config['previous_paths']
        self.project_management = app_config(company=self.company)['account_info']['project_management']
        self.setCentralWidget(CGLumberjackWidget(self, project_management=self.project_management,
                                                 user_email=self.proj_man_user_email,
                                                 user_name=self.proj_man_user_name,
                                                 company=self.company,
                                                 path=self.previous_path,
                                                 radio_filter=self.filter,
                                                 show_import=show_import))
        if self.proj_man_user_email:
            self.setWindowTitle('Lumbermill - Logged in as %s' % self.proj_man_user_email)
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
        proj_man = QtWidgets.QAction('%s' % self.project_management, self)
        tools_menu = menu_bar.addMenu('&Tools')
        if self.project_management != 'lumbermill':
            self.proj_man_link = two_bar.addAction(proj_man)
        self.login_menu = two_bar.addAction(login)
        settings = QtWidgets.QAction('Settings', self)
        open_globals = QtWidgets.QAction('Go to Company Globals', self)
        open_user_globals = QtWidgets.QAction('Go to User Globals', self)
        settings.setShortcut('Ctrl+,')
        menu_designer = QtWidgets.QAction('Menu Designer', self)
        shelf_designer = QtWidgets.QAction('Shelf Designer', self)
        preflight_designer = QtWidgets.QAction('Preflight Designer', self)
        ingest_dialog = QtWidgets.QAction('Ingest Tool', self)
        # add actions to the file menu
        tools_menu.addAction(settings)
        tools_menu.addAction(open_globals)
        tools_menu.addAction(open_user_globals)
        tools_menu.addAction(menu_designer)
        tools_menu.addAction(shelf_designer)
        tools_menu.addAction(preflight_designer)
        tools_menu.addAction(ingest_dialog)
        # connect signals and slots
        open_globals.triggered.connect(self.open_company_globals)
        open_user_globals.triggered.connect(self.open_user_globals)
        settings.triggered.connect(self.on_settings_clicked)
        menu_designer.triggered.connect(self.on_menu_designer_clicked)
        preflight_designer.triggered.connect(self.on_preflight_designer_clicked)
        shelf_designer.triggered.connect(self.on_shelf_designer_clicked)
        login.triggered.connect(self.on_login_clicked)
        proj_man.triggered.connect(self.on_proj_man_menu_clicked)

    def on_proj_man_menu_clicked(self):
        link = app_config()['project_management'][self.project_management]['api']['server_url']
        start_url(link)

    def check_configs(self):
        return False

    def open_company_globals(self):
        logging.info(os.path.dirname(app_config()['paths']['globals']))
        start(os.path.dirname(app_config()['paths']['globals']))

    def open_user_globals(self):
        logging.info(os.path.dirname(app_config()['paths']['user_globals']))
        start(os.path.dirname(app_config()['paths']['user_globals']))

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
        pm = app_config()['account_info']['project_management']
        print pm
        def_schema = app_config()['project_management'][pm]['api']['default_schema']
        schema = app_config()['project_management'][pm]['tasks'][def_schema]
        from apps.pipeline.preflight_designer import PreflightDesigner
        dialog = PreflightDesigner(self, pm_tasks=schema)
        dialog.setMinimumWidth(1200)
        dialog.setMinimumHeight(500)
        dialog.exec_()

    def on_shelf_designer_clicked(self):
        from apps.pipeline.shelf_designer import ShelfDesigner
        dialog = ShelfDesigner(self)
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
        user_config = UserConfig(user_email=self.centralWidget().user_email,
                                 user_name=self.centralWidget().user_name,
                                 current_path=self.centralWidget().path_widget.text)
        user_config.update_all()

    # check the config file to see if it has a default company and a default location


def sleeper():
    time.sleep(5)


if __name__ == "__main__":
    from cglui.startup import do_gui_init
    app = do_gui_init()
    # splash_pix = QtGui.QPixmap(image_path('lumbermill.jpg'))
    splash_dialog = ProgressDialog('Loading...', 'night_rider.gif')
    splash_dialog.show()
    QtWidgets.qApp.processEvents()

    # splash = QtGui.QSplashScreen(splash_pix, QtCore.Qt.WindowStaysOnTopHint)
    # splash.setMask(splash_pix.mask())
    # splash.show()

    td = CGLumberjack(show_import=False)

    td.show()
    td.raise_()
    # # setup stylesheet
    style_sheet = load_style_sheet()
    app.setStyleSheet(style_sheet)
    #splash.finish(td)
    splash_dialog.hide()
    app.exec_()

