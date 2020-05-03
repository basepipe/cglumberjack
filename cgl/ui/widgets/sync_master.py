import glob
import os
from cgl.plugins.Qt import QtCore, QtGui, QtWidgets
from cgl.ui.widgets.base import LJDialog
from cgl.core.utils.general import current_user
from cgl.ui.widgets.widgets import AdvComboBox
from cgl.core.path import PathObject, show_in_folder, get_folder_size, find_latest_publish_objects
from cgl.core.config import get_globals


class SyncMaster(LJDialog):

    def __init__(self, company=None, project=None, scope='assets', device_list=[]):
        LJDialog.__init__(self)
        user = current_user()
        self.device_list = device_list
        self.setWindowTitle('Lumber Sync')
        self.globals = get_globals()
        self.company = company
        self.project = project
        self.scope = scope
        self.current_selection = ''
        self.path_object = PathObject(self.globals['paths']['root'])
        self.sync_folder_dict = self.get_sync_folder_dict()

        layout = QtWidgets.QVBoxLayout(self)
        grid_layout = QtWidgets.QGridLayout()
        check_box_layout = QtWidgets.QHBoxLayout()
        radio_layout = QtWidgets.QHBoxLayout()
        company_label = QtWidgets.QLabel('Company:')
        project_label = QtWidgets.QLabel('Project:')
        self.source_check_box = QtWidgets.QCheckBox('source')
        self.render_check_box = QtWidgets.QCheckBox('render')
        self.publish_check_box = QtWidgets.QCheckBox('publish only')
        self.publish_check_box.setChecked(True)
        self.publish_check_box.setEnabled(False)
        self.assets_radio = QtWidgets.QRadioButton('assets')
        self.shots_radio = QtWidgets.QRadioButton('shots')
        if self.scope == 'assets':
            self.assets_radio.setChecked(True)
        elif self.scope == 'shots':
            self.shots_radio.setChecked(True)
        else:
            self.assets_radio.setChecked(True)
        self.model = SyncTreeModel(self.sync_folder_dict)
        self.model.setRootPath(self.path_object.path_root)
        self.file_tree = QtWidgets.QTreeView()
        self.file_tree.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.file_tree.customContextMenuRequested.connect(self.sync_menu)
        self.file_tree.hide()

        self.company_combo = AdvComboBox()
        self.project_combo = AdvComboBox()

        check_box_layout.addWidget(self.publish_check_box)
        check_box_layout.addWidget(self.source_check_box)
        check_box_layout.addWidget(self.render_check_box)
        check_box_layout.addStretch(1)
        radio_layout.addWidget(self.assets_radio)
        radio_layout.addWidget(self.shots_radio)
        radio_layout.addStretch(1)

        grid_layout.addWidget(company_label, 0, 0)
        grid_layout.addWidget(project_label, 1, 0)
        grid_layout.addWidget(self.company_combo, 0, 1)
        grid_layout.addWidget(self.project_combo, 1, 1)
        
        layout.addLayout(grid_layout)
        layout.addLayout(check_box_layout)
        layout.addLayout(radio_layout)
        layout.addWidget(self.file_tree)

        self.source_check_box.setChecked(True)
        self.company_combo.currentIndexChanged.connect(self.on_company_changed)
        self.project_combo.currentIndexChanged.connect(self.on_project_changed)
        self.shots_radio.clicked.connect(self.on_scope_changed)
        self.assets_radio.clicked.connect(self.on_scope_changed)
        self.file_tree.clicked.connect(self.on_file_tree_clicked)
        self.assets_radio.hide()
        self.shots_radio.hide()
        self.load_companies()

    @staticmethod
    def get_sync_folder_dict():
        import cgl.plugins.syncthing.utils as st
        dict_ = st.get_sync_folders()
        for each in dict_:
            print 'key', each
        return st.get_sync_folders()

    @QtCore.Slot(QtCore.QModelIndex)
    def on_file_tree_clicked(self, index):
        index_ = self.model.index(index.row(), 0, index.parent())
        file_path = self.model.filePath(index_)
        self.current_selection = file_path

    def sync_menu(self, position):
        indexes = self.file_tree.selectedIndexes()
        if len(indexes) > 0:
            level = 0
            index = indexes[0]
            while index.parent().isValid():
                index = index.parent()
                level += 1
                menu = QtWidgets.QMenu()
                if level == 0:
                    menu.addAction(self.tr("Edit person"))
                elif level == 1:
                    menu.addAction(self.tr("Edit object/container"))
                elif level == 2:
                    show_action = QtWidgets.QAction("Show in Folder", self)
                    sync_action = QtWidgets.QAction("Sync", self)
                    menu.addAction(show_action)
                    menu.addAction(sync_action)
                    show_action.triggered.connect(self.show_in_folder)
                    sync_action.triggered.connect(self.sync_clicked)
                    menu.exec_(self.file_tree.viewport().mapToGlobal(position))

    def show_in_folder(self):
        show_in_folder(self.current_selection)
        print 'Total Folder Size:', get_folder_size(self.current_selection)

    def sync_clicked(self):
        import cgl.plugins.syncthing.utils as st
        publishes = find_latest_publish_objects(self.current_selection, source=self.source_check_box.isChecked(),
                                                render=self.render_check_box.isChecked())
        device_dict = st.get_device_dict()
        this_device = st.get_my_device_info()['id']
        dialog_sharing = SharingDialog(this_device, device_dict)
        dialog_sharing.exec_()
        if dialog_sharing.button == 'Ok':
            all_device_id = dialog_sharing.device_list
            if all_device_id:
                st.kill_syncthing()
                if publishes:
                    for p in publishes:
                        folder_id = '[root]\\%s' % p.path.replace('/', '\\')
                        folder = p.path_root.replace('/', '\\')
                        st.add_folder_to_config(folder_id, folder, all_device_id, type_='sendonly')
                st.launch_syncthing()

    def on_scope_changed(self):
        if self.shots_radio.isChecked():
            self.scope = 'shots'
        else:
            self.scope = 'assets'
        self.path_object.set_attr(scope=self.scope)
        self.load_file_tree()

    def on_project_changed(self):
        self.project = self.project_combo.currentText()
        if self.project:
            self.path_object.set_attr(project=self.project_combo.currentText())
            self.path_object.set_attr(scope=self.scope)
            self.shots_radio.show()
            self.assets_radio.show()
            self.load_file_tree()
        else:
            self.shots_radio.hide()
            self.assets_radio.hide()

    def load_file_tree(self):
        self.model = SyncTreeModel(self.sync_folder_dict)
        self.model.setRootPath(self.path_object.path_root)
        self.file_tree.show()
        self.file_tree.setModel(self.model)
        self.file_tree.setRootIndex(self.model.index(self.path_object.path_root))
        self.file_tree.setColumnHidden(1, True)
        self.file_tree.setColumnHidden(2, True)
        self.file_tree.setColumnHidden(3, True)

    def on_company_changed(self):
        self.company = self.company_combo.currentText()
        self.path_object.set_attr(company=self.company)
        self.path_object.set_attr(context='source')
        self.path_object.set_attr(project='*')
        self.path_object.set_attr(scope=None)
        self.load_projects()

    def load_companies(self):
        company = self.company
        self.path_object.set_attr(company='*')
        companies = glob.glob(self.path_object.path_root)
        items = ['']
        for c in companies:
            items.append(os.path.basename(c))
        self.company_combo.addItems(items)
        if company in items:
            # TODO = i should add this as a function in AdvComboBox
            i = self.company_combo.findText(company)
            if i != -1:
                self.company_combo.setCurrentIndex(i)
            else:
                self.company_combo.setCurrentIndex(0)

    def load_projects(self):
        project = self.project
        if self.company:
            projects = glob.glob(self.path_object.path_root)
            items = ['']
            for p in projects:
                items.append(os.path.basename(p))
            self.project_combo.addItems(items)
            if project in items:
                i = self.project_combo.findText(project)
                if i != -1:
                    self.project_combo.setCurrentIndex(i)


class SyncTreeModel(QtWidgets.QFileSystemModel):

    def __init__(self, sync_folder_dict):
        QtWidgets.QFileSystemModel.__init__(self)
        self.sync_folder_dict = sync_folder_dict

    def headerData(self, section, orientation, role):
        if section == 4:
            if role == QtCore.Qt.DisplayRole:
                return 'Sync Status'
        if section == 5:
            if role == QtCore.Qt.DisplayRole:
                return 'Total Size'
        if role == QtCore.Qt.DecorationRole:
            return None
        else:
            return super(SyncTreeModel, self).headerData(section, orientation, role)

    def columnCount(self, parent=QtCore.QModelIndex()):
        return super(SyncTreeModel, self).columnCount()+2

    def data(self, index, role):
        if index.column() == self.columnCount()-1:
            if role == QtCore.Qt.DisplayRole:
                return "Calculating..."
            if role == QtCore.Qt.TextAlignmentRole:
                return QtCore.Qt.AlignHCenter
        if index.column() == self.columnCount()-2:
            if role == QtCore.Qt.DisplayRole:
                current_file = self.filePath(index).replace('/', '\\')
                if current_file in self.sync_folder_dict.keys():
                    print current_file
                    return self.sync_folder_dict[current_file]['type']
                else:
                    return "Not Synced"
            if role == QtCore.Qt.TextAlignmentRole:
                return QtCore.Qt.AlignHCenter
        return super(SyncTreeModel, self).data(index, role)


class SharingDialog(LJDialog):
    """
    Allows someone to choose who they will share a folder with.
    """
    def __init__(self, this_device, device_dict):
        LJDialog.__init__(self)
        self.setWindowTitle('Sharing Options')
        layout = QtWidgets.QVBoxLayout(self)
        grid = QtWidgets.QGridLayout()
        self.device_dict = device_dict
        self.device_list = []
        self.this_device = this_device
        self.button = ''
        for i, d in enumerate(device_dict):
            device_id = d
            if device_id != self.this_device:
                device_name = device_dict[d]['device_name']
                user = device_dict[d]['username']
                proj_man_user = device_dict[d]['proj_man_user']
                full_name = device_dict[d]['full_name']
                label = '%s: (%s)' % (user, device_name)
                check_box = QtWidgets.QCheckBox(label)
                check_box.device_id = device_id
                check_box.proj_man_user = proj_man_user
                check_box.full_name = full_name
                check_box.user = user
                check_box.device_name = device_name
                grid.addWidget(check_box, i, 0)
                check_box.clicked.connect(self.on_checkbox_clicked)

        message = QtWidgets.QLabel("Who (which machines) do you want to share with?")
        button_row = QtWidgets.QHBoxLayout()
        ok_button = QtWidgets.QPushButton('Ok')
        cancel_button = QtWidgets.QPushButton('Cancel')

        ok_button.clicked.connect(self.on_ok_clicked)
        cancel_button.clicked.connect(self.on_cancel_clicked)
        button_row.addStretch(1)
        button_row.addWidget(cancel_button)
        button_row.addWidget(ok_button)
        layout.addWidget(message)
        layout.addLayout(grid)
        layout.addLayout(button_row)

    def on_checkbox_clicked(self):
        check_box = self.sender()
        if self.sender().isChecked():
            self.device_list.append(check_box.device_id)
            print check_box.device_id
            print check_box.device_name
            print check_box.user
            print check_box.full_name

    def on_ok_clicked(self):
        self.button = 'Ok'
        self.accept()
        return self.device_list

    def on_cancel_clicked(self):
        self.button = 'Cancel'
        self.accept()
        return None


if __name__ == "__main__":
    # from cgl.core.utils import load_style_sheet
    pass
