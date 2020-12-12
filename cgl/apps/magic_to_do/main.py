from cgl.plugins.Qt import QtCore, QtGui, QtWidgets
from cgl.core.path import PathObject
from cgl.ui.widgets.base import LJDialog
from cgl.core.config import app_config, UserConfig
from datetime import datetime, date

import glob
import os

SHOTS_LABELS = ['Animation', 'Seq Lighting', 'Lighting', 'Comp']
LABEL_MAP = {'Animation': 'anim',
             'Seq Lighting': 'lite',
             'Lighting': 'lite',
             'Comp': 'comp'}
STATUS_COLORS = {'Not Started': 'grey',
                 'In Progress': 'yellow',
                 'Published': 'green'}


class ScopeList(QtWidgets.QWidget):

    def __init__(self, parent=None):
        QtWidgets.QWidget.__init__(self, parent)
        self.row = QtWidgets.QHBoxLayout(self)
        self.assets = QtWidgets.QRadioButton('assets')
        self.shots = QtWidgets.QRadioButton('shots')
        self.row.addWidget(self.assets)
        self.row.addWidget(self.shots)
        self.row.addStretch(1)
        self.shots.setChecked(True)


class MagicButtonWidget(QtWidgets.QWidget):
    filepath = ''
    path_object = None
    published_path = None
    newest_version_folder = None
    newest_version_files = None
    status = 'Not Started'
    latest_date = None
    publish_date = None
    date_format = "%m-%d-%Y"
    last_updated = None
    last_published = None

    def __init__(self, parent=None, button_label='Default Text', info_label=None, task=None):
        QtWidgets.QWidget.__init__(self, parent)

        self.task = task
        if info_label:
            self.filepath = info_label.filepath
            self.path_object = PathObject(self.filepath)
        self.row = QtWidgets.QHBoxLayout(self)
        self.check_box = QtWidgets.QCheckBox()
        self.button = QtWidgets.QPushButton()
        self.button.setText(button_label)
        self.button.setStyleSheet("background-color: {}".format(STATUS_COLORS[self.status]))
        # self.row.addWidget(self.check_box)
        self.row.addWidget(self.button)

        self.get_published_path()
        self.get_newest_version()

        self.button.clicked.connect(self.button_clicked)

    def get_published_path(self):
        if self.task:
            # if it's seq-lighting we need to set that here somehow
            published_path_object = self.path_object.copy(task=self.task, context='render', user='publish',
                                                          resolution='high', latest=True)
            if os.path.exists(published_path_object.path_root):
                raw_time = os.path.getctime(published_path_object.path_root)
                self.publish_date = datetime.fromtimestamp(raw_time).strftime(self.date_format)
                self.status = 'Published'
                self.button.setStyleSheet("background-color: {}".format(STATUS_COLORS[self.status]))
                self.published_path = published_path_object.path_root

    def get_newest_version(self):
        latest_glob_object = self.path_object.copy(task=self.task, context='source', user='*',
                                                   resolution='high', version='*')
        versions = glob.glob(latest_glob_object.path_root)
        if versions:
            latest = 0
            latest_folder = ''
            if not self.published_path:
                self.status = 'In Progress'
                self.button.setStyleSheet("background-color: {}".format(STATUS_COLORS[self.status]))
            for each in versions:
                raw_time = os.path.getctime(each)
                if raw_time > latest:
                    latest = raw_time
                    latest_folder = each
            self.latest_date = datetime.fromtimestamp(latest).strftime(self.date_format)
            self.newest_version_folder = latest_folder
            self.newest_version_files = os.listdir(latest_folder)
            self.set_time_stuff()
        else:
            self.status = 'Not Started'
            self.button.setStyleSheet("background-color: {}".format(STATUS_COLORS[self.status]))

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

    def button_clicked(self):
        print(self.task)
        print('\t{}'.format(self.published_path))
        print('\tLast Publish {} days ago'.format(self.last_published))
        print('\t{}'.format(self.newest_version_folder))
        print('\tLast updated {} days ago'.format(self.last_updated))


class MagicToDo(LJDialog):
    cancel_signal = QtCore.Signal()
    button = True
    company = None
    project = None
    dict = None
    base_path_object = None
    current_scope = 'shots'

    def __init__(self, parent=None):
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
        self.user_config = UserConfig().d
        print(self.user_config)
        self.setWindowTitle('Mystic - To Do')
        layout = QtWidgets.QVBoxLayout(self)
        self.scope_list = ScopeList()
        self.grid_layout = QtWidgets.QGridLayout()
        self.shots_labels = ['Animation', 'Seq Lighting', 'Lighting', 'Comp']
        layout.addWidget(self.scope_list)
        layout.addLayout(self.grid_layout)

        self.scope_changed()
        self.scope_list.assets.clicked.connect(self.scope_changed)
        self.scope_list.shots.clicked.connect(self.scope_changed)

    def scope_changed(self):
        self.wipe_grid()
        try:
            self.current_scope = self.sender().text()
        except AttributeError:
            pass
        self.set_defaults()
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
        for i, each in enumerate(self.shots_labels):
            i += 1
            task = LABEL_MAP[each]
            button = MagicButtonWidget(button_label=each, info_label=label, task=task)
            self.grid_layout.addWidget(button, row_number, i)

    def set_defaults(self):
        if 'default_company' in self.user_config.keys():
            self.company = self.user_config['default_company']
        else:
            self.company = ''
        if 'default_project' in self.user_config.keys():
            self.project = self.user_config['default_project']
        else:
            self.project = None
        self.dict = {'project': self.project,
                     'company': self.company,
                     'context': 'render',
                     'scope': self.current_scope,
                     'seq': '*',
                     'shot': '*'}
        self.base_path_object = PathObject(self.dict)

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
            self.grid_layout.addWidget(QtWidgets.QLabel('Shot Name'), 0, 0)
            self.grid_layout.addWidget(QtWidgets.QLabel('Animation'), 0, 1)
            self.grid_layout.addWidget(QtWidgets.QLabel('Seq Lighting'), 0, 2)
            self.grid_layout.addWidget(QtWidgets.QLabel('Lighting'), 0, 3)
            self.grid_layout.addWidget(QtWidgets.QLabel('Comp'), 0, 4)


if __name__ == "__main__":
    from cgl.ui.startup import do_gui_init
    app = do_gui_init()
    mw = MagicToDo()
    mw.show()
    mw.raise_()
    app.exec_()


