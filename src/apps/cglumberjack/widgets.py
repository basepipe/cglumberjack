import os
import pandas as pd
import shutil
from Qt.QtCore import Qt
from Qt import QtWidgets, QtCore, QtGui
from cglcore import path
from cglcore.config import app_config
from cglui.widgets.combo import AdvComboBox
from cglui.widgets.base import LJFileBrowser
from cglui.widgets.search import LJSearchEdit
from cglui.widgets.containers.table import LJTableWidget
from cglui.widgets.containers.model import ListItemModel
from cglui.widgets.containers.menu import LJMenu


class FileTableModel(ListItemModel):
    def data(self, index, role):
        row = index.row()
        col = index.column()
        if role == Qt.DisplayRole:
            return self.data_[row][col]
        if role == Qt.DecorationRole:
            data = self.data_[row][col]
            if "." not in data:
                icon_path = os.path.join(path.icon_path(), 'folder2.png')
                return QtWidgets.QIcon(icon_path)
        # if role == Qt.ToolTipRole:
        #     return "hello tom"


class AddAssetModel(ListItemModel):
    def data(self, index, role):
        row = index.row()
        col = index.column()
        if role == Qt.DisplayRole:
            return self.data_[row][col]
        if role == Qt.DecorationRole:
            data = self.data_[row][col]
            if "." not in data:
                icon_path = os.path.join(path.icon_path(), 'folder2.png')
                return QtWidgets.QIcon(icon_path)
        # if role == Qt.ToolTipRole:
        #     return "hello tom"


class FileTable(LJTableWidget):
    files_added = QtCore.Signal(basestring)
    file_selected = QtCore.Signal(object)

    def __init__(self, parent):
        LJTableWidget.__init__(self, parent)
        self.setShowGrid(False)
        self.setAcceptDrops(True)

    def mouseReleaseEvent(self, e):
        super(FileTable, self).mouseReleaseEvent(e)
        self.row_selected()

    def dragEnterEvent(self, e):
        if e.mimeData().hasUrls:
            e.accept()
        else:
            e.ignore()

    def dragMoveEvent(self, e):
        if e.mimeData().hasUrls:
            e.setDropAction(QtCore.Qt.CopyAction)
            e.accept()
        else:
            e.ignore()

    def dropEvent(self, e):
        if e.mimeData().hasUrls:
            e.setDropAction(QtCore.Qt.CopyAction)
            e.accept()
            file_list = []
            for url in e.mimeData().urls():
                file_list.append(str(url.toLocalFile()))
            self.files_added.emit(file_list)
        else:
            print 'invalid'
            e.ignore()


class AssetWidget(QtWidgets.QWidget):
    button_clicked = QtCore.Signal(object)
    filter_changed = QtCore.Signal()

    def __init__(self, parent, title, filter_string=None):
        QtWidgets.QWidget.__init__(self, parent)
        v_layout = QtWidgets.QVBoxLayout(self)
        h_layout = QtWidgets.QHBoxLayout(self)
        self.filter_string = filter_string
        self.label = title
        self.title = QtWidgets.QLabel("<b>%s</b>" % title)
        self.message = QtWidgets.QLabel("")
        self.search_box = LJSearchEdit(self)
        self.button = QtWidgets.QToolButton()
        self.button.setText("+")
        self.data_table = LJTableWidget(self)
        self.data_table.setMinimumHeight(200)

        # this is where the filter needs to be!
        h_layout.addWidget(self.title)
        h_layout.addWidget(self.search_box)
        h_layout.addWidget(self.button)

        v_layout.addLayout(h_layout)
        v_layout.addWidget(self.message)
        v_layout.addWidget(self.data_table, 1)

        self.message.hide()
        self.button.clicked.connect(self.on_button_clicked)

    def setup(self, mdl):
        self.data_table.set_item_model(mdl)
        self.data_table.set_search_box(self.search_box)

    def on_button_clicked(self):
        data = {'title': self.label}
        self.button_clicked.emit(data)

    def set_title(self, new_title):
        self.title.setText('<b>%s</b>' % new_title.title())


class IOWidget(QtWidgets.QFrame):
    versions_changed = QtCore.Signal(object)

    def __init__(self, parent, title, path_object=None):
        QtWidgets.QFrame.__init__(self, parent)
        self.setFrameStyle(QtWidgets.QFrame.StyledPanel | QtWidgets.QFrame.Sunken)
        self.sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.Maximum)
        self.setSizePolicy(self.sizePolicy)
        widget_width = 500
        self.io_statuses = ['Ingested', 'Tagged', 'Published']

        self.path_object = path_object
        self.pandas_path = None

        v_layout = QtWidgets.QVBoxLayout()
        title_layout = QtWidgets.QHBoxLayout()

        self.label = title
        self.title = QtWidgets.QLabel("<b>%s</b>" % title.title())
        self.add_button = QtWidgets.QToolButton()
        self.add_button.setText("Create First Version")
        self.versions = QtWidgets.QComboBox()
        self.file_tree = LJFileBrowser(self)

        self.tags_title = QtWidgets.QLabel("<b>Select File(s) or Folder(s) to tag</b>")

        self.shot_radio_button = QtWidgets.QRadioButton('Shots')
        self.shot_radio_button.setChecked(True)
        self.asset_radio_button = QtWidgets.QRadioButton('Assets')
        self.radio_row = QtWidgets.QHBoxLayout()

        self.radio_row.addWidget(self.shot_radio_button)
        self.radio_row.addWidget(self.asset_radio_button)
        self.radio_row.addItem(QtWidgets.QSpacerItem(0, 0, QtWidgets.QSizePolicy.Expanding,
                                                     QtWidgets.QSizePolicy.Minimum))

        self.seq_label = QtWidgets.QLabel('Seq ')
        self.seq_combo = AdvComboBox()
        self.seq_row = QtWidgets.QHBoxLayout()
        self.seq_row.addWidget(self.seq_label)
        self.seq_row.addWidget(self.seq_combo)

        self.shot_label = QtWidgets.QLabel('Shot')
        self.shot_combo = AdvComboBox()
        self.seq_row.addWidget(self.shot_label)
        self.seq_row.addWidget(self.shot_combo)

        self.task_label = QtWidgets.QLabel('Task')
        self.task_combo = AdvComboBox()
        self.seq_row.addWidget(self.task_label)
        self.seq_row.addWidget(self.task_combo)

        self.tags_label = QtWidgets.QLabel("Tags")
        self.tags_label.setWordWrap(True)
        self.tags_label.setMaximumWidth(100)
        self.tags_line_edit = QtWidgets.QLineEdit()
        self.tags_row = QtWidgets.QHBoxLayout()
        self.tags_row.addWidget(self.tags_label)
        self.tags_row.addWidget(self.tags_line_edit)

        # create buttons row
        self.buttons_row = QtWidgets.QHBoxLayout()
        self.publish_button = QtWidgets.QPushButton('Publish Tagged')
        self.publish_button.setEnabled(False)
        self.buttons_row.addItem(QtWidgets.QSpacerItem(0, 0, QtWidgets.QSizePolicy.Expanding,
                                                        QtWidgets.QSizePolicy.Minimum))
        self.buttons_row.addWidget(self.publish_button)


        title_layout.addWidget(self.title)
        title_layout.addItem(QtWidgets.QSpacerItem(0, 0, QtWidgets.QSizePolicy.Expanding,
                                                        QtWidgets.QSizePolicy.Minimum))
        title_layout.addWidget(self.versions)
        title_layout.addWidget(self.add_button)
        self.setMinimumWidth(widget_width)

        v_layout.addLayout(title_layout)
        v_layout.addWidget(self.file_tree)
        v_layout.addWidget(self.tags_title)
        v_layout.addLayout(self.radio_row)
        v_layout.addLayout(self.seq_row)
        v_layout.addLayout(self.tags_row)
        v_layout.addLayout(self.buttons_row)
        v_layout.addItem(QtWidgets.QSpacerItem(0, 0, QtWidgets.QSizePolicy.Minimum,
                                               QtWidgets.QSizePolicy.Expanding))
        self.setLayout(v_layout)
        self.versions.currentIndexChanged.connect(self.on_version_changed)
        self.hide_tags()

        self.shot_radio_button.clicked.connect(self.on_radio_clicked)
        self.asset_radio_button.clicked.connect(self.on_radio_clicked)
        self.seq_combo.currentIndexChanged.connect(self.on_seq_changed)
        self.file_tree.initialized.connect(self.load_data_frame)
        self.seq_combo.editTextChanged.connect(self.edit_data_frame)
        self.shot_combo.editTextChanged.connect(self.edit_data_frame)
        self.task_combo.editTextChanged.connect(self.edit_data_frame)
        self.tags_line_edit.textChanged.connect(self.edit_tags)
        self.publish_button.clicked.connect(self.publish_tagged_assets)
        self.data_frame = None

    def publish_tagged_assets(self):
        for index, row in self.data_frame.iterrows():
            if row['Status'] == 'Tagged':
                print 'Copying %s to %s' % (row['Filepath'], row['Project Filepath'])
                if os.path.isfile(row['Project Filepath']):
                    dir_, file_ = os.path.split(row['Project Filepath'])
                    if not os.path.exists(row['Project Filepath']):
                        os.makedirs(dir_)
                elif os.path.isdir(row['Project Filepath']):
                    dir_ = os.path.isdir(row['Project Filepath'])
                path.CreateProductionData(dir_)
                shutil.copy2(row['Filepath'], row['Project Filepath'])
                # TODO - I need to create a .txt file in the src directory that describes the action that
                # produced these files.

    def load_data_frame(self):
        print 'initializing data frame'
        self.pandas_path = os.path.join(self.file_tree.directory, 'publish_data.csv')
        if os.path.exists(self.pandas_path):
            self.data_frame = pd.read_csv(self.pandas_path, names=["Filepath", "Tags", "Keep Client Naming",
                                                                   "Seq", "Shot", "Task", "Project Filepath", "Status"])
        else:
            data = []
            # msg = "Generating Pandas DataFrame from folder: %s" % folder
            # LOG.info(msg)
            for root, _, files in os.walk(self.file_tree.directory):
                for filename in files:
                    fullpath = os.path.join(os.path.abspath(root), filename)
                    data.append((fullpath, '', True, '', '', '', '', self.io_statuses[0]))
            self.data_frame = pd.DataFrame(data, columns=["Filepath", "Tags", "Keep Client Naming",
                                                          "Seq", "Shot", "Task",
                                                          "Project Filepath", "Status"])

    def edit_tags(self):
        files = self.file_tree.selected_items
        tags = self.tags_line_edit.text()
        if tags:
            for f in files:
                f = f.replace('/', '\\')
                row = self.data_frame.loc[self.data_frame['Filepath'] == f].index[0]
                self.data_frame.at[row, 'Tags'] = tags
            self.save_data_frame()

    def edit_data_frame(self):
        files = self.file_tree.selected_items
        if self.shot_radio_button.isChecked():
            scope = 'shots'
        elif self.asset_radio_button.isChecked():
            scope = 'assets'
        if self.seq_combo.currentText():
            seq = str(self.seq_combo.currentText())
            if self.shot_combo.currentText():
                shot = str(self.shot_combo.currentText())

                if self.task_combo.currentText():
                    try:
                        task = app_config()['pipeline_steps'][scope][str(self.task_combo.currentText())]
                        to_object = self.path_object.copy(scope=scope,
                                                          seq=seq,
                                                          shot=shot,
                                                          task=task,
                                                          context='render',
                                                          version='000.000',
                                                          user='publish',
                                                          resolution='high')
                        for f in files:
                            f = f.replace('/', '\\')
                            row = self.data_frame.loc[self.data_frame['Filepath'] == f].index[0]
                            to_path = os.path.join(to_object.path_root, os.path.split(f)[-1])
                            self.data_frame.at[row, 'Seq'] = seq
                            self.data_frame.at[row, 'Shot'] = shot
                            self.data_frame.at[row, 'Task'] = task
                            self.data_frame.at[row, 'Project Filepath'] = to_path
                            self.data_frame.at[row, 'Status'] = self.io_statuses[1]
                        self.save_data_frame()
                    except KeyError:
                        pass

    def clear_all(self):
        self.shot_combo.clear()
        self.seq_combo.clear()
        self.task_combo.clear()
        self.tags_line_edit.clear()

    def show_line_edit_info(self, data):
        self.tags_line_edit.clear()
        filepath = data[-1].replace('/', '\\')
        row = self.data_frame.loc[self.data_frame['Filepath'] == filepath].index[0]
        tags = self.data_frame.loc[row, 'Tags']
        if type(tags) != float:
            if tags:
                self.tags_line_edit.setText(tags)

    def show_combo_info(self, data):
        if data:
            print data
            filepath = data[-1].replace('/', '\\')
            row = self.data_frame.loc[self.data_frame['Filepath'] == filepath].index[0]
            seq = self.data_frame.loc[row, 'Seq']
            shot = self.data_frame.loc[row, 'Shot']
            task = self.data_frame.loc[row, 'Task']
            status = self.data_frame.loc[row, 'Status']
            self.publish_button.setEnabled(False)
            if type(seq) != float:
                if seq:
                    seq = '%03d' % int(seq)
                    self.set_combo_to_text(self.seq_combo, seq)
            if type(shot) != float:
                if shot:
                    shot = '%04d' % int(shot)
                    self.set_combo_to_text(self.shot_combo, shot)
            if type(task) != float:
                if task:
                    task = app_config()['pipeline_steps']['short_to_long'][task]
                    self.set_combo_to_text(self.task_combo, task)
            if type(status) != float:
                if status == 'Tagged':
                    self.publish_button.setEnabled(True)

    def set_combo_to_text(self, combo, text):
        index = combo.findText(text)
        if index != -1:
            combo.setCurrentIndex(index)
        else:
            combo.addItem(text)
            self.set_combo_to_text(combo, text)

    def save_data_frame(self):
        dropped_dupes = self.data_frame.drop_duplicates()
        dropped_dupes.to_csv(self.pandas_path)

    def on_version_changed(self):
        self.versions_changed.emit(self.versions.currentText())

    def on_radio_clicked(self):
        self.clear_all()
        if self.shot_radio_button.isChecked():
            self.seq_label.setText('Seq ')
            self.shot_label.setText('Shot')
            self.tags_label.setText('Tags')
        if self.asset_radio_button.isChecked():
            self.seq_label.setText('Category')
            self.shot_label.setText('Asset')
            self.tags_label.setText('Tags        ')
        self.populate_combos()

    def hide_tags(self):
        self.tags_title.setText("<b>Select File(s) or Folder(s) to tag</b>")
        self.asset_radio_button.hide()
        self.shot_radio_button.hide()
        self.seq_label.hide()
        self.seq_combo.hide()
        self.shot_label.hide()
        self.shot_combo.hide()
        self.task_label.hide()
        self.task_combo.hide()
        self.tags_label.hide()
        self.tags_line_edit.hide()

    def show_tags(self, files=[]):
        if len(files) == 1:
            files_text = files[0]
        else:
            files_text = '%s files' % len(files)

        self.tags_title.setText("<b>Tag %s for Publish</b>" % files_text)
        self.asset_radio_button.show()
        self.shot_radio_button.show()
        self.seq_label.show()
        self.seq_combo.show()
        self.shot_label.show()
        self.shot_combo.show()
        self.task_label.show()
        self.task_combo.show()
        self.tags_label.show()
        self.tags_line_edit.show()

    def populate_combos(self):
        ignore = ['default_steps', '']
        if self.shot_radio_button.isChecked():
            scope = 'shots'
        else:
            scope = 'assets'
        tasks = app_config()['pipeline_steps'][scope]
        seqs = self.path_object.copy(seq='*', scope=scope).glob_project_element('seq')
        task_names = ['']
        for each in tasks:
            if each not in ignore:
                task_names.append(each)
        self.task_combo.addItems(sorted(task_names))
        seqs.insert(0, '')
        self.seq_combo.addItems(seqs)

    def on_seq_changed(self):
        self.shot_combo.clear()
        if self.shot_radio_button.isChecked():
            scope = 'shots'
        else:
            scope = 'assets'
        seq = self.seq_combo.currentText()
        if seq:
            this = self.path_object.copy(scope=scope, seq=seq, shot='*')
            shots = self.path_object.copy(scope=scope, seq=seq, shot='*').glob_project_element('shot')
            if shots:
                shots.insert(0, '')
                self.shot_combo.addItems(shots)


class TaskWidget(QtWidgets.QFrame):
    button_clicked = QtCore.Signal(object)
    filter_changed = QtCore.Signal()
    add_clicked = QtCore.Signal()
    assign_clicked = QtCore.Signal(object)
    open_button_clicked = QtCore.Signal()
    new_version_clicked = QtCore.Signal()

    def __init__(self, parent, title, short_title, filter_string=None, path_object=None):
        QtWidgets.QFrame.__init__(self, parent)
        self.setFrameStyle(QtWidgets.QFrame.StyledPanel | QtWidgets.QFrame.Sunken)
        v_layout = QtWidgets.QVBoxLayout(self)
        task_row = QtWidgets.QHBoxLayout()
        self.path_object = path_object
        self.tool_button_layout = QtWidgets.QHBoxLayout()
        self.sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.Maximum)
        self.setSizePolicy(self.sizePolicy)
        self.filter_string = filter_string
        self.label = title
        self.title = QtWidgets.QLabel("<b>%s</b>" % title.title())
        self.task = None
        self.user = None
        self.in_file_tree = None
        self.versions = AdvComboBox()
        # self.versions.setMinimumWidth(200)
        self.versions.hide()
        self.setMinimumWidth(300)
        self.setMinimumHeight(200)

        self.users_label = QtWidgets.QLabel("User:")
        self.users = AdvComboBox()
        self.users_layout = QtWidgets.QHBoxLayout()
        self.users_layout.addItem(QtWidgets.QSpacerItem(0, 0, QtWidgets.QSizePolicy.Expanding,
                                                        QtWidgets.QSizePolicy.Minimum))
        self.users_layout.addWidget(self.users_label)

        self.users_layout.addWidget(self.users)

        self.resolutions = AdvComboBox()
        self.resolutions_layout = QtWidgets.QHBoxLayout()
        self.resolutions_layout.addItem(QtWidgets.QSpacerItem(0, 0, QtWidgets.QSizePolicy.Expanding,
                                                              QtWidgets.QSizePolicy.Minimum))
        self.resolutions_label = QtWidgets.QLabel("Resolution:")
        self.resolutions_layout.addWidget(self.resolutions_label)
        self.resolutions_layout.addWidget(self.resolutions)
        self.resolutions_layout.setContentsMargins(0, 0, 0, 0)

        # self.search_box = LJSearchEdit(self)
        # self.add_button = QtWidgets.QToolButton()
        # self.add_button.setText("+")
        self.show_button = QtWidgets.QToolButton()
        self.show_button.setText("more")
        self.assign_button = QtWidgets.QPushButton()
        self.assign_button.setText("Create Assignment")
        self.hide_button = QtWidgets.QToolButton()
        self.hide_button.setText("less")
        self.data_table = FileTableWidget(self)
        self.data_table.set_draggable(True)
        self.data_table.title = title
        self.data_table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.data_table.setMinimumHeight(50)
        self.data_table.setMinimumWidth(150)

        # build the tool button row
        self.open_button = QtWidgets.QToolButton()
        self.open_button.setText('Open')
        self.new_version_button = QtWidgets.QToolButton()
        self.new_version_button.setText('Version Up')
        self.review_button = QtWidgets.QToolButton()
        self.review_button.setText('Review')
        self.publish_button = QtWidgets.QToolButton()
        self.publish_button.setText('Publish')
        self.tool_button_layout.addItem(QtWidgets.QSpacerItem(0, 0, QtWidgets.QSizePolicy.Expanding,
                                                              QtWidgets.QSizePolicy.Minimum))
        self.tool_button_layout.addWidget(self.open_button)
        self.tool_button_layout.addWidget(self.new_version_button)
        self.tool_button_layout.addWidget(self.review_button)
        self.tool_button_layout.addWidget(self.publish_button)

        # this is where the filter needs to be!
        task_row.addWidget(self.title)
        task_row.addWidget(self.versions)
        # task_row.addWidget(self.search_box)
        task_row.addWidget(self.show_button)
        task_row.addWidget(self.hide_button)
        # task_row.addWidget(self.assign_button)
        # task_row.addWidget(self.add_button)

        v_layout.addLayout(task_row)
        # v_layout.addWidget(self.message)
        v_layout.addWidget(self.assign_button)
        v_layout.addLayout(self.users_layout)
        v_layout.addLayout(self.resolutions_layout)
        v_layout.addWidget(self.data_table, 1)
        v_layout.addItem((QtWidgets.QSpacerItem(0, 25, QtWidgets.QSizePolicy.Minimum,
                                                QtWidgets.QSizePolicy.Minimum)))
        v_layout.addLayout(self.tool_button_layout)
        v_layout.addItem((QtWidgets.QSpacerItem(0, 0, QtWidgets.QSizePolicy.Minimum,
                                                QtWidgets.QSizePolicy.MinimumExpanding)))
        self.setLayout(v_layout)
        self.hide_combos()

        self.assign_button.hide()
        self.hideall()
        self.show_button.clicked.connect(self.on_show_button_clicked)
        self.hide_button.clicked.connect(self.on_hide_button_clicked)
        # self.add_button.clicked.connect(self.on_add_button_clicked)
        self.assign_button.clicked.connect(self.on_assign_button_clicked)
        self.open_button.clicked.connect(self.on_open_button_clicked)
        self.new_version_button.clicked.connect(self.on_new_version_clicked)
        self.hide_tool_buttons()

    def get_category_label(self):
        if self.scope == 'assets':
            return 'Category'
        elif self.scope == 'shots':
            return 'Sequence'

    def hide(self):
        self.hide_button.hide()
        self.add_button.hide()
        self.data_table.hide()
        self.search_box.hide()
        self.show_button.hide()
        self.hide_button.hide()
        self.title.hide()
        self.users.hide()
        self.users_label.hide()
        self.resolutions.hide()
        self.resolutions_label.hide()
        self.assets_radio.hide()
        self.shots_radio.hide()
        self.io_radio.hide()
        self.category_combo.hide()
        self.category_label.hide()

    def show(self, combos=False):
        self.show_button.show()
        self.data_table.show()
        self.search_box.show()
        self.show_button.show()
        self.hide_button.show()
        self.title.show()
        if combos:
            self.show_combos()

    def hide_tool_buttons(self):
        self.open_button.hide()
        self.new_version_button.hide()
        self.publish_button.hide()
        self.review_button.hide()

    def show_filters(self):
        self.category_combo.show()
        self.category_label.show()
        self.assets_radio.show()
        self.shots_radio.show()
        self.io_radio.show()

    def hide_filters(self):
        self.category_combo.hide()
        self.category_label.hide()
        self.assets_radio.hide()
        self.shots_radio.hide()
        self.io_radio.hide()

    def show_tool_buttons(self):
        self.open_button.show()
        self.new_version_button.show()
        self.publish_button.show()
        self.review_button.show()

    def show_combos(self):
        self.users.show()
        self.users_label.show()
        self.resolutions.show()
        self.resolutions_label.show()

    def hide_combos(self):
        self.users.hide()
        self.users_label.hide()
        self.resolutions.hide()
        self.resolutions_label.hide()

    def hideall(self):
        self.hide_button.hide()
        self.data_table.hide()

    def showall(self):
        self.hide_button.show()
        self.show_button.hide()
        self.data_table.show()

    def setup(self, mdl):
        self.data_table.set_item_model(mdl)
        # self.data_table.set_search_box(self.search_box)

    def on_new_version_clicked(self):
        self.new_version_clicked.emit()

    def on_open_button_clicked(self):
        self.open_button_clicked.emit()

    def on_add_button_clicked(self):
        self.add_clicked.emit()

    def on_show_button_clicked(self):
        self.show_combos()
        self.hide_button.show()
        self.show_button.hide()

    def on_hide_button_clicked(self):
        self.hide_combos()
        self.hide_button.hide()
        self.show_button.show()

    def on_assign_button_clicked(self):
        self.assign_clicked.emit(self.path_object)

    def set_title(self, new_title):
        self.title.setText('<b>%s</b>' % new_title.title())


class ProjectWidget(QtWidgets.QWidget):
    button_clicked = QtCore.Signal(object)
    filter_changed = QtCore.Signal()
    add_clicked = QtCore.Signal()
    assign_clicked = QtCore.Signal(object)

    def __init__(self, parent=None, title='', filter_string=None, path_object=None):
        QtWidgets.QWidget.__init__(self, parent)
        v_layout = QtWidgets.QVBoxLayout(self)
        h_layout = QtWidgets.QHBoxLayout()
        self.path_object = path_object
        self.tool_button_layout = QtWidgets.QHBoxLayout()
        self.sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.MinimumExpanding)
        self.setSizePolicy(self.sizePolicy)
        self.filter_string = filter_string
        self.label = title
        self.title = QtWidgets.QLabel("<b>%s</b>" % title)
        self.task = None
        self.user = None

        self.message = QtWidgets.QLabel("")
        # TODO - need to remove the dropdown button on this instance
        self.search_box = LJSearchEdit(self)
        self.add_button = QtWidgets.QToolButton()
        self.add_button.setText("+")
        self.data_table = LJTableWidget(self)
        self.data_table.title = title
        self.data_table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.data_table.setMinimumWidth(220)
        h_layout.addWidget(self.title)
        h_layout.addWidget(self.add_button)

        v_layout.addLayout(h_layout)
        #v_layout.addWidget(self.message)
        v_layout.addWidget(self.search_box)
        v_layout.addWidget(self.data_table, 1)
        # v_layout.setSpacing(10)
        #v_layout.setContentsMargins(0, 20, 0, 0)  # left, top, right, bottom

        self.add_button.clicked.connect(self.on_add_button_clicked)

    def setup(self, mdl):
        self.data_table.set_item_model(mdl)
        self.data_table.set_search_box(self.search_box)

    def on_add_button_clicked(self):
        self.add_clicked.emit()

    def on_show_button_clicked(self):
        self.show_combos()
        self.hide_button.show()
        self.show_button.hide()

    def on_hide_button_clicked(self):
        self.hide_combos()
        self.hide_button.hide()
        self.show_button.show()

    def on_assign_button_clicked(self):
        self.assign_clicked.emit(self.path_object)

    def set_title(self, new_title):
        self.title.setText('<b>%s</b>' % new_title.title())

    def hide_all(self):
        self.search_box.hide()
        self.add_button.hide()
        self.data_table.hide()
        self.title.hide()

    def show_all(self):
        self.search_box.show()
        self.add_button.show()
        self.data_table.show()
        self.title.show()


class AssetWidget(QtWidgets.QWidget):
    button_clicked = QtCore.Signal(object)
    filter_changed = QtCore.Signal()
    add_clicked = QtCore.Signal()
    assign_clicked = QtCore.Signal(object)

    def __init__(self, parent, title, filter_string=None, path_object=None):
        QtWidgets.QWidget.__init__(self, parent)
        self.v_layout = QtWidgets.QVBoxLayout(self)
        v_list = QtWidgets.QVBoxLayout()
        scope_layout = QtWidgets.QHBoxLayout()
        self.path_object = path_object
        self.tool_button_layout = QtWidgets.QHBoxLayout()
        self.sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.MinimumExpanding)
        self.setSizePolicy(self.sizePolicy)
        self.filter_string = filter_string
        self.label = title
        self.title = QtWidgets.QLabel("<h2>Project: %s</h2>" % title)
        self.scope_title = QtWidgets.QLabel("<b>%s</b>" % 'Assets')
        self.task = None
        self.user = None
        minWidth = 340

        self.message = QtWidgets.QLabel("")
        self.message.setMinimumWidth(minWidth)
        self.message.setSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
        self.message.setAlignment(QtCore.Qt.AlignCenter)
        self.search_box = LJSearchEdit(self)
        self.add_button = QtWidgets.QToolButton()
        self.add_button.setText("+")
        self.data_table = LJTableWidget(self)
        self.data_table.title = title
        self.data_table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.data_table.setMinimumWidth(minWidth)

        # build the filter optoins row
        self.assets_radio = QtWidgets.QRadioButton('Assets')
        self.shots_radio = QtWidgets.QRadioButton('Shots')
        self.radio_group_scope = QtWidgets.QButtonGroup(self)
        self.radio_group_scope.addButton(self.shots_radio)
        self.radio_group_scope.addButton(self.assets_radio)

        scope_layout.addWidget(self.scope_title)
        scope_layout.addItem(QtWidgets.QSpacerItem(0, 0, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum))
        scope_layout.addWidget(self.shots_radio)
        scope_layout.addWidget(self.assets_radio)
        scope_layout.addWidget(self.add_button)

        v_list.addItem(QtWidgets.QSpacerItem(0, 3, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Minimum))
        v_list.addWidget(self.search_box)
        v_list.addWidget(self.data_table, 1)

        self.v_layout.addWidget(self.title)
        self.v_layout.addLayout(scope_layout)
        self.v_layout.addWidget(self.message)
        self.v_layout.addLayout(v_list)
        self.v_layout.setContentsMargins(0, 12, 0, 0)

        self.add_button.clicked.connect(self.on_add_button_clicked)

    def get_category_label(self):
        if self.scope == 'assets':
            return 'Category'
        elif self.scope == 'shots':
            return 'Sequence'

    def setup(self, mdl):
        self.data_table.set_item_model(mdl)
        self.data_table.set_search_box(self.search_box)

    def on_add_button_clicked(self):
        self.add_clicked.emit()

    def on_show_button_clicked(self):
        self.show_combos()
        self.hide_button.show()
        self.show_button.hide()

    def on_hide_button_clicked(self):
        self.hide_combos()
        self.hide_button.hide()
        self.show_button.show()

    def on_assign_button_clicked(self):
        self.assign_clicked.emit(self.path_object)

    def set_title(self, new_title):
        self.title.setText('<h2>Project:  %s</h2>' % new_title.title())

    def set_scope_title(self, new_title):
        self.scope_title.setText('<b>%s</b>' % new_title.title())


class FileTableWidget(LJTableWidget):
    show_in_folder = QtCore.Signal()
    show_in_shotgun = QtCore.Signal()
    copy_folder_path = QtCore.Signal()
    copy_file_path = QtCore.Signal()
    import_version_from = QtCore.Signal()
    push_to_cloud = QtCore.Signal()
    pull_from_cloud = QtCore.Signal()
    share_download_link = QtCore.Signal()

    def __init__(self, parent):
        LJTableWidget.__init__(self, parent)
        # Set The Right Click Menu
        self.horizontalHeader().hide()
        self.item_right_click_menu = LJMenu(self)
        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.item_right_click_menu.create_action("Show In Folder", self.show_in_folder)
        self.item_right_click_menu.create_action("Show In ShotGun", self.show_in_shotgun)
        self.item_right_click_menu.addSeparator()
        self.item_right_click_menu.create_action("Copy Folder Path", self.copy_folder_path)
        self.item_right_click_menu.create_action("Copy File Path", self.copy_file_path)
        self.item_right_click_menu.addSeparator()
        self.item_right_click_menu.create_action("Import Version From...", self.import_version_from)
        self.item_right_click_menu.addSeparator()
        self.item_right_click_menu.create_action("Push", self.push_to_cloud)
        self.item_right_click_menu.create_action("Pull", self.pull_from_cloud)
        self.item_right_click_menu.create_action("Share Download Link", self.share_download_link)
        self.item_right_click_menu.addSeparator()
        # self.item_right_click_menu.create_action("Create Dailies Template", self.create_dailies_template_signal)
        # self.item_right_click_menu.addSeparator()
        self.customContextMenuRequested.connect(self.item_right_click)
        self.setAcceptDrops(True)
        self.setMaximumHeight(self.height_hint)

    def item_right_click(self, position):
        self.item_right_click_menu.exec_(self.mapToGlobal(position))

    def dragEnterEvent(self, e):
        if e.mimeData().hasUrls:
            e.accept()
        else:
            e.ignore()

    def dragMoveEvent(self, e):
        if e.mimeData().hasUrls:
            e.setDropAction(QtCore.Qt.CopyAction)
            e.accept()
        else:
            e.ignore()