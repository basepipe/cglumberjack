from cgl.plugins.Qt import QtCore, QtGui, QtWidgets
from cgl.core.config.config import ProjectConfig
from cgl.core.path import PathObject
from cgl.core.utils.general import load_json, cgl_copy
from cgl.ui.widgets.base import LJDialog
from cgl.ui.widgets.widgets import AdvComboBox
from cgl.apps.magic_browser.project_optimize import get_shots
import os


class CreateBranchDialog(LJDialog):

    def __init__(self, path_object):
        LJDialog.__init__(self)
        self.cfg = path_object.project_config
        self.path_object = path_object
        self.setWindowTitle('Create New Branch for {}: {}'.format(self.path_object.company, self.path_object.project))
        layout = QtWidgets.QVBoxLayout(self)

        self.user_row = QtWidgets.QHBoxLayout()
        self.user_ass_label = QtWidgets.QLabel('User Assignments')
        self.user_ass_combo = AdvComboBox()
        self.user_row.addWidget(self.user_ass_label)
        self.user_row.addWidget(self.user_ass_combo)
        self.assets_check_box = QtWidgets.QCheckBox('Assets')

        self.assets = AssetChooser(self.path_object)
        self.shots = AssetChooser(self.path_object, scope='shots')
        tabwidget = QtWidgets.QTabWidget()
        tabwidget.addTab(self.assets, "Assets")
        tabwidget.addTab(self.shots, "Shots")

        self.migrate_row = QtWidgets.QHBoxLayout()
        self.migrate_label = QtWidgets.QLabel('New Company:')
        self.migrate_line_edit = QtWidgets.QLineEdit()
        self.migrate_create_branch = QtWidgets.QPushButton('Migrate Project to New Folder Structure')
        self.migrate_row.addStretch(1)
        self.migrate_row.addWidget(self.migrate_label)
        self.migrate_row.addWidget(self.migrate_line_edit)
        self.migrate_row.addWidget(self.migrate_create_branch)

        self.button_row = QtWidgets.QHBoxLayout()
        self.branch_label = QtWidgets.QLabel('New Branch:')
        self.branch_line_edit = QtWidgets.QLineEdit()
        self.button_create_branch = QtWidgets.QPushButton('Create New Branch')
        self.button_row.addStretch(1)
        self.button_row.addWidget(self.branch_label)
        self.button_row.addWidget(self.branch_line_edit)
        self.button_row.addWidget(self.button_create_branch)
        self.assets_message = QtWidgets.QLabel("No Asset Tasks Selected for Branch")
        self.shots_message = QtWidgets.QLabel("No Shot Tasks Selected for Branch")
        self.assets_message_row = QtWidgets.QHBoxLayout()
        self.shots_message_row = QtWidgets.QHBoxLayout()
        self.assets_message_row.addStretch(1)
        self.assets_message_row.addWidget(self.assets_message)
        self.shots_message_row.addStretch(1)
        self.shots_message_row.addWidget(self.shots_message)

        # layout.addLayout(self.user_row)
        layout.addWidget(tabwidget)
        layout.addLayout(self.assets_message_row)
        layout.addLayout(self.shots_message_row)
        layout.addLayout(self.migrate_row)
        layout.addLayout(self.button_row)

        self.assets.task_clicked.connect(self.update_count)
        self.shots.task_clicked.connect(self.update_count)
        self.migrate_create_branch.clicked.connect(self.on_migrate_branch_clicked)
        self.button_create_branch.clicked.connect(self.on_create_branch_clicked)
        #layout.addWidget(self.assets)

    def update_count(self):
        self.asset_task_count = len(self.assets.selected_tasks)
        self.shot_task_count = len(self.shots.selected_tasks)
        self.assets_message.setText("{} Asset Tasks Selected for Branch".format(self.asset_task_count))
        self.shots_message.setText("{} Shot Tasks Selected for Branch".format(self.shot_task_count))

    def asset_task_clicked(self):
        print(self.assets.selected_tasks)
        self.update_count()

    def shot_task_clicked(self):
        print(self.shots.selected_tasks)
        self.update_count()

    def on_create_branch_clicked(self):
        for task in self.assets.selected_tasks:
            render_path, source_path = self.new_branch_path(task)
            if os.path.exists(task.render_path):
                # print('Copying {} to {}'.format(task.render_path, render_path))
                cgl_copy(task.render_path, render_path, verbose=True)
            if os.path.exists(task.source_path):
                # print('Copying {} to {}'.format(task.source_path, source_path))
                cgl_copy(task.source_path, source_path, verbose=True)
        for task in self.shots.selected_tasks:
            render_path, source_path = self.new_branch_path(task)
            if os.path.exists(task.render_path) and render_path:
                # print('Copying {} to {}'.format(task.render_path, render_path))
                cgl_copy(task.render_path, render_path, verbose=True)
            if os.path.exists(task.source_path) and render_path:
                # print('Copying {} to {}'.format(task.source_path, source_path))
                cgl_copy(task.source_path, source_path, verbose=True)
        print('Branch Creation Complete')

    def on_migrate_branch_clicked(self):
        for task in self.shots.selected_tasks:
            render_path, source_path = self.migrate_path(task)
            if os.path.exists(task.render_path):
                cgl_copy(task.render_path, render_path, verbose=True)
            if os.path.exists(task.source_path):
                cgl_copy(task.source_path, source_path, verbose=True)
        for task in self.assets.selected_tasks:
            render_path, source_path = self.migrate_path(task)
            if os.path.exists(task.render_path):
                cgl_copy(task.render_path, render_path, verbose=True)
            if os.path.exists(task.source_path):
                cgl_copy(task.source_path, source_path, verbose=True)

    def new_branch_path(self, task):
        new_branch = self.branch_line_edit.text()
        render_path = None
        source_path = None
        if new_branch:
            if os.path.exists(task.render_path):
                render_path = PathObject(task.render_path).copy(branch=new_branch).path_root
            else:
                print('{} Does Not Exist'.format(task.render_path))
                render_path = None
            if os.path.exists(task.source_path):
                source_path = PathObject(task.source_path).copy(branch=new_branch).path_root
            else:
                print('{} Does Not Exist'.format(task.source_path))
                render_path = None
            return render_path, source_path

    def migrate_path(self, task, new_branch='master'):
        render_path = None
        source_path = None
        new_company = self.migrate_line_edit.text()
        if new_company:
            project_branch = '/{}/{}/'.format(self.path_object.project, new_branch)
            task_variant = '/{}/default/'.format(task.text())
            render_path = task.render_path.replace('/{}/'.format(self.path_object.project), project_branch)
            render_path = render_path.replace(self.path_object.company, new_company)
            render_path = render_path.replace('/{}/'.format(task.text()), task_variant)
            source_path = task.source_path.replace('/{}/'.format(self.path_object.project), project_branch)
            source_path = source_path.replace(self.path_object.company, new_company)
            source_path = source_path.replace('/{}/'.format(task.text()), task_variant)
            return render_path, source_path
        else:
            print('Nothing entered into "New Company Field"')
            return None


class AssetChooser(QtWidgets.QWidget):
    task_clicked = QtCore.Signal()

    def __init__(self, path_object, scope='assets'):
        QtWidgets.QWidget.__init__(self)
        self.cfg = path_object.project_config
        self.project_msd = load_json(r'Z:\Projects\cmpa-animation\render\02BTH_2021_Kish\master\project.msd')
        self.scope = scope
        proj_man = self.cfg['account_info']['project_management']
        self.project_management = self.cfg['project_management'][proj_man]
        self.default_task_type = self.project_management['api']['default_schema']
        self.task_dict = self.project_management['tasks'][self.default_task_type]['short_to_long'][self.scope]
        self.tasks = self.task_dict.keys()
        self.selected_tasks = []
        grid = QtWidgets.QGridLayout(self)
        shots = get_shots(path_object.company, path_object.project, scope=scope)
        self.column_dict = {}
        self.row_dict = {}
        self.column_headers = []
        self.row_headers = []
        for iii, tt in enumerate(self.tasks):
            self.column_dict[tt] = []
            task_button = QtWidgets.QPushButton('All {}'.format(tt))
            task_button.clicked.connect(self.on_column_clicked)
            self.column_headers.append(task_button)
            grid.addWidget(task_button, 0, iii+1)
        for i, s in enumerate(shots):
            path_object = PathObject(s)
            if not '.' in path_object.shot:
                label = '{}_{}'.format(path_object.seq, path_object.shot)
                self.row_dict[label] = []
                row_button = QtWidgets.QPushButton(label)
                self.row_headers.append(row_button)
                row_button.clicked.connect(self.on_row_clicked)
                grid.addWidget(row_button, i+1, 0)
                for ii, t in enumerate(self.tasks):
                    check_button = QtWidgets.QCheckBox(t)
                    check_button.clicked.connect(self.on_task_clicked)
                    asset_dict = self.project_msd[path_object.scope][path_object.seq][path_object.shot]
                    if t in asset_dict.keys():
                        task_dict = asset_dict[t]['publish']
                        check_button.msd = task_dict['render']['msd']
                        check_button.source_path = task_dict['source']['folder']
                        check_button.render_path = task_dict['render']['folder']
                        if not check_button.render_path:
                            pass
                            check_button.hide()
                        else:
                            self.column_dict[t].append(check_button)
                            self.row_dict[label].append(check_button)
                    else:
                        check_button.hide()
                    grid.addWidget(check_button, i+1, ii+1)
        self.hide_empty_columns()

    def hide_empty_columns(self):
        for task in self.column_dict:
            if not self.column_dict[task]:
                # find which button
                for button in self.column_headers:
                    if str(task) in button.text():
                        button.hide()

    def on_column_clicked(self):
        text = self.sender().text()
        text = text.replace('All ', '')
        for each in self.column_dict[text]:
            if each.isChecked():
                state = False
            else:
                state = True
            each.setChecked(state)
            self.process_check_boxes(each)
        self.task_clicked.emit()

    def on_row_clicked(self):
        text = self.sender().text()
        for each in self.row_dict[text]:
            if each.isChecked():
                state = False
            else:
                state = True
            each.setChecked(state)
            self.process_check_boxes(each)
        self.task_clicked.emit()

    def on_task_clicked(self):
        if self.sender().isChecked():
            self.selected_tasks.append(self.sender())
        else:
            if self.sender() in self.selected_tasks:
                self.selected_tasks.remove(self.sender())
        self.task_clicked.emit()

    def process_check_boxes(self, check_box):
        if check_box.isChecked():
            self.selected_tasks.append(check_box)
        else:
            if check_box in self.selected_tasks:
                self.selected_tasks.remove(check_box)


if __name__ == "__main__":
    from cgl.ui.startup import do_gui_init
    from cgl.core.utils.general import load_style_sheet
    app = do_gui_init()
    d = {'company': 'VFX',
         'project': '02BTH_2021_Kish'}
    path_object = PathObject(d)
    mw = CreateBranchDialog(path_object)
    mw.setWindowTitle('Create New Branch for {}'.format(path_object.project))
    mw.setMinimumWidth(1200)
    mw.setMinimumHeight(500)
    mw.show()
    mw.raise_()
    style_sheet = load_style_sheet()
    app.setStyleSheet(style_sheet)
    app.exec_()


