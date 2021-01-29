from cgl.plugins.Qt import QtCore, QtGui, QtWidgets
from cgl.core.path import PathObject, CreateProductionData, get_companies, get_projects
from cgl.ui.widgets.base import LJDialog
from cgl.ui.widgets.widgets import AdvComboBox
from cgl.core.config.config import user_config
from datetime import datetime, date
from cgl.core.path import start
from cgl.core.utils.general import load_json, current_user
import copy
import glob
import os

SHOTS_LABELS = ['Animation', 'Seq Lighting', 'Lighting', 'FX', 'Comp']
ASSETS_LABEL_MAP = {'Reference': "ref",
                    'Model': 'mdl',
                    'Rig': 'rig',
                    'Textures': 'tex',
                    'Shading': 'shd'}
SHOTS_LABEL_MAP = {'Layout': 'lay',
                   'Camera': 'cam',
                   'Animation': 'anim',
                     'Seq Lighting': 'lite',
                     'Lighting': 'lite',
                     'FX': 'fx',
                     'Comp': 'comp'}
LABEL_MAP = {'shots': SHOTS_LABEL_MAP,
             'assets': ASSETS_LABEL_MAP}
STATUS_COLORS = {'Not Started': '#BFBFBF',
                 'In Progress': '#F3D886',
                 'Published': '#52B434'}
FILE_TYPES = {'maya': {'defaults': ['.mb', '.ma']},
              'houdini': {'defaults': ['']},
              'nuke': {'defaults': ['.nk']}}
ROOT = user_config()['paths']['root'].replace('\\', '/')


class ScopeList(QtWidgets.QWidget):
    update_clicked = QtCore.Signal()

    def __init__(self, parent=None):
        QtWidgets.QWidget.__init__(self, parent)
        self.row = QtWidgets.QHBoxLayout(self)
        self.assets = QtWidgets.QRadioButton('assets')
        self.shots = QtWidgets.QRadioButton('shots')
        self.key_label = QtWidgets.QLabel('Key: ')
        self.button_dict = {}
        self.update_button = QtWidgets.QPushButton('Refresh')

        self.row.addWidget(self.assets)
        self.row.addWidget(self.shots)
        self.row.addWidget(self.update_button)
        self.row.addStretch(1)
        self.row.addWidget(self.key_label)
        for status in STATUS_COLORS:
            button = QtWidgets.QPushButton(status)
            button_css = 'background-color: {}'.format(STATUS_COLORS[status])
            button.setStyleSheet(button_css)
            self.button_dict[status] = button
            self.row.addWidget(button)
        self.shots.setChecked(True)


        self.update_button.clicked.connect(self.on_update_clicked)

    def on_update_clicked(self):
        self.update_clicked.emit()



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
    user = current_user()
    thumb_path = None
    preview_path = None

    def __init__(self, parent=None, button_label='Default Text', info_label=None, task=None, task_dict=None,
                 button_click_dict=None):
        QtWidgets.QWidget.__init__(self, parent)
        self.setContentsMargins(0, 0, 0, 0)
        self.task = task
        if info_label:
            self.filepath = info_label.filepath
            self.path_object = PathObject(self.filepath)
        self.row = QtWidgets.QHBoxLayout(self)
        self.row.setContentsMargins(0, 0, 0, 0)
        self.task_dict = task_dict
        self.button = QtWidgets.QPushButton()
        # self.button.setProperty('class', 'grey_border')
        self.button.setText(button_label)

        self.set_button_look()
        self.button.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.button.customContextMenuRequested.connect(self.on_context_menu)
        # self.check_box = QtWidgets.QCheckBox()
        # self.row.addWidget(self.check_box)
        self.row.addWidget(self.button)
        self.latest_user_context_text = ""
        self.latest_publish_text = ""
        self.create_user_version_text = ""
        self.latest_user_render_text = ""
        self.context_menu = QtWidgets.QMenu()

        self.process_path_dict()
        # self.context_menu.addSeparator()
        self.button.clicked.connect(self.button_clicked)

    def update_publish_msd(self):
        from cgl.plugins.maya.alchemy import cl_update_msd
        if self.published_file:
            cl_update_msd(self.published_file)

    def update_thumb(self):
        print('Updating Thumbnail')
        from cgl.plugins.maya.alchemy import cl_create_preview
        if self.published_file:
            cl_create_preview(self.published_file)

    def process_path_dict(self):
        self.get_published_path()
        self.get_newest_version()
        self.set_tool_tip()
        self.latest_user_context_text = 'User:       {}'.format(self.newest_version_file)
        self.latest_publish_text = 'Publish:   {}'.format(self.published_file)
        self.create_user_version_text = 'Create {} version'.format(self.user)
        self.latest_user_render_text = '{}'.format(self.latest_user_render_folder)

        button_dict = {'Show File Location': self.open_in_magic_browser,
                       'separator4': None,
                       'Update Publish MSD': self.update_publish_msd,
                       'Update Thumb': self.update_thumb,
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

    def set_button_look(self):
        border_color = '#808080'
        bg_color = STATUS_COLORS[self.status]
        if self.thumb_path:
            if os.path.exists(self.thumb_path):
                pixmap = QtGui.QPixmap(self.thumb_path)
                icon = QtGui.QIcon(pixmap)
                self.button.setIcon(icon)
                self.button.setIconSize(pixmap.rect().size())
                self.button.setText('')
                self.button.setMinimumWidth(pixmap.rect().size().width()+8)
                self.button.setMinimumHeight(pixmap.rect().size().height()+8)
                self.button.setMaximumWidth(pixmap.rect().size().width() + 8)
                self.button.setMaximumHeight(pixmap.rect().size().height() + 8)
                border_color = STATUS_COLORS[self.status]
                bg_color = 'black'
        border_px = 4
        font_color = '#383838'
        height = 120
        width = 100
        button_css = 'background-color: {}; border: {}px solid {}; font-family: "Karmatic Arcade"; ' \
                     'font-size: 8pt; color: {};width: {}px;' \
                     'border-radius: 8px; padding: 6px;'.format(bg_color, border_px, border_color, font_color, width, height)
        self.button.setStyleSheet(button_css)

    def create_default_file(self):
        print('Creating {} version for task {}'.format(self.user, self.task))
        current = self.path_object.copy(task=self.task, user=self.user, version='000.000', resolution='high',
                                        context='source', variant='default')
        next_minor = current.new_minor_version_object()
        next_minor.set_attr(filename='')
        next_minor.set_attr(ext='')
        CreateProductionData(next_minor, create_default_file=True)
        self.set_latest_user_file(next_minor.path_root)
        with_filepath = PathObject(next_minor.path_root).copy(set_proper_filename=True, ext='*')
        file_name = glob.glob(with_filepath.path_root)[0]
        if file_name:
            if os.path.exists(file_name):
                cmd = "cmd /c start {}".format(file_name)
                os.system(cmd)
        # self.on_task_selected(next_minor)

    def create_and_build_file(self):
        print('Creating a {} file and autobuilding'.format(self.task))

    def set_latest_user_file(self, user_file):
        self.latest_user_file = user_file
        self.set_button_look()

    def set_publish_file(self, filepath):
        self.published_file = filepath
        self.set_button_look()

    def open_latest_user_file(self):
        if self.newest_version_file:
            print("Open: {}".format(self.newest_version_file))
            cmd = "cmd /c start {}".format(self.newest_version_file)
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
        self.set_publish_file(render_object.copy(context='source').path_root)
        self.status = 'Published'
        self.set_button_look()

    def open_latest_publish_file(self):
        if self.published_file:
            print("Open: {}".format(self.published_file))
            cmd = "cmd /c start {}".format(self.published_file)
            os.system(cmd)

    def open_in_magic_browser(self):
        folder = ''
        if self.published_folder:
            folder = self.published_folder
        elif self.newest_version_file:
            folder = os.path.dirname(self.newest_version_file)
        if folder:
            cmd = "cmd /c start {}".format(folder)
            os.system(cmd)
        else:
            print('No Folder to Go to')

    def on_context_menu(self, point):
        self.context_menu.exec_(self.button.mapToGlobal(point))

    def get_published_path(self):
        if self.task_dict:
            self.published_folder = self.add_root(self.task_dict['publish']['source']['folder'])
            # raw_time = self.task_dict['publish']['source']['date']
            if self.published_folder:
                raw_time = os.path.getctime(self.published_folder)
                self.publish_date = datetime.fromtimestamp(raw_time).strftime(self.date_format)
                self.set_publish_file(self.add_root(self.task_dict['publish']['source']['source_file']))
                self.preview_path = self.add_root(self.task_dict['publish']['source']['preview_file'])
                self.thumb_path = self.add_root(self.task_dict['publish']['source']['thumb_file'])
                self.status = 'Published'
                self.set_button_look()

    def add_root(self, filepath):
        if filepath:
            new_path = '{}/{}'.format(ROOT, filepath)
            return new_path
        else:
            return ""

    def get_newest_version(self):
        if self.task_dict:

            self.newest_version_folder = self.add_root(self.task_dict['latest_user']['source']['folder'])
            self.newest_version_files = self.task_dict['latest_user']['source']['source_files']
            newest_version_file = self.add_root(self.task_dict['latest_user']['source']['source_file'])
            if not newest_version_file and self.newest_version_files:
                newest_version_file = self.add_root(self.newest_version_files[0])
            self.newest_version_file = newest_version_file
            self.latest_user_render_folder = self.add_root(self.newest_version_folder.replace('/source/', '/render/'))
            self.preview_path = self.add_root(self.task_dict['latest_user']['source']['preview_file'])
            self.thumb_path = self.add_root(self.task_dict['latest_user']['source']['thumb_file'])
            #raw_time = self.task_dict['latest_user']['source']['date']
            if self.newest_version_folder:
                raw_time = os.path.getctime(self.newest_version_folder)
                self.latest_date = datetime.fromtimestamp(raw_time).strftime(self.date_format)
                self.set_time_stuff()
                self.set_button_look()
            if self.newest_version_file:
                raw_time = os.path.getctime(self.newest_version_file)
                self.latest_date = datetime.fromtimestamp(raw_time).strftime(self.date_format)
                self.set_time_stuff()
                self.set_button_look()
            if not self.published_folder:
                self.status = 'In Progress'

    def set_time_stuff(self):
        self.last_published = 0
        self.last_updated = 0
        today = date.today()
        date1 = today.strftime(self.date_format)
        date2 = self.latest_date
        date3 = self.publish_date
        self.last_updated = datetime.strptime(date1, self.date_format) - \
                            datetime.strptime(date2, self.date_format)

        self.last_updated = str(self.last_updated).split(' day')[0]
        if self.last_updated == "0:00:00":
            self.last_updated = "0"
        if date3:
            self.last_published = datetime.strptime(date1, self.date_format) - \
                                  datetime.strptime(date3, self.date_format)
            self.last_published = str(self.last_published).split(' day')[0]
            if self.last_published == '0:00:00':
                self.last_published = '0'
        if int(self.last_published) <= int(self.last_updated):
            self.status = 'Published'
        else:
            self.status = 'In Progress'


    def set_tool_tip(self):
        tool_tip = 'Status: {}\nTask Info:\n'.format(self.status)
        if self.published_folder:
            tool_tip = "{}\nPublished File  : {} ({} days ago)".format(tool_tip, self.published_file,
                                                                       self.last_published)
        if self.newest_version_folder:
            tool_tip = "{}\nNewest Version: {} ({} days ago)".format(tool_tip, self.newest_version_file,
                                                                     self.last_updated)
        tool_tip = "{}\n\nClick - Open Latest File\nRight Click - Show Options".format(tool_tip)
        self.button.setToolTip(tool_tip)

    def button_clicked(self):
        if self.status == 'Not Started':
            if self.newest_version_file:
                print('Opening User File {}'.format(self.newest_version_file))
                cmd = "cmd /c start {}".format(self.newest_version_file)
                os.system(cmd)
            else:
                self.create_default_file()
        elif self.status == 'In Progress':
            if self.newest_version_file:
                print('Opening User File {}'.format(self.newest_version_file))
                cmd = "cmd /c start {}".format(self.newest_version_file)
                os.system(cmd)
        elif self.status == 'Published':
            if self.published_file:
                print('Opening Publish File {}'.format(self.published_file))
                cmd = "cmd /c start {}".format(self.published_file)
                os.system(cmd)


class MerlinsEyeball(LJDialog):
    cancel_signal = QtCore.Signal()
    button = True
    company = None
    project = None
    dict = None
    base_path_object = None
    current_scope = 'shots'

    def __init__(self, parent=None, company=None, project=None, branch=None):
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
        self.setMinimumWidth(1200)
        self.setMinimumHeight(800)
        layout = QtWidgets.QVBoxLayout(self)
        self.company = company
        if not self.company:
            return
        self.project = project
        if not self.project:
            return
        self.branch = branch
        if not self.branch:
            return
        self.project_row = QtWidgets.QHBoxLayout()
        self.company_label = QtWidgets.QLabel("Company")
        self.project_label = QtWidgets.QLabel("Project")
        self.branch_label = QtWidgets.QLabel("Branch")
        self.company_combo = AdvComboBox()
        self.project_combo = AdvComboBox()
        self.branch_combo = AdvComboBox()
        self.project_row.addWidget(self.company_label)
        self.project_row.addWidget(self.company_combo)
        self.project_row.addWidget(self.project_label)
        self.project_row.addWidget(self.project_combo)
        self.project_row.addWidget(self.branch_label)
        self.project_row.addWidget(self.branch_combo)
        self.scope_list = ScopeList()
        self.scroll_area = QtWidgets.QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area_widget_contents = QtWidgets.QWidget()
        self.grid_layout = QtWidgets.QGridLayout(self.scroll_area_widget_contents)
        layout.addLayout(self.project_row)
        layout.addWidget(self.scope_list)
        layout.addWidget(self.scroll_area)
        #layout.addLayout(self.grid_layout)
        self.set_defaults()

        self.scope_changed()
        self.scroll_area.setWidget(self.scroll_area_widget_contents)
        self.scope_list.assets.clicked.connect(self.scope_changed)
        self.scope_list.shots.clicked.connect(self.scope_changed)
        self.scope_list.update_clicked.connect(self.on_update_clicked)
        self.company_combo.currentIndexChanged.connect(self.on_company_selected)
        self.project_combo.currentIndexChanged.connect(self.on_project_selected)
        self.branch_combo.currentIndexChanged.connect(self.on_branch_selected)

    def on_update_clicked(self):
        self.refresh(reload=True)

    def scope_changed(self):
        if self.scope_list.assets.isChecked():
            self.current_scope = 'assets'
            print('assets clicked')
        else:
            self.current_scope = 'shots'
            print('shots clicked')
        self.refresh()
        self.get_shots()

    def refresh(self, reload=False):
        self.wipe_grid()
        self.dict = {'project': self.project,
                     'company': self.company,
                     'context': 'render',
                     'branch': self.branch,
                     'scope': self.current_scope,
                     'seq': '*',
                     'shot': '*'}
        self.base_path_object = PathObject(self.dict)
        if reload:
            import cgl.apps.merlins_eyeball.project_analyzer as pa
            pa.get_all(self.company, self.project, self.branch)
        self.project_msd = load_json(self.base_path_object.project_msd_path)
        self.get_shots()

    def get_shots(self):
        print(self.base_path_object.path_root)
        print(self.base_path_object.project_msd_path)
        if 'assets' in self.base_path_object.path_root:
            files = self.project_msd['asset_list']
        elif 'shots' in self.base_path_object.path_root:
            # files = glob.glob(self.base_path_object.path_root)
            files = self.project_msd['shot_list']
        for i, f in enumerate(files):
            f = '{}/{}'.format(ROOT, f)
            ii = i+1
            if not f.endswith('.json'):
                temp_obj = PathObject(f)
                shot_name = '{}_{}'.format(temp_obj.seq, temp_obj.shot)
                label = QtWidgets.QLabel(shot_name)
                label.filepath = f
                label.dict = self.project_msd[self.current_scope][temp_obj.seq][temp_obj.shot]
                self.grid_layout.addWidget(label, ii, 0)
                self.add_row_buttons(ii, label)

    def add_row_buttons(self, row_number, label):
        label_map = LABEL_MAP[self.current_scope]
        for i, each in enumerate(label_map):
            i += 1
            task = label_map[each]
            if task in label.dict.keys():
                task_dict = label.dict[task]
            else:
                task_dict = None
            button = MagicButtonWidget(button_label=each, info_label=label, task=task, task_dict=task_dict)
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
        p_index = self.project_combo.findText(self.project)
        if p_index != -1:
            self.project_combo.setCurrentIndex(p_index)
        else:
            self.project_combo.setCurrentIndex(0)
        self.get_branches()
        b_index = self.branch_combo.findText(self.branch)
        if b_index != -1:
            self.branch_combo.setCurrentIndex(b_index)
        else:
            self.branch_combo.setCurrentIndex(0)
        self.dict = {'project': self.project,
                     'company': self.company,
                     'branch': self.branch,
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
        print(99999)
        self.project = self.project_combo.currentText()
        self.get_branches()
        self.refresh()

    def get_branches(self):
        glob_string = '{}\{}\source\{}\*'.format(user_config()['paths']['root'], self.company, self.project)
        bs = glob.glob(glob_string)
        branches = []
        for b in bs:
            branches.append(os.path.basename(b))
        branches.insert(0, '')
        self.branch_combo.clear()
        self.branch_combo.addItems(branches)
        return branches

    def on_branch_selected(self):
        self.branch = self.branch_combo.currentText()
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
    mw = MerlinsEyeball(company='cmpa-animation', project='02BTH_2021_Kish', branch='master')
    mw.show()
    mw.raise_()
    app.exec_()


