from cgl.plugins.Qt import QtCore, QtGui, QtWidgets
from cgl.core.path import PathObject, CreateProductionData, get_companies, get_projects
from cgl.ui.widgets.base import LJDialog
from cgl.ui.widgets.widgets import AdvComboBox
from cgl.core.config.config import user_config
from datetime import datetime, date
from cgl.core.path import start

import glob
import os

SHOTS_LABELS = ['Animation', 'Seq Lighting', 'Lighting', 'FX', 'Comp']
ASSERTS_LABELS = ['Model', 'Rig', 'Textures', 'Shading']
LABEL_MAP = {'Animation': 'anim',
             'Seq Lighting': 'lite',
             'Lighting': 'lite',
             'FX': 'fx',
             'Comp': 'comp'}
STATUS_COLORS = {'Not Started': '#BFBFBF',
                 'In Progress': '#F3D886',
                 'Published': '#52B434'}

FILE_TYPES = {'maya': {'defaults': ['.mb', '.ma']},
              'houdini': {'defaults': ['']},
              'nuke': {'defaults': ['.nk']}}


class ScopeList(QtWidgets.QWidget):

    def __init__(self, parent=None):
        QtWidgets.QWidget.__init__(self, parent)
        self.row = QtWidgets.QHBoxLayout(self)
        self.assets = QtWidgets.QRadioButton('assets')
        self.shots = QtWidgets.QRadioButton('shots')
        self.key_label = QtWidgets.QLabel('Key: ')
        self.button_dict = {}

        self.row.addWidget(self.assets)
        self.row.addWidget(self.shots)
        self.row.addStretch(1)
        self.row.addWidget(self.key_label)
        for status in STATUS_COLORS:
            button = QtWidgets.QPushButton(status)
            button_css = 'background-color: {}'.format(STATUS_COLORS[status])
            button.setStyleSheet(button_css)
            self.button_dict[status] = button
            self.row.addWidget(button)
        self.shots.setChecked(True)


class MagicButtonWidget(QtWidgets.QWidget):
    filepath = ''
    path_object = None
    published_folder = None
    newest_version_folder = None
    newest_version_files = []
    status = 'Not Started'
    latest_date = None
    publish_date = None
    date_format = "%m-%d-%Y"
    last_updated = None
    last_published = None
    newest_version_file = None
    published_file = None
    latest_user_file = None
    latest_user_render_folder = None
    user = 'tmikota'

    def __init__(self, parent=None, button_label='Default Text', info_label=None, task=None, button_click_dict=None):
        QtWidgets.QWidget.__init__(self, parent)
        self.setContentsMargins(0, 0, 0, 0)
        self.task = task
        if info_label:
            self.filepath = info_label.filepath
            self.path_object = PathObject(self.filepath)
        self.row = QtWidgets.QHBoxLayout(self)
        self.row.setContentsMargins(0, 0, 0, 0)

        self.button = QtWidgets.QPushButton()
        # self.button.setProperty('class', 'grey_border')
        self.button.setText(button_label)

        self.set_button_look()
        self.button.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.button.customContextMenuRequested.connect(self.on_context_menu)
        # self.check_box = QtWidgets.QCheckBox()
        # self.row.addWidget(self.check_box)
        self.row.addWidget(self.button)
        self.get_published_path()
        self.get_newest_version()
        self.set_tool_tip()
        self.latest_user_context_text = 'User:       {}'.format(self.latest_user_file)
        self.latest_publish_text = 'Publish:   {}'.format(self.published_file)
        self.create_user_version_text = 'Create {} version'.format(self.user)
        self.latest_user_render_text = '{}'.format(self.latest_user_render_folder)

        button_dict = {'Open in Magic Browser': self.open_in_magic_browser,
                       'separator': None,
                       self.create_user_version_text: None,
                       'separator2': None,
                       'Source Files:': None,
                       self.latest_user_context_text: self.open_latest_user_file,
                       self.latest_publish_text: self.open_latest_publish_file,
                       'separator3': None,
                       'Render Files:': None,
                       self.latest_user_render_text: self.open_latest_user_render
                       }

        self.context_menu = QtWidgets.QMenu()
        for button in button_dict:
            if button == self.create_user_version_text:
                menu = QtWidgets.QMenu(button, self)
                self.context_menu.addMenu(menu)
                default = QtWidgets.QAction('Create Default', self)
                create_and_build = QtWidgets.QAction('Create And Auto Build', self)
                default.triggered.connect(self.create_default_file)
                create_and_build.triggered.connect(self.create_and_build_file)
                menu.addAction(default)
                menu.addAction(create_and_build)
                menu.addSeparator()
                if self.latest_user_file:
                    from_latest_user = QtWidgets.QAction('From Latest User File', self)
                    menu.addAction(from_latest_user)
                if self.published_file:
                    from_latest_publish = QtWidgets.QAction('From Latest Publish File', self)
                    menu.addAction(from_latest_publish)
            elif button == self.latest_user_render_text:
                menu = QtWidgets.QMenu(button, self)
                self.context_menu.addMenu(menu)
                open_folder = QtWidgets.QAction('Open Folder', self)
                publish_folder = QtWidgets.QAction('Publish', self)
                open_folder.triggered.connect(self.open_latest_user_render)
                publish_folder.triggered.connect(self.publish_latest_user_render)
                menu.addAction(open_folder)
                menu.addAction(publish_folder)
            elif 'separator' in button:
                self.context_menu.addSeparator()
            else:
                action = QtWidgets.QAction(button, self)
                self.context_menu.addAction(action)
                if button_dict[button]:
                    action.triggered.connect(button_dict[button])

        # self.context_menu.addSeparator()
        self.button.clicked.connect(self.button_clicked)

    def set_button_look(self):
        border_color = '#808080'
        border_px = 4
        bg_color = STATUS_COLORS[self.status]
        font_color = '#383838'
        height = 120
        width = 100
        button_css = 'background-color: {}; border: {}px solid {}; font-family: "Karmatic Arcade"; ' \
                     'font-size: 8pt; color: {};width: {}px;' \
                     'border-radius: 8px; padding: 6px;'.format(bg_color, border_px, border_color, font_color, width, height)
        self.button.setStyleSheet(button_css)

    def create_default_file(self):
        print('Creating tmikota version for task {}'.format(self.task))
        print(self.path_object.path_root)
        current = self.path_object.copy(task=self.task, user=self.user, version='000.000', resolution='high',
                                        context='source')
        next_minor = current.new_minor_version_object()
        next_minor.set_attr(filename='')
        next_minor.set_attr(ext='')
        CreateProductionData(next_minor, create_default_file=True)

        with_filepath = PathObject(next_minor.path_root).copy(set_proper_filename=True, ext='*')
        file_name = glob.glob(with_filepath.path_root)[0]
        if file_name:
            if os.path.exists(file_name):
                cmd = "cmd /c start {}".format(file_name)
                print(cmd)
                os.system(cmd)
        # self.on_task_selected(next_minor)

    def create_and_build_file(self):
        print('Creating a {} file and autobuilding'.format(self.task))

    def open_latest_user_file(self):
        if self.latest_user_file:
            print("Open: {}".format(self.latest_user_file))
            cmd = "cmd /c start {}".format(self.latest_user_file)
            os.system(cmd)

    def open_latest_user_render(self):
        if self.latest_user_render_folder:
            print("Open: {}".format(self.latest_user_render_folder))
            cmd = "cmd /c start {}".format(self.latest_user_render_folder)
            os.system(cmd)

    def publish_latest_user_render(self):
        print('Publishing {}'.format(self.latest_user_render_folder))
        render_object = PathObject(self.latest_user_render_folder).publish()
        self.latest_user_render_folder = render_object.path_root
        self.published_file = render_object.copy(context='source').path_root
        self.status = 'Published'
        self.set_button_look()


    def open_latest_publish_file(self):
        if self.published_file:
            print("Open: {}".format(self.published_file))
            cmd = "cmd /c start {}".format(self.published_file)
            os.system(cmd)

    def open_in_magic_browser(self):
        print("Opening in Magic Browser")

    def on_context_menu(self, point):
        self.context_menu.exec_(self.button.mapToGlobal(point))

    def get_published_path(self):
        if self.task:
            # if it's seq-lighting we need to set that here somehow
            published_path_object = self.path_object.copy(task=self.task, context='render', user='publish',
                                                          resolution='high', latest=True)
            if os.path.exists(published_path_object.path_root):
                raw_time = os.path.getctime(published_path_object.path_root)
                self.publish_date = datetime.fromtimestamp(raw_time).strftime(self.date_format)
                self.status = 'Published'
                self.set_button_look()
                self.published_folder = published_path_object.path_root

    def get_newest_version(self):
        latest_glob_object = self.path_object.copy(task=self.task, context='source', user='*',
                                                   resolution='high', version='*')
        versions = glob.glob(latest_glob_object.path_root)
        if versions:
            self.newest_version_files = []
            latest = 0
            latest_folder = ''
            if not self.published_folder:
                self.status = 'In Progress'
                self.set_button_look()
            for each in versions:
                raw_time = os.path.getctime(each)
                if raw_time > latest:
                    latest = raw_time
                    latest_folder = each
            self.latest_date = datetime.fromtimestamp(latest).strftime(self.date_format)
            self.newest_version_folder = latest_folder
            for f in os.listdir(latest_folder):
                _, ext = os.path.splitext(f)
                if ext in FILE_TYPES['maya']['defaults']:
                    self.newest_version_files.append(f)
            if len(self.newest_version_files) == 1:
                self.newest_version_file = os.path.join(self.newest_version_folder,
                                                        self.newest_version_files[0]).replace('\\', '/')
                if 'publish' in self.newest_version_file:
                    self.published_file = self.newest_version_file
                    glob_text = self.newest_version_file.replace('publish', '*')
                    files = glob.glob(glob_text)
                    for each in files:
                        if 'publish' not in each:
                            self.latest_user_file = each.replace('\\', '/')
                else:
                    self.latest_user_file = self.newest_version_file

                    self.latest_user_render_folder = os.path.dirname(self.latest_user_file).replace('/source/',
                                                                                                    '/render/')

            self.set_time_stuff()
        else:
            self.status = 'Not Started'
            self.set_button_look()

    def set_time_stuff(self):
        today = date.today()
        date1 = today.strftime(self.date_format)
        date2 = self.latest_date
        date3 = self.publish_date
        self.last_updated = datetime.strptime(date1, self.date_format) - \
                            datetime.strptime(date2, self.date_format)
        self.last_updated = str(self.last_updated).split(' days')[0]
        if date3:
            self.last_published = datetime.strptime(date1, self.date_format) - \
                                  datetime.strptime(date3, self.date_format)
            self.last_published = str(self.last_published).split(' days')[0]

    def set_tool_tip(self):
        tool_tip = 'Status: {}\nTask Info:\n'.format(self.status)
        if self.published_folder:
            tool_tip = "{}\nPublished File  : {} ({} days ago)".format(tool_tip, self.published_folder,
                                                                       self.last_published)
        if self.newest_version_folder:
            tool_tip = "{}\nNewest Version: {} ({} days ago)".format(tool_tip, self.newest_version_file,
                                                                     self.last_updated)
        tool_tip = "{}\n\nClick - Open Latest File\nRight Click - Show Options".format(tool_tip)
        self.button.setToolTip(tool_tip)

    def button_clicked(self):
        if self.status == 'Not Started':
            if self.latest_user_file:
                cmd = "cmd /c start {}".format(self.latest_user_file)
                os.system(cmd)
            else:
                self.create_default_file()
        else:
            if self.latest_user_file:
                cmd = "cmd /c start {}".format(self.latest_user_file)
                os.system(cmd)
            else:
                if self.newest_version_files:
                    print('\tNewest Files: {}'.format(self.newest_version_files))
                else:
                    print('Creating a new version for the current user')


class SkyView(LJDialog):
    cancel_signal = QtCore.Signal()
    button = True
    company = None
    project = None
    dict = None
    base_path_object = None
    current_scope = 'shots'

    def __init__(self, parent=None, company=None, project=None):
        """
        Frame Range Dialog.
        :param parent:
        :param title:
        :param sframe:
        :param eframe:
        :param minframe:
        :param maxframe:
        :param camera:
        :param message:
        :param both:
        """
        LJDialog.__init__(self, parent)
        self.user_config = user_config()
        self.setWindowTitle("Project View")
        layout = QtWidgets.QVBoxLayout(self)
        self.company = company
        if not self.company:
            return
        self.project = project
        if not self.project:
            return
        self.project_row = QtWidgets.QHBoxLayout()
        self.company_label = QtWidgets.QLabel("Company")
        self.project_label = QtWidgets.QLabel("Project")
        self.company_combo = AdvComboBox()
        self.project_combo = AdvComboBox()
        self.project_row.addWidget(self.company_label)
        self.project_row.addWidget(self.company_combo)
        self.project_row.addWidget(self.project_label)
        self.project_row.addWidget(self.project_combo)
        self.scope_list = ScopeList()
        self.scroll_area = QtWidgets.QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area_widget_contents = QtWidgets.QWidget()
        self.grid_layout = QtWidgets.QGridLayout(self.scroll_area_widget_contents)
        layout.addLayout(self.project_row)
        layout.addWidget(self.scope_list)
        layout.addWidget(self.scroll_area)
        #layout.addLayout(self.grid_layout)
        self.scope_changed()
        self.set_defaults()
        self.get_shots()
        self.scroll_area.setWidget(self.scroll_area_widget_contents)
        self.scope_list.assets.clicked.connect(self.scope_changed)
        self.scope_list.shots.clicked.connect(self.scope_changed)
        self.company_combo.currentIndexChanged.connect(self.on_company_selected)
        self.project_combo.currentIndexChanged.connect(self.on_project_selected)

    def scope_changed(self):
        if self.scope_list.assets.isChecked():
            self.current_scope = 'assets'
        else:
            self.current_scope = 'shots'

    def refresh(self):
        self.wipe_grid()
        self.dict = {'project': self.project,
                     'company': self.company,
                     'context': 'render',
                     'scope': self.current_scope,
                     'seq': '*',
                     'shot': '*'}
        self.base_path_object = PathObject(self.dict)
        self.get_shots()

    def get_shots(self):
        files = glob.glob(self.base_path_object.path_root)
        for i, f in enumerate(files):
            ii = i+1
            if not f.endswith('.json'):
                temp_obj = PathObject(f)
                shot_name = '{}_{}'.format(temp_obj.seq, temp_obj.shot)
                label = QtWidgets.QLabel(shot_name)
                label.filepath = f
                self.grid_layout.addWidget(label, ii, 0)
                self.add_row_buttons(ii, label)

    def add_row_buttons(self, row_number, label):
        for i, each in enumerate(LABEL_MAP):
            i += 1
            task = LABEL_MAP[each]
            button = MagicButtonWidget(button_label=each, info_label=label, task=task)
            if each == 'Seq Lighting':
                if button.path_object.shot == '0000':
                    self.grid_layout.addWidget(button, row_number, i)
            else:
                self.grid_layout.addWidget(button, row_number, i)

    def set_defaults(self):
        companies = get_companies()
        companies.insert(0, '')
        self.company_combo.clear()
        self.company_combo.addItems(companies)
        # if 'default_company' in self.user_config.keys():
        #     self.company = self.user_config['default_company']
        index = self.company_combo.findText(self.company)
        if index != -1:
            self.company_combo.setCurrentIndex(index)
            self.on_company_selected()
        else:
            self.company_combo.setCurrentIndex(0)
        # if 'default_project' in self.user_config.keys():
        #     self.project = self.user_config['default_project']
        p_index = self.project_combo.findText(self.project)
        if p_index != -1:
            self.project_combo.setCurrentIndex(p_index)
        else:
            self.project_combo.setCurrentIndex(0)
        self.dict = {'project': self.project,
                     'company': self.company,
                     'context': 'render',
                     'scope': self.current_scope,
                     'seq': '*',
                     'shot': '*'}
        self.base_path_object = PathObject(self.dict)

    def on_company_selected(self):
        company = self.company_combo.currentText()
        projects = get_projects(company)
        self.company = company
        projects.insert(0, '')
        self.project_combo.clear()
        self.project_combo.addItems(projects)

    def on_project_selected(self):
        self.project = self.project_combo.currentText()
        self.refresh()

    def wipe_grid(self):
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            widget = item.widget()
            # if widget has some id attributes you need to
            # save in a list to maintain order, you can do that here
            # i.e.:   aList.append(widget.someId)
            widget.deleteLater()
        self.add_labels()

    def add_labels(self):
        if self.current_scope == 'shots':
            for i, key in enumerate(LABEL_MAP):
                self.grid_layout.addWidget(QtWidgets.QLabel(key), 0, i+1)


if __name__ == "__main__":
    from cgl.ui.startup import do_gui_init
    app = do_gui_init()
    mw = SkyView(company='VFX', project='02BTH_2021_Kish')
    mw.show()
    mw.raise_()
    app.exec_()


