import time
import os
import logging
from cgl.plugins.Qt import QtCore, QtGui, QtWidgets
from cgl.ui.widgets.progress_gif import ProgressGif, process_method
from cgl.ui.widgets.search import LJSearchEdit
from cgl.ui.widgets.base import LJMainWindow
from cgl.ui.widgets.dialog import LoginDialog, InputDialog
import cgl.core.path as cglpath
from cgl.core.util import current_user, check_for_latest_master, update_master
from cgl.core.config import app_config, UserConfig
from apps.lumbermill.elements.panels import ProjectPanel, ProductionPanel, ScopePanel, CompanyPanel, TaskPanel
from apps.lumbermill.elements.FilesPanel import FilesPanel
from cgl.ui.widgets.help import ReportBugDialog, RequestFeatureDialog
try:
    import apps.lumbermill.elements.IOPanel as IoP
    DO_IOP = True
except ImportError:
    IoP = None
    DO_IOP = False

ICON_WIDTH = 24


class PathWidget(QtWidgets.QFrame):

    def __init__(self, parent=None, path_object=None):
        QtWidgets.QFrame.__init__(self, parent)
        if path_object:
            self.path_object = cglpath.PathObject(path_object)
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
        # self.path_line_edit.setObjectName('display_path')

    def update_path(self, path_object):
        if isinstance(path_object, dict):
            path_object = cglpath.PathObject(path_object)
        if path_object:
            self.text = path_object.path_root
            self.path_line_edit.setText(path_object.path_root)


class NavigationWidget(QtWidgets.QFrame):
    location_changed = QtCore.Signal(object)
    my_tasks_clicked = QtCore.Signal()
    ingest_button_clicked = QtCore.Signal()
    refresh_button_clicked = QtCore.Signal(object)

    def __init__(self, parent=None, path_object=None):
        QtWidgets.QFrame.__init__(self, parent)
        if path_object:
            self.path_object = path_object
        else:
            return
        self.setProperty('class', 'light_grey')
        self.my_tasks_button = QtWidgets.QPushButton()
        self.my_tasks_button.setToolTip('My Tasks')
        tasks_icon = os.path.join(cglpath.icon_path(), 'star24px.png')
        self.my_tasks_button.setProperty('class', 'grey_border')
        self.my_tasks_button.setIcon(QtGui.QIcon(tasks_icon))
        self.my_tasks_button.setIconSize(QtCore.QSize(ICON_WIDTH, ICON_WIDTH))

        self.refresh_button = QtWidgets.QPushButton()
        self.refresh_button.setToolTip('Refresh')
        refresh_icon = os.path.join(cglpath.icon_path(), 'spinner11.png')
        self.refresh_button.setProperty('class', 'grey_border')
        self.refresh_button.setIcon(QtGui.QIcon(refresh_icon))
        self.refresh_button.setIconSize(QtCore.QSize(ICON_WIDTH, ICON_WIDTH))

        self.ingest_button = QtWidgets.QPushButton()
        self.ingest_button.setToolTip('My Tasks')
        self.ingest_button.setProperty('class', 'grey_border')
        ingest_icon = os.path.join(cglpath.icon_path(), 'ingest24px.png')
        self.ingest_button.setIcon(QtGui.QIcon(ingest_icon))
        self.ingest_button.setIconSize(QtCore.QSize(ICON_WIDTH, ICON_WIDTH))

        self.back_button = QtWidgets.QPushButton()
        self.back_button.setToolTip('Go back')
        self.projects_button = QtWidgets.QPushButton()
        self.projects_button.setToolTip('Go to Projects')
        self.companies_button = QtWidgets.QPushButton()
        self.companies_button.setToolTip('Go to Companies')
        self.my_tasks_button.setProperty('class', 'grey_border')
        self.back_button.setStyleSheet("background: transparent;")
        self.projects_button.setStyleSheet("background: transparent;")
        self.companies_button.setStyleSheet("background: transparent;")

        back_icon = os.path.join(cglpath.icon_path(), 'back24px.png')
        home_icon = os.path.join(cglpath.icon_path(), 'project24px.png')
        company_icon = os.path.join(cglpath.icon_path(), 'company24px.png')

        self.back_button.setIcon(QtGui.QIcon(back_icon))
        self.back_button.setIconSize(QtCore.QSize(ICON_WIDTH, ICON_WIDTH))
        self.companies_button.setIcon(QtGui.QIcon(company_icon))
        self.companies_button.setIconSize(QtCore.QSize(ICON_WIDTH, ICON_WIDTH))
        self.projects_button.setIcon(QtGui.QIcon(home_icon))
        self.projects_button.setIconSize(QtCore.QSize(ICON_WIDTH, ICON_WIDTH))
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
        self.cl_row.addWidget(self.my_tasks_button)
        self.cl_row.addWidget(self.refresh_button)
        self.cl_row.addWidget(self.search_box)

        self.cl_row.addWidget(self.ingest_button)

        layout.addLayout(self.cl_row)
        layout.addWidget(self.current_location_line_edit)

        self.my_tasks_button.clicked.connect(self.my_tasks_pressed)
        self.ingest_button.clicked.connect(self.ingest_clicked)
        self.refresh_button.clicked.connect(self.refresh_clicked)
        self.back_button.clicked.connect(self.back_button_pressed)
        self.companies_button.clicked.connect(self.buttons_pressed)
        self.projects_button.clicked.connect(self.buttons_pressed)
        self.set_text(self.path_object.path_root)

    def refresh_clicked(self):
        print 'Refresh clicked'
        self.refresh_button_clicked.emit(self.path_object)

    def text(self):
        return self.current_location_line_edit.text()

    def set_text(self, text):
        self.current_location_line_edit.setText(text.replace('\\', '/'))
        if self.current_location_line_edit.text():
            self.path_object = cglpath.PathObject(self.current_location_line_edit.text())
            
    def show_company(self):
        self.companies_button.show()
        self.projects_button.hide()
        self.my_tasks_button.hide()
        
    def show_projects(self):
        self.companies_button.show()
        self.projects_button.show()
        self.my_tasks_button.hide()
        
    def show_production(self):
        self.companies_button.show()
        self.projects_button.show()
        self.my_tasks_button.show()

    def show_none(self):
        self.shots_button.hide()
        self.my_tasks_button.hide()
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
            self.show_production()
        elif path_object.scope == '*':
            self.show_production()
        elif path_object.seq == '*':
            self.show_production()
        elif path_object.type == '*':
            self.show_production()
        else:
            self.show_production()

    def buttons_pressed(self):
        path = None
        if self.sender() == self.projects_button:
            path = '%s/%s/source/*' % (self.path_object.root, self.path_object.company)
        elif self.sender() == self.companies_button:
            path = '%s/%s' % (self.path_object.root, '*')
        elif self.sender() == self.shots_button:
            path = '%s/%s/source/%s/%s/*' % (self.path_object.root, self.path_object.company, self.path_object.project,
                                             self.path_object.scope)
        new_obj = cglpath.PathObject(path)
        self.location_changed.emit(new_obj)

    def my_tasks_pressed(self):
        self.my_tasks_clicked.emit()

    def ingest_clicked(self):
        if self.path_object.project and self.path_object.company and self.path_object.project != '*':
            self.path_object = self.path_object.copy(seq=None, shot=None, ingest_source=None, resolution='', version='',
                                                     user=None, scope='IO')
            self.location_changed.emit(self.path_object)
        else:
            print 'Please Choose a Company and a Project before pushing the ingest button'

    def back_button_pressed(self):
        path_object = cglpath.PathObject(self.current_location_line_edit.text())
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
        self.path_object = cglpath.PathObject(new_path)
        self.update_buttons()
        self.location_changed.emit(self.path_object)

    @staticmethod
    def format_new_path(path_object, split_after=None):
        new_path = '%s/%s' % (path_object.split_after(split_after), '*')
        return new_path


class CGLumberjackWidget(QtWidgets.QWidget):

    def __init__(self, parent=None, project_management=None, user_email=None, company=None,
                 path=None, radio_filter=None, show_import=False):
        QtWidgets.QWidget.__init__(self, parent)
        try:
            font_db = QtGui.QFontDatabase()
            font_db.addApplicationFont(os.path.join(cglpath.font_path(), 'ARCADECLASSIC.TTF'))
            font_db.addApplicationFont(os.path.join(cglpath.font_path(), 'ka1.ttf'))
        except AttributeError:
            logging.error('Skipping Loading Fonts - possible Pyside2 issue')

        # Environment Stuff
        self.show_import = show_import
        self.user_email = user_email
        self.company = company
        self.project_management = project_management
        self.root = app_config()['paths']['root']  # Company Specific
        self.user_root = app_config()['cg_lumberjack_dir']
        self.context = 'source'
        self.path_object = None
        self.panel = None
        self.radio_filter = radio_filter
        self.source_selection = []
        self.setMinimumWidth(840)
        self.setMinimumHeight(800)
        self.frame_range = None

        self.layout = QtWidgets.QVBoxLayout(self)
        self.setContentsMargins(0, 0, 0, 0)
        self.layout.setContentsMargins(0, 0, 0, 0)
        if path:
            try:
                self.path_object = cglpath.PathObject(path)
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
            self.path_object = cglpath.PathObject(self.root)
        # self.project = '*'
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
        self.progress_bar = ProgressGif()
        self.progress_bar.hide()
        # self.nav_widget.update_buttons()
        self.path_widget.update_path(path_object=self.path_object)

        self.nav_widget.location_changed.connect(self.update_location)
        self.nav_widget.refresh_button_clicked.connect(self.update_location_to_latest)
        self.nav_widget.my_tasks_clicked.connect(self.show_my_tasks)
        self.nav_widget.location_changed.connect(self.path_widget.update_path)
        self.layout.addWidget(self.nav_widget)
        self.update_location(self.path_object)

    def show_my_tasks(self):
        self.path_object = cglpath.PathObject(self.path_widget.path_line_edit.text())
        self.path_object.set_attr(user=current_user(), resolution='', filename='', ext='')
        self.path_object.set_attr(scope='shots', seq='*', shot=None, task=None)
        self.path_object.data['my_tasks'] = True
        self.path_widget.update_path(path_object=self.path_object)
        self.update_location(self.path_object)

    def update_location_to_latest(self, data):
        path_object = data.copy(latest=True)
        self.update_location(path_object)

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
            path_object = cglpath.PathObject(data)
        elif type(data) == cglpath.PathObject:
            path_object = cglpath.PathObject(data)
        if path_object.frame_range:
            self.frame_range = path_object.frame_range
        self.nav_widget.set_text(path_object.path_root)
        self.nav_widget.update_buttons(path_object=path_object)
        last = path_object.get_last_attr()
        seq_attrs = ['seq', 'type']
        shot_attrs = ['shot', 'asset']

        if DO_IOP:
            if path_object.scope == 'IO':
                if path_object.version:
                    if not self.panel:
                        self.panel = IoP.IOPanel(parent=self, path_object=path_object)
                        self.setMinimumWidth(1100)
                        self.setMinimumHeight(700)
                        self.panel.location_changed.connect(self.update_location)
                        self.panel.location_changed.connect(self.path_widget.update_path)
                        self.layout.addWidget(self.panel)
                        self.layout.addWidget(self.path_widget)
                    return
        if 'my_tasks' in path_object.data or last == 'scope':
            go_ahead = False
            if last == 'scope':
                go_ahead = True
                if path_object.scope == 'IO':
                    go_ahead = False
            else:
                if path_object.data['my_tasks']:
                    go_ahead = True
            if go_ahead:
                self.panel = ProductionPanel(parent=self, path_object=path_object, search_box=self.nav_widget.search_box,
                                             my_tasks=True)
                if self.panel:
                    if self.panel.load_tasks():
                        self.update_panel(set_tasks_radio=True)
                        self.layout.addWidget(self.progress_bar)
                        self.layout.addWidget(self.path_widget)
                        self.path_object.data['my_tasks'] = False
                        return
                    else:
                        self.panel = None
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
            self.load_files_panel(path_object)
        if last == 'project':
            if path_object.project == '*':
                self.panel = ProjectPanel(path_object=path_object, search_box=self.nav_widget.search_box)
            else:
                self.panel = ProductionPanel(parent=self, path_object=path_object, search_box=self.nav_widget.search_box)
        if last == 'scope':
            if path_object.scope == '*':
                self.panel = ScopePanel(path_object=path_object)
            elif path_object.scope == 'IO':
                if DO_IOP:
                    self.panel = IoP.IOPanel(path_object=path_object)
            else:
                self.panel = ProductionPanel(parent=self, path_object=path_object, search_box=self.nav_widget.search_box)
        elif last in shot_attrs:
            if path_object.shot == '*' or path_object.asset == '*' or path_object.seq == '*' or path_object.type == '*':
                self.panel = ProductionPanel(parent=self, path_object=path_object, search_box=self.nav_widget.search_box)
            else:
                self.panel = TaskPanel(path_object=path_object, element='task')
                self.panel.add_button.connect(self.add_task)
        elif last in seq_attrs:
            if path_object.shot == '*' or path_object.asset == '*' or path_object.seq == '*' or path_object.type == '*':
                self.panel = ProductionPanel(parent=self, path_object=path_object, search_box=self.nav_widget.search_box)
        elif last == 'ingest_source':
            if DO_IOP:
                self.panel = IoP.IOPanel(path_object=path_object)
        elif last == 'task':
            if path_object.task == '*':
                self.panel = TaskPanel(path_object=path_object, element='task')
                self.panel.add_button.connect(self.add_task)
            else:
                self.load_files_panel(path_object)
        elif last == 'company':
            self.panel = CompanyPanel(path_object=path_object, search_box=self.nav_widget.search_box)
        if self.panel:
            self.update_panel()
        self.layout.addWidget(self.progress_bar)
        self.layout.addWidget(self.path_widget)

    def update_panel(self, set_tasks_radio=False):
        self.panel.location_changed.connect(self.update_location)
        if set_tasks_radio:
            self.panel.assets.tasks_radio.setChecked(True)
        self.panel.location_changed.connect(self.path_widget.update_path)

        self.layout.addWidget(self.panel)
        to_delete = []
        for i in range(self.layout.count()):
            if i == 2:
                child = self.layout.takeAt(i - 1)
                to_delete.append(child)
        for each in to_delete:
            each.widget().deleteLater()

    def add_task(self, path_object):
        from apps.lumbermill.elements import asset_creator
        task_mode = True
        dialog = asset_creator.AssetCreator(self, path_dict=path_object.data, task_mode=task_mode)
        dialog.exec_()
        self.update_location(path_object.data)

    def load_files_panel(self, path_object):
        self.panel = FilesPanel(path_object=path_object, user_email=self.user_email,
                                show_import=self.show_import)
        self.panel.open_signal.connect(self.open_clicked)
        self.panel.import_signal.connect(self.import_clicked)
        # self.panel.new_version_signal.connect(self.new_version_clicked)
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
            cglpath.start(self.path_widget.path_line_edit.text())

    @staticmethod
    def import_clicked():
        print 'import clicked'

    def review_clicked(self):
        selection = cglpath.PathObject(self.path_widget.path_line_edit.text())
        selection.set_file_type()
        process_method(self.progress_bar, self.do_review, args=(self.progress_bar, selection), text='Submitting Review')
        print 'updating_location %s %s' % (selection.path_root, selection.data)
        self.update_location(data=selection.data)

    @staticmethod
    def do_review(progress_bar, path_object):
        from cgl.core.project import do_review
        do_review(progress_bar, path_object)

    def publish_clicked(self):
        from plugins.preflight.launch import launch_
        from cgl.ui.widgets.publish_dialog import PublishDialog
        selection = cglpath.PathObject(self.path_widget.path_line_edit.text())
        if not selection.filename or selection.context == 'source':
            dialog = InputDialog(title='Invalid Selection', message='Please select a valid file or sequence\nfrom '
                                                                    'the "Ready to Review/Publish" Section')
            dialog.exec_()
        else:
            task = selection.task
            dialog = PublishDialog(path_object=selection)
            dialog.do_publish.connect(lambda: launch_(self, task, selection, do_review=dialog.do_review))
            dialog.exec_()
            # launch_(self, task, selection)


class CGLumberjack(LJMainWindow):
    def __init__(self, show_import=False, user_info=None, start_time=None, previous_path=None):
        LJMainWindow.__init__(self)

        if start_time:
            print 'Finished Loading Modules in %s seconds' % (time.time() - start_time)
        self.user_config = UserConfig().d
        if previous_path:
            self.previous_path = previous_path
            self.previous_paths = []
        else:
            self.previous_path = self.user_config['previous_path']
            self.previous_paths = self.user_config['previous_paths']
        self.filter = 'Everything'
        self.project_management = app_config()['account_info']['project_management']
        self.user_info = ''
        self.user_email = ''
        self.user_name = ''
        self.company = ''
        self.setCentralWidget(CGLumberjackWidget(self, project_management=self.project_management,
                                                 user_email=user_info['login'],
                                                 company=self.company,
                                                 path=self.previous_path,
                                                 radio_filter=self.filter,
                                                 show_import=show_import))
        if user_info['first']:
            self.setWindowTitle('Lumbermill - Logged in as %s' % user_info['first'])
        else:
            self.setWindowTitle('Lumbermill - Logged in as %s' % user_info['login'])
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
        login = QtWidgets.QAction('login', self)
        time_tracking = QtWidgets.QAction('time', self)
        proj_man = QtWidgets.QAction('%s' % self.project_management, self)
        update_button = QtWidgets.QAction('Check For Updates', self)
        report_bug_button = QtWidgets.QAction('Report Bug', self)
        request_feature_button = QtWidgets.QAction('Request Feature', self)
        tools_menu = menu_bar.addMenu('&Tools')
        if self.project_management != 'lumbermill':
            self.proj_man_link = two_bar.addAction(proj_man)
        self.login_menu = two_bar.addAction(login)
        two_bar.addAction(time_tracking)
        settings = QtWidgets.QAction('Settings', self)
        open_globals = QtWidgets.QAction('Go to Company Globals', self)
        open_user_globals = QtWidgets.QAction('Go to User Globals', self)
        create_project = QtWidgets.QAction('Import .csv', self)
        settings.setShortcut('Ctrl+,')
        pipeline_designer = QtWidgets.QAction('Pipeline Designer', self)

        # add actions to the file menu
        tools_menu.addAction(settings)
        tools_menu.addAction(open_globals)
        tools_menu.addAction(open_user_globals)
        tools_menu.addSeparator()
        tools_menu.addAction(create_project)
        tools_menu.addAction(pipeline_designer)
        tools_menu.addSeparator()
        tools_menu.addAction(update_button)
        tools_menu.addAction(report_bug_button)
        tools_menu.addAction(request_feature_button)
        # connect signals and slots
        open_globals.triggered.connect(self.open_company_globals)
        open_user_globals.triggered.connect(self.open_user_globals)
        create_project.triggered.connect(self.open_create_project_dialog)
        settings.triggered.connect(self.on_settings_clicked)
        pipeline_designer.triggered.connect(self.on_menu_designer_clicked)
        login.triggered.connect(self.on_login_clicked)
        proj_man.triggered.connect(self.on_proj_man_menu_clicked)
        update_button.triggered.connect(self.update_lumbermill_clicked)
        report_bug_button.triggered.connect(self.report_bug_clicked)
        request_feature_button.triggered.connect(self.feature_request_clicked)
        time_tracking.triggered.connect(self.time_tracking_clicked)

    @staticmethod
    def time_tracking_clicked():
        from cgl.ui.widgets.dialog import TimeTracker
        dialog = TimeTracker()
        dialog.exec_()
        print 'time tracking clicked'

    def update_lumbermill_clicked(self):
        process_method(self.centralWidget().progress_bar, self.do_update_check,
                       args=(self, self.centralWidget().progress_bar, True, True), text='Checking For Updates')

    @staticmethod
    def do_update_check(widget, progress_bar, show_confirmation=False, print_output=True):
        if not check_for_latest_master(print_output=print_output):
            progress_bar.hide()
            dialog = InputDialog(title='Update Lumbermill',
                                 message='There is a new version of Lumbermill Available, would you like to update?',
                                 buttons=['Cancel', 'Update'])
            dialog.exec_()
            if dialog.button == 'Update':
                update_master()
                widget.close()
        else:
            progress_bar.hide()
            if show_confirmation:
                dialog = InputDialog(title='Up to date', message='Lumbermill is up to date!')
                dialog.exec_()
                if dialog.button == 'Ok' or dialog.button == 'Cancel':
                    dialog.accept()

    def report_bug_clicked(self):
        dialog = ReportBugDialog(self)
        dialog.exec_()

    def feature_request_clicked(self):
        dialog = RequestFeatureDialog(self)
        dialog.exec_()

    def open_create_project_dialog(self):
        from cgl.ui.widgets.dialog import ProjectCreator
        dialog = ProjectCreator(self)
        dialog.exec_()

    def on_proj_man_menu_clicked(self):
        link = app_config()['project_management'][self.project_management]['api']['server_url']
        cglpath.start_url(link)

    @staticmethod
    def check_configs():
        return False

    @staticmethod
    def open_company_globals():
        logging.info(os.path.dirname(app_config()['paths']['globals']))
        cglpath.start(os.path.dirname(app_config()['paths']['globals']))

    @staticmethod
    def open_user_globals():
        logging.info(os.path.dirname(app_config()['paths']['user_globals']))
        cglpath.start(os.path.dirname(app_config()['paths']['user_globals']))

    def load_user_config(self):
        user_config = UserConfig()
        if 'd' in user_config.__dict__:
            config = user_config.d
            self.user_name = str(config['user_info']['local'])
            self.user_email = str(config['user_info'][self.project_management]['login'])
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

    @staticmethod
    def on_settings_clicked():
        print 'settings clicked'

    def on_designer_clicked(self):
        pm = app_config()['account_info']['project_management']
        def_schema = app_config()['project_management'][pm]['api']['default_schema']
        schema = app_config()['project_management'][pm]['tasks'][def_schema]
        from apps.pipeline.designer import Designer
        dialog = Designer(self, pm_tasks=schema)
        dialog.setMinimumWidth(1200)
        dialog.setMinimumHeight(500)
        dialog.exec_()

    def on_menu_designer_clicked(self):
        self.on_designer_clicked()

    def closeEvent(self, event):
        # set the current path so that it works on the load better.
        user_config = UserConfig(current_path=self.centralWidget().path_widget.text)
        user_config.update_all()

    # check the config file to see if it has a default company and a default location


def sleeper():
    time.sleep(5)


if __name__ == "__main__":
    import sys
    project_management = app_config()['account_info']['project_management']
    users = app_config()['project_management'][project_management]['users']
    app = QtWidgets.QApplication(sys.argv)
    main_window = CGLumberjack(user_info=users[current_user()])
    main_window.setWindowTitle('CG Lumberjack: Nuke')
    main_window.setAttribute(QtCore.Qt.WA_DeleteOnClose)
    main_window.show()
    app.exec_()


