import time
import os
import re
import logging
from cgl.plugins.Qt import QtCore, QtGui, QtWidgets
from cgl.ui.widgets.progress_gif import ProgressGif, process_method
from cgl.ui.widgets.search import LJSearchEdit
from cgl.ui.widgets.base import LJMainWindow
from cgl.ui.widgets.dialog import LoginDialog, InputDialog
from cgl.ui.widgets.widgets import AdvComboBox
import cgl.core.path as cglpath
from cgl.core.config.config import ProjectConfig, check_for_latest_master, update_master, paths,\
    get_user_config_file, get_root, user_config
from cgl.core.utils.general import current_user, launch_lumber_watch, save_json
from cgl.core.config.config import ProjectConfig, paths
from cgl.apps.magic_browser.elements.panels import ProjectPanel, ProductionPanel, ScopePanel, TaskPanel
from cgl.apps.magic_browser.elements.FilesPanel import FilesPanel
from cgl.ui.widgets.help import ReportBugDialog, RequestFeatureDialog
# import cgl.plugins.syncthing.utils as st_utils

try:
    import apps.magic_browser.elements.IOPanel as IoP
    DO_IOP = True
except ImportError:
    IoP = None
    DO_IOP = False

ICON_WIDTH = 24


class FunctionRow(QtWidgets.QFrame):
    def __init__(self, parent=None):
        QtWidgets.QFrame.__init__(self, parent)

        layout = QtWidgets.QHBoxLayout(self)
        sync_button = QtWidgets.QToolButton()
        render_label = QtWidgets.QLabel('Render: ')
        self.render_local = QtWidgets.QRadioButton("Local")
        # TODO - this needs to be something in the globals
        self.render_farm = QtWidgets.QRadioButton("Smedge")
        self.sync_state = False

        layout.addStretch(1)
        layout.addWidget(sync_button)
        layout.addWidget(render_label)
        layout.addWidget(self.render_local)
        layout.addWidget(self.render_farm)

        sync_button.clicked.connect(self.on_sync_clicked)
        self.render_local.clicked.connect(self.on_render_clicked)
        self.render_farm.clicked.connect(self.on_render_clicked)

    def on_render_clicked(self):
        if self.render_local.isChecked():
            logging.debug('local rendering')
        elif self.render_farm.isChecked():
            logging.debug('farm rendering')

    def on_sync_clicked(self):
        logging.debug('sync clicked')
        # TODO - see if syncthing is running currently
        # see if lumberwatch is currently running


class PathWidget(QtWidgets.QFrame):

    def __init__(self, parent=None, path_object=None, cfg=None):
        QtWidgets.QFrame.__init__(self, parent)
        if path_object.path_root:
            self.path_object = cglpath.PathObject(path_object, cfg)
            self.path_root = self.path_object.path_root
        else:
            return
        layout = QtWidgets.QHBoxLayout(self)
        self.path_line_edit = QtWidgets.QLineEdit()
        self.path_line_edit.setMinimumHeight(ICON_WIDTH)
        self.view_button = QtWidgets.QToolButton()
        self.view_button.setText('^')
        self.text = self.path_object.path_root
        layout.addWidget(self.path_line_edit)
        layout.addWidget(self.view_button)

        # add css
        self.setProperty('class', 'light_grey')
        self.path_line_edit.setProperty('class', 'medium_grey')
        # self.path_line_edit.setObjectName('display_path')
        self.view_button.clicked.connect(self.go_to_path)

    def go_to_path(self):
        path = self.path_line_edit.text()
        cglpath.show_in_folder(path)

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

    def __init__(self, parent=None, path_object=None, cfg=None, label_widget=None):
        QtWidgets.QFrame.__init__(self, parent)
        if path_object:
            self.path_object = path_object
        else:
            return
        if not cfg:
            print('NavigationWidget')
            self.cfg = ProjectConfig(self.path_object)
        else:
            self.cfg = cfg
        self.label_widget = label_widget

        self.setProperty('class', 'light_grey')
        self.my_tasks_button = QtWidgets.QPushButton()
        self.my_tasks_button.setToolTip('My Tasks')
        tasks_icon = os.path.join(self.cfg.icon_path('star24px.png'))
        self.my_tasks_button.setProperty('class', 'grey_border')
        self.my_tasks_button.setIcon(QtGui.QIcon(tasks_icon))
        self.my_tasks_button.setIconSize(QtCore.QSize(ICON_WIDTH, ICON_WIDTH))

        self.refresh_button = QtWidgets.QPushButton()
        self.refresh_button.setToolTip('Refresh')
        refresh_icon = os.path.join(self.cfg.icon_path('spinner11.png'))
        self.refresh_button.setProperty('class', 'grey_border')
        self.refresh_button.setIcon(QtGui.QIcon(refresh_icon))
        self.refresh_button.setIconSize(QtCore.QSize(ICON_WIDTH, ICON_WIDTH))

        self.ingest_button = QtWidgets.QPushButton()
        self.ingest_button.setToolTip('Ingest Data')
        self.ingest_button.setProperty('class', 'grey_border')
        ingest_icon = os.path.join(self.cfg.icon_path('ingest24px.png'))
        self.ingest_button.setIcon(QtGui.QIcon(ingest_icon))
        self.ingest_button.setIconSize(QtCore.QSize(ICON_WIDTH, ICON_WIDTH))

        self.sync_button = QtWidgets.QPushButton()
        self.sync_button.setToolTip('Sync Status')
        self.sync_button.setProperty('class', 'grey_border')
        sync_icon = os.path.join(self.cfg.icon_path('sync_on24px.png'))
        self.sync_button.setIcon(QtGui.QIcon(sync_icon))
        self.sync_button.setIconSize(QtCore.QSize(ICON_WIDTH, ICON_WIDTH))
        self.sync_button.installEventFilter(self)

        # sync menu
        self.sync_button.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.sync_button.customContextMenuRequested.connect(self.sync_clicked)
        self.sync_popup = QtWidgets.QMenu(self)
        self.sync_popup.addAction(QtWidgets.QAction('Sync Manager', self))
        self.sync_popup.addSeparator()
        self.sync_popup.addAction(QtWidgets.QAction('Set up Server', self))
        self.sync_popup.addAction(QtWidgets.QAction('Set up Workstation', self))
        self.sync_popup.addSeparator()
        self.sync_popup.addAction(QtWidgets.QAction('Start Sync', self))
        self.sync_popup.addAction(QtWidgets.QAction('Stop Sync', self))

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

        back_icon = os.path.join(self.cfg.icon_path('back24px.png'))
        home_icon = os.path.join(self.cfg.icon_path('project24px.png'))
        company_icon = os.path.join(self.cfg.icon_path('company24px.png'))

        self.back_button.setIcon(QtGui.QIcon(back_icon))
        self.back_button.setIconSize(QtCore.QSize(ICON_WIDTH, ICON_WIDTH))
        self.companies_button.setIcon(QtGui.QIcon(company_icon))
        self.companies_button.setIconSize(QtCore.QSize(ICON_WIDTH, ICON_WIDTH))
        self.projects_button.setIcon(QtGui.QIcon(home_icon))
        self.projects_button.setIconSize(QtCore.QSize(ICON_WIDTH, ICON_WIDTH))
        self.current_location_line_edit = QtWidgets.QLineEdit()
        self.current_location_line_edit.setReadOnly(True)
        self.current_location_line_edit.setMinimumHeight(ICON_WIDTH * 1.28)
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
        self.cl_row.addWidget(self.sync_button)

        layout.addLayout(self.cl_row)
        layout.addWidget(self.current_location_line_edit)

        self.my_tasks_button.clicked.connect(self.my_tasks_pressed)
        self.ingest_button.clicked.connect(self.ingest_clicked)
        # self.sync_button.clicked.connect(self.sync_clicked)
        self.refresh_button.clicked.connect(self.refresh_clicked)
        self.back_button.clicked.connect(self.back_button_pressed)
        self.companies_button.clicked.connect(self.buttons_pressed)
        self.projects_button.clicked.connect(self.buttons_pressed)
        self.set_text(self.path_object.path_root)

    def eventFilter(self, widget, event):
        if widget == self.sync_button and isinstance(event,QtGui.QMouseEvent) and event.buttons() & QtCore.Qt.LeftButton:
            self.leftClicked(event.pos())
            return True
        return False

    def leftClicked(self, pos):
        parentPosition = self.sync_button.mapToGlobal(QtCore.QPoint(0, 0))
        menuPosition = parentPosition + pos

        self.sync_popup.move(menuPosition)
        self.sync_popup.show()

    def sync_clicked(self, point):
        self.sync_popup.exec_(self.sync_button.mapToGlobal(point))
        # update the icon instead of the menu name on the other things.

    def refresh_clicked(self):
        self.refresh_button_clicked.emit(self.path_object)

    def text(self):
        return self.current_location_line_edit.text()

    def set_text(self, text):
        if text:
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
        # self.shots_button.hide()
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
        if not path_object.branch:
            self.label_widget.hide_branch()
            print('\t project: {}'.format(path_object.project))
            if path_object.project != '*' and path_object.project:
                self.label_widget.show_branch()

        else:
            print('this')
            self.label_widget.show_branch()

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
            logging.debug('Please Choose a Company and a Project before pushing the ingest button')

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


class LocationWidget(QtWidgets.QWidget):

    def __init__(self, parent=None, path_object=None):
        QtWidgets.QWidget.__init__(self, parent)
        self.path_object = path_object
        self.label_row = QtWidgets.QHBoxLayout(self)
        self.current_project_label = QtWidgets.QLabel()
        self.current_project_label.setProperty('class', 'xlarge')
        self.branch_label = QtWidgets.QLabel('Branch:')
        self.branch_combo = AdvComboBox()
        branches = path_object.get_branches()
        self.branch_combo.addItem('New Branch')
        self.branch_combo.insertSeparator(1)
        self.branch_combo.addItems(branches)
        index = self.branch_combo.findText(self.path_object.branch)
        if index != -1:
            self.branch_combo.setCurrentIndex(index)
        self.label_row.addWidget(self.current_project_label)
        self.label_row.addStretch(1)
        self.label_row.addWidget(self.branch_label)
        self.label_row.addWidget(self.branch_combo)
        self.path_changed(self.path_object)
        self.branch_combo.currentIndexChanged.connect(self.branch_changed)
        self.new_live = True

    def reload(self, path_object, branch):
        self.new_live = False
        self.path_object = path_object
        self.branch_combo.clear()
        branches = path_object.get_branches()
        self.branch_combo.addItem('New Branch')
        self.branch_combo.insertSeparator(1)
        self.branch_combo.addItems(branches)
        print('88888', branch)
        index = self.branch_combo.findText(branch)
        if index != -1:
            self.branch_combo.setCurrentIndex(index)

    def hide_branch(self):
        self.branch_combo.hide()
        self.branch_label.hide()

    def show_branch(self):
        self.branch_combo.show()
        self.branch_label.show()

    def branch_changed(self):
        cfg = ProjectConfig(self.path_object)
        if self.branch_combo.currentText() == 'New Branch':
            if self.new_live:
                new_branch = self.create_project_branch()
        else:
            new_branch = self.branch_combo.currentText()
            self.path_object.set_attr(branch=new_branch)
            # TODO - refresh the widget
        if self.new_live:
            cfg.edit_user_config(['default_branch', self.path_object.company, self.path_object.project],
                                 new_branch)

    def create_project_branch(self):
        """

        :return:
        """
        from cgl.apps.magic_browser.project_branch import CreateBranchDialog
        print('Creating a new branch for {}'.format(self.branch_combo.currentText()))
        dialog = CreateBranchDialog(self.path_object)
        dialog.exec_()
        return dialog.branch_line_edit.text()

    def path_changed(self, path_object):
        print('path_changed', path_object.path_root)
        if path_object.project:
            if path_object.branch:
                print('branch', path_object.branch)
            if path_object.shot:
                if path_object.variant == 'default' or path_object.variant == '*' or not path_object.variant:
                    shot = path_object.shot
                else:
                    shot = '{}_{}'.format(path_object.shot, path_object.variant)
                if path_object.scope == 'assets':
                    text = " {}: {}".format(path_object.project, shot)
                elif path_object.scope == 'shots':
                    text = " {}: {}_{}".format(path_object.project, path_object.seq, shot)
            else:
                text = " {}".format(path_object.project)
            self.current_project_label.setText(text)


class CGLumberjackWidget(QtWidgets.QWidget):

    def __init__(self, parent=None, project_management=None, user_email=None, company=None,
                 path=None, radio_filter=None, show_import=False, show_reference=False, default_project=None,
                 set_to_publish=False, cfg=None):
        QtWidgets.QWidget.__init__(self, parent)
        if not cfg:
            print(CGLumberjackWidget)
            self.cfg = ProjectConfig(company=company, project=default_project)
        else:
            self.cfg = cfg
        try:
            font_db = QtGui.QFontDatabase()
            font_db.addApplicationFont(os.path.join(self.cfg.app_font_folder, 'ARCADECLASSIC.TTF'))
            font_db.addApplicationFont(os.path.join(self.cfg.app_font_folder, 'ka1.ttf'))
        except AttributeError:
            logging.error('Skipping Loading Fonts from: {} '
                          '\n\t- possible Pyside2 issue'.format(self.cfg.app_font_folder))

        # Environment Stuff
        self.set_to_publish = set_to_publish
        self.show_import = show_import
        self.show_reference = show_reference
        self.user_email = user_email
        self.company = company
        self.project_management = project_management
        self.root = paths()['root']  # Company Specific
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
                self.path_object = cglpath.PathObject(path, cfg=self.cfg)
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
            if self.company:
                if default_project:
                    proj = default_project
                    scp = '*'
                    try:
                        default_branch = user_config()['default_branch'][self.company][proj]
                    except KeyError:
                        default_branch = 'master'
                else:
                    proj = '*'
                    scp = None
                d_ = {"company": self.company,
                      "root": self.root,
                      "context": 'source',
                      "project": proj,
                      "scope": scp,
                      "branch": default_branch
                      }

                self.path_object = cglpath.PathObject(d_, self.cfg)
            else:
                self.path_object = cglpath.PathObject(self.root, self.cfg)
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
        self.label_widget = LocationWidget(path_object=self.path_object)
        self.nav_widget = NavigationWidget(path_object=self.path_object, cfg=self.cfg, label_widget=self.label_widget)
        self.path_widget = PathWidget(path_object=self.path_object, cfg=self.cfg)
        self.progress_bar = ProgressGif(cfg=self.cfg)
        self.progress_bar.hide()
        # self.nav_widget.update_buttons()
        self.path_widget.update_path(path_object=self.path_object)
        self.nav_widget.location_changed.connect(self.update_location)
        self.nav_widget.refresh_button_clicked.connect(self.update_location_to_latest)
        self.nav_widget.my_tasks_clicked.connect(self.show_my_tasks)
        self.nav_widget.location_changed.connect(self.path_widget.update_path)
        self.layout.addWidget(self.nav_widget)
        self.layout.addWidget(self.label_widget)
        self.update_location(self.path_object)

    def show_my_tasks(self):
        self.path_object = cglpath.PathObject(self.path_widget.path_line_edit.text(), self.cfg)
        self.path_object.set_attr(user=current_user(), resolution='', filename='', ext='')
        self.path_object.set_attr(scope='shots', seq='*', shot=None, task=None)
        self.path_object.data['my_tasks'] = True
        self.path_widget.update_path(path_object=self.path_object)
        self.update_location(self.path_object)

    def update_location_to_latest(self, data):
        path_object = data.copy(latest=True, filename=None, ext=None)
        self.update_location(path_object)

    def update_render_location(self, data):
        logging.debug('updating the render location')

    def update_title(self):
        project = ""
        shot = ""
        if self.path_object.asset:
            if self.path_object.asset != '*':
                shot = self.path_object.asset
        if self.path_object.project:
            if self.path_object.project != '*':
                project = self.path_object.project
                self.title_label.setText(" {}: {}".format(project, shot))

    def update_location(self, data):
        self.nav_widget.search_box.setText('')
        try:
            if self.sender().force_clear:
                if self.panel:
                    self.panel.clear_layout()
                    self.panel = None
        except AttributeError:
            pass
        path_object = None
        if type(data) == dict:
            path_object = cglpath.PathObject(data, self.cfg)
        elif type(data) == cglpath.PathObject:
            path_object = cglpath.PathObject(data, self.cfg)
        if path_object.frame_range:
            self.frame_range = path_object.frame_range
        self.label_widget.path_changed(path_object)
        self.nav_widget.set_text(path_object.path_root)
        self.nav_widget.update_buttons(path_object=path_object)
        last = path_object.get_last_attr()
        seq_attrs = ['seq', 'type']
        shot_attrs = ['shot', 'asset']
        version_template = path_object.version_template
        del version_template[0:2]
        if DO_IOP:
            print(1)
            if path_object.scope == 'IO':
                if path_object.version:
                    if not self.panel:
                        self.panel = IoP.IOPanel(parent=self, path_object=path_object)
                        self.setMinimumWidth(1100)
                        self.setMinimumHeight(700)
                        self.panel.location_changed.connect(self.update_location)
                        self.panel.location_changed.connect(self.path_widget.update_path)
                        self.panel.render_location_changed.connect(self.render_location)
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
                self.panel = ProductionPanel(parent=self, path_object=path_object,
                                             search_box=self.nav_widget.search_box,
                                             my_tasks=True, cfg=self.cfg)
                if self.panel:
                    if self.panel.load_tasks():
                        self.update_panel(set_tasks_radio=True)
                        self.layout.addWidget(self.progress_bar)
                        self.layout.addWidget(self.path_widget)
                        self.path_object.data['my_tasks'] = False
                        return
                    else:
                        self.panel = None

        if last in version_template:
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
                self.panel = ProjectPanel(path_object=path_object, search_box=self.nav_widget.search_box,
                                          branch_widget=self.label_widget, cfg=self.cfg)
            else:
                self.panel = ProductionPanel(parent=self, path_object=path_object,
                                             search_box=self.nav_widget.search_box, cfg=self.cfg)
        if last == 'scope':
            if path_object.scope == '*':
                self.panel = ScopePanel(path_object=path_object, cfg=self.cfg)
            elif path_object.scope == 'IO':
                if DO_IOP:
                    self.panel = IoP.IOPanel(path_object=path_object)
            else:
                self.panel = ProductionPanel(parent=self, path_object=path_object,
                                             search_box=self.nav_widget.search_box, cfg=self.cfg)
        elif last in shot_attrs:
            if path_object.shot == '*' or path_object.asset == '*' or path_object.seq == '*' or path_object.type == '*':
                self.panel = ProductionPanel(parent=self, path_object=path_object,
                                             search_box=self.nav_widget.search_box, cfg=self.cfg)
            else:
                self.panel = TaskPanel(path_object=path_object, element='task')
                self.panel.add_button.connect(self.add_task)
        elif last in seq_attrs:
            if path_object.shot == '*' or path_object.asset == '*' or path_object.seq == '*' or path_object.type == '*':
                self.panel = ProductionPanel(parent=self, path_object=path_object,
                                             search_box=self.nav_widget.search_box, cfg=self.cfg)
        elif last == 'ingest_source':
            if DO_IOP:
                self.panel = IoP.IOPanel(path_object=path_object)
        elif last == 'task':
            if path_object.task == '*':
                self.panel = TaskPanel(path_object=path_object, element='task', cfg=self.cfg)
                self.panel.add_button.connect(self.add_task)
            else:
                self.load_files_panel(path_object)
        elif last == 'variant':
            if path_object.variant == '*':
                self.panel = TaskPanel(path_object=path_object, element='variant', cfg=self.cfg)
                self.panel.add_button.connect(self.add_task)
            else:
                self.load_files_panel(path_object)
        elif last == 'branch':
            print('last is project')
        elif last == 'company':
            self.panel = ProjectPanel(path_object=path_object, search_box=self.nav_widget.search_box, title='Companies',
                                      cfg=self.cfg)
        if self.panel:
            self.update_panel()
        self.layout.addWidget(self.progress_bar)
        self.layout.addWidget(self.path_widget)

    def update_cfg(self):
        print('update_cfg')
        self.cfg = ProjectConfig(self.path_object)

    def update_panel(self, set_tasks_radio=False):
        self.panel.location_changed.connect(self.update_location)
        if set_tasks_radio:
            self.panel.assets.tasks_radio.setChecked(True)
        self.panel.location_changed.connect(self.path_widget.update_path)

        self.layout.addWidget(self.panel)
        to_delete = []
        for i in range(self.layout.count()):
            if i == 3:
                child = self.layout.takeAt(i - 1)
                to_delete.append(child)
        for each in to_delete:
            each.widget().deleteLater()

    def add_task(self, path_object):
        logging.debug(1)
        from cgl.apps.magic_browser.elements import asset_creator
        task_mode = True
        dialog = asset_creator.AssetCreator(self, path_dict=path_object.data, task_mode=task_mode, cfg=self.cfg)
        dialog.exec_()
        self.update_location(path_object.data)

    def load_files_panel(self, path_object):
        self.panel = FilesPanel(path_object=path_object, show_import=self.show_import,
                                show_reference=self.show_reference, set_to_publish=self.set_to_publish, cfg=self.cfg)
        self.panel.open_signal.connect(self.open_clicked)
        self.panel.import_signal.connect(self.import_clicked)
        self.panel.reference_signal.connect(self.reference_clicked)
        # self.panel.new_version_signal.connect(self.new_version_clicked)
        self.panel.review_signal.connect(self.review_clicked)
        self.panel.publish_signal.connect(self.publish_clicked)
        self.panel.source_selection_changed.connect(self.set_source_selection)

    def set_source_selection(self, data):
        self.source_selection = data

    def open_clicked(self):
        if '##' in self.path_widget.path_line_edit.text():
            sequence_path = self.path_widget.path_line_edit.text()
            sequence = cglpath.Sequence(sequence_path)
            file_seq = sequence.num_sequence.split()[0]
            command = ('{} -start_number {} {}'.format(paths()['ffplay'], sequence.start_frame, file_seq))
            os.system(command)
            logging.info('Nothing set for sequences yet')
        else:
            logging.info('Opening %s' % self.path_widget.path_line_edit.text())
            cglpath.start(self.path_widget.path_line_edit.text())

    @staticmethod
    def import_clicked():
        logging.debug('import clicked')

    @staticmethod
    def reference_clicked():
        print('reference clicked')
        logging.debug('reference clicked')

    def review_clicked(self):

        selection = cglpath.PathObject(self.path_widget.path_line_edit.text(), self.cfg)
        if not os.path.exists(selection.preview_path):
            selection.set_file_type()
            process_method(self.progress_bar, self.do_review,
                           args=(self.progress_bar, selection),
                           text='Submitting Review')
            logging.debug('updating_location %s %s' % (selection.path_root, selection.data))
            self.update_location(data=selection.data)
        else:

            dialog = InputDialog(title='Preview Exists', message='Review Exists, version up to create new one')

            dialog.exec_()

    @staticmethod
    def do_review(progress_bar, path_object):
        from cgl.core.project import do_review
        do_review(progress_bar, path_object)

    def publish_clicked(self):
        logging.debug(3)
        from cgl.plugins.preflight.launch import launch_
        from cgl.ui.widgets.publish_dialog import PublishDialog
        selection = cglpath.PathObject(self.path_widget.path_line_edit.text(), self.cfg)
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
    def __init__(self, show_import=False, user_info=None, start_time=None, previous_path=None, sync_enabled=True,
                 cfg=None):
        LJMainWindow.__init__(self)

        if start_time:
            logging.debug('Finished Loading Magic Browser in %s seconds' % (time.time() - start_time))
        if cfg:
            self.cfg = cfg
        else:
            print('Dont know company and project')
            self.cfg = ProjectConfig()  # we don't know the company or project at this stage.
        self.user_config = self.cfg.user_config

        self.previous_path = previous_path
        self.filter = 'Everything'
        self.project_management = self.cfg.project_config['account_info']['project_management']
        self.user_info = ''
        self.user_email = ''
        if user_info:
            self.user_info = user_info
            if user_info['login']:
                self.user_email = user_info['login']
        self.user_name = ''
        if 'default_company' in self.user_config.keys():
            self.company = self.user_config['default_company']
        else:
            self.company = ''
        if 'default_project' in self.user_config.keys():
            self.project = self.user_config['default_project']
        else:
            self.project = None
        self.cfg = ProjectConfig(company=self.company, project=self.project)
        self.pd_menus = {}
        self.menu_dict = {}
        self.menus = {}
        self.previous_path = os.path.join(get_root(), '*')
        self.setCentralWidget(CGLumberjackWidget(self, project_management=self.project_management,
                                                 user_email=self.user_info,
                                                 company=self.company,
                                                 default_project=self.project,
                                                 radio_filter=self.filter,
                                                 show_import=show_import,
                                                 cfg=self.cfg))
        if user_info:
            if user_info['first']:
                self.setWindowTitle('Magic Browser - Logged in as %s' % user_info['first'])
            else:
                self.setWindowTitle('Magic Browser - Logged in as %s' % user_info['login'])
        self.status_bar = QtWidgets.QStatusBar()
        self.setStatusBar(self.status_bar)

        # Load Style Sheet and set up Styles:
        w = 400
        h = 500

        self.resize(w, h)
        self.menu_bar = self.menuBar()
        self.two_bar = self.menuBar()
        icon = QtGui.QPixmap(":/images/lumberjack.24px.png").scaled(24, 24)
        self.setWindowIcon(icon)
        self.load_syncthing = True
        login = QtWidgets.QAction('login', self)
        time_tracking = QtWidgets.QAction('time', self)
        proj_man = QtWidgets.QAction('%s' % self.project_management, self)
        update_button = QtWidgets.QAction('Check For Updates', self)
        report_bug_button = QtWidgets.QAction('Report Bug', self)
        request_feature_button = QtWidgets.QAction('Request Feature', self)
        tools_menu = self.menu_bar.addMenu('&Tools')
        self.sync_menu = self.menu_bar.addMenu('&Sync')
        if self.project_management != 'magic_browser':
            self.proj_man_link = self.two_bar.addAction(proj_man)
        self.login_menu = self.two_bar.addAction(login)
        self.two_bar.addAction(time_tracking)
        settings = QtWidgets.QAction('Settings', self)
        open_globals = QtWidgets.QAction('Go to Project Globals', self)
        open_user_globals = QtWidgets.QAction('Go to User Globals', self)
        open_default_files = QtWidgets.QAction("Go to Default Files", self)
        create_project = QtWidgets.QAction('Import .csv', self)
        settings.setShortcut('Ctrl+,')
        alchemy_cookbook = QtWidgets.QAction("Alchemist's Cookbook", self)
        set_up_sync_thing_server = QtWidgets.QAction('Set up Server', self)
        set_up_sync_thing_workstation = QtWidgets.QAction('Set Up Workstation', self)
        # check_machines_action = QtWidgets.QAction('Check for new Machines', self)
        # add_machines_to_folders = QtWidgets.QAction('Share Folders With Machines', self)
        # pull_from_server = QtWidgets.QAction('Pull from Server', self)
        manage_sharing_action = QtWidgets.QAction('Share Files', self)
        launch_syncthing = QtWidgets.QAction('Start Syncing', self)
        kill_syncthing = QtWidgets.QAction('Stop Syncing', self)
        show_sync_thing_browser = QtWidgets.QAction('Debug Mode', self)
        self.auto_launch_setting = QtWidgets.QAction('Auto-Launch: Off', self)
        self.current_processing_method = QtWidgets.QMenu('Processing Method: Local', self)
        change_to_local = QtWidgets.QAction('Set to Local', self)
        change_to_smedge = QtWidgets.QAction('Set to Smedge', self)
        change_to_deadline = QtWidgets.QAction('Set to Deadline', self)
        lumberwatch_launch = QtWidgets.QAction('Start Sync', self)
        # fix_paths = QtWidgets.QAction('Fix File Paths', self)

        # add actions to the file menu
        tools_menu.addAction(alchemy_cookbook)
        tools_menu.addSeparator()
        tools_menu.addAction(settings)
        tools_menu.addAction(open_globals)
        tools_menu.addAction(open_user_globals)
        tools_menu.addAction(open_default_files)
        tools_menu.addSeparator()
        tools_menu.addMenu(self.current_processing_method)
        tools_menu.addSeparator()
        tools_menu.addAction(create_project)
        tools_menu.addSeparator()
        tools_menu.addAction(update_button)
        tools_menu.addAction(report_bug_button)
        tools_menu.addAction(request_feature_button)
        # connect signals and slots

        self.current_processing_method.addAction(change_to_local)
        self.current_processing_method.addAction(change_to_smedge)
        self.current_processing_method.addAction(change_to_deadline)

        self.sync_menu.addAction(manage_sharing_action)
        self.sync_menu.addSeparator()
        self.sync_menu.addAction(set_up_sync_thing_server)
        # self.sync_menu.addAction(check_machines_action)
        # self.sync_menu.addAction(add_machines_to_folders)
        self.sync_menu.addSeparator()
        self.sync_menu.addAction(set_up_sync_thing_workstation)
        # self.sync_menu.addAction(pull_from_server)
        # self.sync_menu.addAction(fix_paths)
        self.sync_menu.addSeparator()
        #self.sync_menu.addAction(kill_syncthing)
        #self.sync_menu.addAction(launch_syncthing)
        self.sync_menu.addAction(lumberwatch_launch)
        self.sync_menu.addAction(show_sync_thing_browser)
        self.sync_menu.addSeparator()
        self.sync_menu.addAction(self.auto_launch_setting)

        # connect signals and slots
        change_to_deadline.triggered.connect(self.change_processing_method)
        change_to_local.triggered.connect(self.change_processing_method)
        change_to_smedge.triggered.connect(self.change_processing_method)
        kill_syncthing.triggered.connect(self.on_kill_syncthing)
        launch_syncthing.triggered.connect(self.on_launch_syncthing)
        lumberwatch_launch.triggered.connect(self.on_launch_lumberwatch)

        # pull_from_server.triggered.connect(self.enable_server_connection_clicked)
        # check_machines_action.triggered.connect(self.check_for_machines_clicked)
        # add_machines_to_folders.triggered.connect(self.add_machines_to_folders_clicked)
        manage_sharing_action.triggered.connect(self.manage_sharing_action_clicked)
        show_sync_thing_browser.triggered.connect(self.show_sync_details)
        self.auto_launch_setting.triggered.connect(self.toggle_auto_launch)
        set_up_sync_thing_server.triggered.connect(self.set_up_st_server_clicked)
        set_up_sync_thing_workstation.triggered.connect(self.set_up_st_workstation_clicked)
        open_globals.triggered.connect(self.open_company_globals)
        open_user_globals.triggered.connect(self.open_user_globals)
        open_default_files.triggered.connect(self.open_default_files)
        create_project.triggered.connect(self.open_create_project_dialog)
        settings.triggered.connect(self.on_settings_clicked)
        alchemy_cookbook.triggered.connect(self.on_alchemists_cookbook_clicked)
        login.triggered.connect(self.on_login_clicked)
        proj_man.triggered.connect(self.on_proj_man_menu_clicked)
        update_button.triggered.connect(self.update_lumbermill_clicked)
        report_bug_button.triggered.connect(self.report_bug_clicked)
        request_feature_button.triggered.connect(self.feature_request_clicked)
        time_tracking.triggered.connect(self.time_tracking_clicked)
        # Load any custom menus that the user has defined
        self.load_pipeline_designer_menus()
        self.set_auto_launch_text()
        self.set_processing_method_text()
        # TODO how do i run this as a background process, or a parallell process?
        # TODO - how do i grab the pid so i can close this when magic_browser closes potentially?
        if sync_enabled:
            import cgl.plugins.syncthing.utils as st_utils
            try:
                if self.cfg.user_config['sync']['syncthing']['sync_thing_url']:

                    # TODO - check for user config settings to use syncthing.
                    if "sync_thing_auto_launch" in USERself.cfg.project_config.keys():
                        try:

                            if self.cfg.user_config["sync_thing_auto_launch"] == 'True':
                                sync = False
                                st_utils.kill_syncthing()
                                if st_utils.syncthing_running():
                                    self.change_sync_icon(syncing=True)
                                    sync = True
                                else:
                                    self.change_sync_icon(syncing=False)
                                    # TODO - turn icon to not syncing
                                self.lumber_watch = launch_lumber_watch(new_window=True)
                                # TODO if syncthing is set as a feature in the globals!!!!
                                try:
                                    st_utils.launch_syncthing()
                                    self.change_sync_icon(syncing=True)
                                except:
                                    # this is a WindowsError - which doesn't seem to allow me to use in the except clause
                                    logging.debug('Sync Thing Not Found, run "Setup Workstation" to start using it.')
                            else:
                                self.load_syncthing = False
                                self.change_sync_icon(syncing=False)
                                logging.debug('sync_thing_auto_launch set to False, skipping launch')
                        except ModuleNotFoundError:
                            logging.info('problem launching syncthing - main.py line 800')
                    else:
                        self.load_syncthing = False
                        self.change_sync_icon(syncing=False)
                        self.cfg.user_config["sync_thing_auto_launch"] = False
                        self.cfg.user_config["sync_thing_machine_type"] = ""
                        logging.debug('Syncthing Auto Launch setting not set in globals.  Skipping sync operations')

            except KeyError:
                logging.debug('Skipping, Syncthing Not Set up')

    def set_processing_method_text(self, method=None):
        if not method:
            method = self.cfg.user_config['methodology']
        self.current_processing_method.setTitle('Processing Method: %s' % method.title())

    def change_processing_method(self):
        if 'Local' in self.sender().text():
            logging.debug('Changing to Local')
            method = 'Local'
        elif 'Smedge' in self.sender().text():
            logging.debug('Changing to Smedge')
            method = "Smedge"
        elif 'Deadline' in self.sender().text():
            logging.debug('Changing to Deadline')
            method = "Deadline"
        else:
            return
        self.cfg.edit_user_config(['methodology'], method.lower())
        self.set_processing_method_text(method)

    def change_sync_icon(self, syncing=True):
        # ss = QtCore.QString("QMenu { background: black; color: red }")
        # TODO - can i change menu title color?
        # TODO - can i add an icon to the menu instead of a title?
        # self.sync_menu.setStyleSheet(ss)
        sync_button = self.centralWidget().nav_widget.sync_button
        if syncing:
            logging.debug('setting sync icon to sync_on')
            sync_icon = os.path.join(self.cfg.icon_path('sync_on24px.png'))
            logging.debug(sync_icon)
        else:
            logging.debug('setting sync icon to sync_off')
            sync_icon = os.path.join(self.cfg.icon_path('sync_off24px.png'))
            logging.debug(sync_icon)
        sync_button.setIcon(QtGui.QIcon(sync_icon))
        sync_button.setIconSize(QtCore.QSize(ICON_WIDTH, ICON_WIDTH))

    def on_kill_syncthing(self):
        self.change_sync_icon(syncing=False)
        logging.debug('Killing Sync Thing')
        st_utils.kill_syncthing()

    def on_launch_syncthing(self):
        self.change_sync_icon(syncing=True)
        logging.debug('Starting Sync Thing')
        st_utils.launch_syncthing()

    def on_launch_lumberwatch(self):
        self.lumber_watch = launch_lumber_watch(new_window=True)

    def enable_server_connection_clicked(self):
        """
        connects an artist's machine to the server after the server has added them
        :return:
        """
        st_utils.process_st_config()
        self.change_sync_icon(syncing=True)
        pass

    def check_for_machines_clicked(self):
        st_utils.update_machines()
        self.change_sync_icon(syncing=True)
        pass

    def add_machines_to_folders_clicked(self):
        st_utils.update_machines()
        self.change_sync_icon(syncing=True)
        pass

    def manage_sharing_action_clicked(self):
        """
        opens a dialog where use chooses who they want to share with
        and which tasks they want to share.
        :return:
        """
        path_object = self.centralWidget().path_widget.path_object
        import cgl.plugins.syncthing.utils as st_utils
        share_mode = 'full'
        if share_mode == 'full':
            print('Full Sync Mode - sync from Projects>Project>Share Project')
        else:
            st_utils.share_files(path_object)
        # except NameError:
        # print("This machine is not set up for syncing!")

    def set_auto_launch_text(self):
        """
        reads syncthing_auto_launch setting from globals and sets text accordingly.
        :return:
        """
        if "sync_thing_auto_launch" in self.cfg.user_config.keys():
            if self.cfg.user_config["sync_thing_auto_launch"] == 'True':
                self.auto_launch_setting.setText('Auto-Launch: On')
            else:
                self.auto_launch_setting.setText('Auto-Launch: Off')

    def toggle_auto_launch(self):
        """
        Turns Auto-Launch of Lumberwatch/Syncthing on/off by toggling.
        :return:
        """
        if "sync_thing_auto_launch" in self.cfg.user_config.keys():
            if self.cfg.user_config["sync_thing_auto_launch"] == 'True':
                self.cfg.user_config["sync_thing_auto_launch"] = 'False'
                save_json(user_config(), self.cfg.user_config)
                logging.debug('Setting Auto Launch of LumberSync Off - Restart to see effects')
            else:
                self.cfg.user_config["sync_thing_auto_launch"] = 'True'
                save_json(self.cfg.user_config_file, self.cfg.user_config)
                logging.debug('Setting Auto Launch of LumberSync On - Restart to see effects')
        self.set_auto_launch_text()

    @staticmethod
    def show_sync_details():
        """
        shows the syncthing web gui
        :return:
        """
        import cgl.plugins.syncthing.utils as st_utils
        st_utils.kill_syncthing()
        st_utils.launch_syncthing(verbose=True)

    def set_up_st_server_clicked(self):
        """
        setups up server using client.json file from aws folder of the company's name, and a Google Sheets file that
        keeps track of all machines being used.
        :return:
        """
        dialog = InputDialog(title='Attention',
                             message='Setting up Server will wipe all syncing information, you sure?')
        dialog.exec_()
        if dialog.button == 'Ok':
            import cgl.plugins.syncthing.utils as st_utils
            st_utils.setup_server()
            self.change_sync_icon(syncing=True)

    def set_up_st_workstation_clicked(self):
        """
        Set up the local workstation to work with sync thing and register local workstation to the sheets file.
        :return:
        """
        dialog = InputDialog(title='Attention',
                             message='Setting up Workstation will wipe all syncing information, you sure?')
        dialog.exec_()
        if dialog.button == 'Ok':
            import cgl.plugins.syncthing.utils as st_utils
            st_utils.setup_workstation()
            self.change_sync_icon(syncing=True)

    def load_pipeline_designer_menus(self):
        import json
        #
        menus_json = os.path.join(self.cfg.cookbook_folder, 'magic_browser', 'menus.cgl')
        if os.path.exists(menus_json):
            with open(menus_json, 'r') as stream:
                self.pd_menus = json.load(stream)['magic_browser']
                software_menus = self.order_menus(self.pd_menus)
                if software_menus:
                    for menu in software_menus:
                        _menu = self.create_menu(menu)
                        self.menu_dict[menu] = _menu
                        buttons = self.order_buttons(menu)
                        self.add_menu_buttons(menu, buttons)
                else:                    logging.debug('No Menus Found')
        else:
            logging.debug('No menu file found!')
        pass

    @staticmethod
    def order_menus(menus):
        """
        Orders the Menus from the json file correctly.  This is necessary for the menus to show up in the correct
        order within the interface.
        :return:
        """
        for menu in menus:
            menus[menu]['order'] = menus[menu].get('order', 10)

        if menus:
            return sorted(menus, key=lambda key: menus[key]['order'])

    def create_menu(self, menu):
        menu_object = self.menu_bar.addMenu(menu)
        return menu_object

    def add_menu_buttons(self, menu, buttons):
        for button in buttons:
            label = self.pd_menus[menu][button]['label']
            if 'icon' in self.pd_menus[menu][button].keys():
                icon_file = self.pd_menus[menu][button]['icon']
                if icon_file:
                    label = ''
            else:
                icon_file = ''

            if 'annotation' in self.pd_menus[menu][button].keys():
                annotation = self.pd_menus[menu][button]['annotation']
            else:
                annotation = ''
            self.add_button(menu, label=self.pd_menus[menu][button]['label'],
                            annotation=annotation,
                            command=self.pd_menus[menu][button]['module'],
                            icon=icon_file,
                            image_overlay_label=label)

    def add_button(self, menu, label='', annotation='', command='', icon='', image_overlay_label='', hot_key=''):
        module = command.split()[1]
        module_name = module.split('.')[-1]
        try:
            try:
                # Python 2.7
                loaded_module = __import__(module, globals(), locals(), module_name, -1)
            except ValueError:
                import importlib
                # Python 3.0
                loaded_module = importlib.import_module(module, module_name)
            action = QtWidgets.QAction(label, self)
            self.menu_dict[menu].addAction(action)
            function = getattr(loaded_module, 'run')
            action.triggered.connect(lambda: function(self.centralWidget()))
        except ImportError:
            pass
        pass

    def order_buttons(self, menu):
        """
        orders the buttons correctly within a menu.
        :param menu:
        :return:
        """
        buttons = self.pd_menus[menu]
        buttons.pop('order')
        try:
            # there is something weird about this - as soon as these are removed "shelves" never reinitializes
            buttons.pop('active')
        except KeyError:
            pass
        for button in buttons:
            if button:
                buttons[button]['order'] = buttons[button].get('order', 10)
        if buttons:
            return sorted(buttons, key=lambda key: buttons[key]['order'])
        else:
            return {}

    @staticmethod
    def time_tracking_clicked():
        from cgl.ui.widgets.dialog import TimeTracker
        dialog = TimeTracker()
        dialog.exec_()
        logging.debug('time tracking clicked')

    def update_lumbermill_clicked(self):
        process_method(self.centralWidget().progress_bar, self.do_update_check,
                       args=(self, self.centralWidget().progress_bar), text='Checking For Updates')

    @staticmethod
    def do_update_check(widget, progress_bar):
        updated = check_for_latest_master()
        if not updated:
            update_master(widget)
        else:
            print('Lumbermill is Up to Date!')
        progress_bar.hide()

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
        link = self.cfg.project_config['project_management'][self.project_management]['api']['server_url']
        cglpath.start_url(link)

    @staticmethod
    def check_configs():
        return False

    def open_company_globals(self):
        print(self.cfg.company)
        print(self.cfg.project)
        print(self.cfg.globals_root)
        logging.debug(self.cfg.globals_root)
        cglpath.start(self.cfg.globals_root)

    @staticmethod
    def open_user_globals():
        logging.debug(os.path.dirname(get_user_config_file()))
        cglpath.start(os.path.dirname(get_user_config_file()))

    def open_default_files(self):
        location = os.path.join(self.cfg.get_cgl_resources_path(), 'default_files')
        logging.debug(location)
        cglpath.start(location)

    def load_user_config(self):
        user_config = self.cfg.user_config
        if 'd' in user_config.__dict__:
            config = user_config.d
            self.user_name = str(config['user_info']['local'])
            self.user_email = str(config['user_info'][self.project_management]['login'])
            self.company = str(config['company'])
            self.previous_path = '%s%s/source/%s' % (paths()['root'], self.company, self.project)
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
        logging.debug('settings clicked')

    def on_alchemists_cookbook_clicked(self):
        from cgl.apps.cookbook.designer import Designer
        self.cfg = ProjectConfig(company=self.company, project=self.project)
        pm = self.cfg.project_config['account_info']['project_management']
        def_schema = self.cfg.project_config['project_management'][pm]['api']['default_schema']
        schema = self.cfg.project_config['project_management'][pm]['tasks'][def_schema]

        dialog = Designer(self, pm_tasks=schema, cfg=self.cfg)
        dialog.setMinimumWidth(1200)
        dialog.setMinimumHeight(500)
        dialog.exec_()


    def closeEvent(self, event):
        print('closing')
        # set the current path so that it works on the load better.
        # self.cfg.edit_user_config(['current_path'], self.centralWidget().path_widget.text)
        #user_config = UserConfig(current_path=self.centralWidget().path_widget.text)
        #user_config.update_all()

    # check the config file to see if it has a default company and a default location


def sleeper():
    time.sleep(5)


if __name__ == "__main__":
    import sys
    cfg_ = None
    root = None
    user_globals = user_config()
    root_dir = user_globals['paths']['root']
    cfg_ = ProjectConfig()
    if cfg_:
        project_management = cfg_.project_config['account_info']['project_management']
        try:
            users = cfg_.project_config['project_management'][project_management]['users']
        except:
            users = {current_user(): {}}
        app = QtWidgets.QApplication(sys.argv)
        main_window = CGLumberjack(user_info=users[current_user()], cfg=cfg_)
        main_window.setWindowTitle('CG Lumberjack: Nuke')
        main_window.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        main_window.show()
        app.exec_()


