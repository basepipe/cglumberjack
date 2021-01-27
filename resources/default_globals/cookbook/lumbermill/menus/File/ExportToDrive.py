import sys
import os
from cgl.plugins.Qt import QtWidgets
from cgl.ui.widgets.base import LJDialog
from cgl.ui.widgets.combo import AdvComboBox
from cgl.core.path import PathObject
from cgl.core.utils.general import cgl_copy


def run(lumbermill):
    """
    Copies Entire Folder Structures to an external Drive
    :param session:
    :return:
    """
    path_object = PathObject(lumbermill.path_widget.text.replace('/*', ''))
    dialog = ExportDialog(path_object=path_object)
    dialog.exec_()


class ExportDialog(LJDialog):
    def __init__(self, path_object):
        LJDialog.__init__(self)
        self.path_object = path_object
        if self.path_object.context == 'source':
            self.other_path_object = PathObject.copy(path_object, context='render')
        else:
            self.other_path_object = PathObject.copy(path_object, context='source')
        # TODO - i need something here to check if i'm in a task or not, if not send a popup
        task = path_object.task
        seq = path_object.seq
        shot = path_object.shot
        self.to_object = None
        self.root = ''
        all_ = r'%s/%s/%s' % (seq, shot, task)
        self.setWindowTitle('Export %s to drive' % all_)
        v_layout = QtWidgets.QVBoxLayout(self)
        grid_layout = QtWidgets.QGridLayout()
        button_layout = QtWidgets.QHBoxLayout()
        drive_label = QtWidgets.QLabel('External Drive:')
        self.drive_combo = AdvComboBox()
        root_label = QtWidgets.QLabel('External Drive Root:')
        self.root_line_edit = QtWidgets.QLineEdit()
        copy_from_label = QtWidgets.QLabel('copy from:')
        self.copy_from_path = QtWidgets.QLabel(path_object.path_root)
        copy_to_label = QtWidgets.QLabel('copy to')
        self.copy_to_path = QtWidgets.QLabel('')
        self.message = QtWidgets.QLabel('')
        self.cancel_button = QtWidgets.QPushButton('Cancel')
        self.ok_button = QtWidgets.QPushButton('Copy Task')

        grid_layout.addWidget(drive_label, 0, 0)
        grid_layout.addWidget(self.drive_combo, 0, 1)
        grid_layout.addWidget(root_label, 1, 0)
        grid_layout.addWidget(self.root_line_edit, 1, 1)
        grid_layout.addWidget(copy_from_label, 2, 0)
        grid_layout.addWidget(self.copy_from_path, 2, 1)
        grid_layout.addWidget(copy_to_label, 3, 0)
        grid_layout.addWidget(self.copy_to_path, 3, 1)

        button_layout.addStretch(1)
        button_layout.addWidget(self.cancel_button)
        button_layout.addWidget(self.ok_button)

        v_layout.addLayout(grid_layout)
        v_layout.addWidget(self.message)
        v_layout.addLayout(button_layout)

        self.drive_combo.currentIndexChanged.connect(self.on_drive_changed)
        self.root_line_edit.textChanged.connect(self.on_root_edited)
        self.cancel_button.clicked.connect(self.on_cancel_clicked)
        self.ok_button.clicked.connect(self.on_copy_clicked)
        self.get_available_drives()

    def get_available_drives(self):
        ignore = ['C:\\']
        root_drive = self.path_object.root.split(':')[0]
        print(root_drive)
        ignore.append('%s:\\' % root_drive)
        if sys.platform == "darwin":
            print('osx')
        elif sys.platform == "linux2":
            print('linux')
        else:
            import win32api
            drives = win32api.GetLogicalDriveStrings()
            drives = drives.split('\000')[:-1]
            for each in drives:
                if each not in ignore:
                    self.drive_combo.addItem(each)

    def on_drive_changed(self):
        self.drive = self.drive_combo.currentText()
        self.root = os.path.join(self.drive, 'CGL_EXPORT', 'COMPANIES')
        self.root_line_edit.setText(self.root)
        self.to_object = PathObject.copy(self.path_object, root=self.root)
        if self.to_object.context == 'source':
            self.other_to_object = PathObject.copy(self.to_object, context='render')
        else:
            self.other_to_object = PathObject.copy(self.to_object, context='source')
        self.copy_to_path.setText(self.to_object.path_root.replace('\\', '/'))

    def on_root_edited(self):
        self.root = os.path.join(self.drive, self.root_line_edit.text()).replace('\\', '/')
        self.to_object = PathObject.copy(self.path_object, root=self.root)
        if self.to_object.context == 'source':
            self.other_to_object = PathObject.copy(self.to_object, context='render')
        else:
            self.other_to_object = PathObject.copy(self.to_object, context='source')
        self.copy_to_path.setText(self.to_object.path_root.replace('\\', '/'))

    def on_cancel_clicked(self):
        self.accept()

    def on_copy_clicked(self):
        from_path = self.copy_from_path.text()
        to_path = self.copy_to_path.text()
        other_from_path = self.other_path_object.path_root
        other_to_path = self.other_to_object.path_root
        print('Copying %s to %s' % (from_path, to_path))
        print('Copying %s to %s' % (other_from_path, other_to_path))
        cgl_copy(from_path, to_path)
        cgl_copy(other_from_path, other_to_path)
        self.accept()

