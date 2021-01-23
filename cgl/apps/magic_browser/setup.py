import getpass
import glob
import os
import logging
import urllib.request
import requests
from cgl.plugins.Qt import QtCore, QtGui, QtWidgets
from cgl.core.utils.general import save_json, load_json, cgl_copy
from cgl.core.config.config import get_user_config_file, get_sync_config_file, ProjectConfig, user_config

DEFAULT_ROOT = r"C:\CGLUMBERJACK\COMPANIES"
DEFAULT_CODE_ROOT = os.path.join(os.path.expanduser("~"), 'PycharmProjects', 'cglumberjack')
DEFAULT_HOME = os.path.join(os.path.expanduser("~"), 'Documents', 'cglumberjack')


class QuickSync(QtWidgets.QDialog):

    def __init__(self, parent=None):
        QtWidgets.QDialog.__init__(self, parent)
        self.setMinimumWidth(500)
        self.setMinimumHeight(200)
        self.setWindowTitle('Magic Browser Quick Setup')
        self.default_user_globals = get_user_config_file()
        self.default_root = DEFAULT_ROOT
        self.default_code_root = DEFAULT_CODE_ROOT
        size_policy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)
        size_policy.setVerticalStretch(1)
        layout = QtWidgets.QVBoxLayout(self)
        #layout.setSizePolicy(size_policy)
        grid_layout = QtWidgets.QGridLayout()
        button_layout = QtWidgets.QHBoxLayout()

        company_label = QtWidgets.QLabel('Company Name')
        root_label = QtWidgets.QLabel('Root Folder:')

        self.company_line_edit = QtWidgets.QLineEdit()
        self.root_line_edit = QtWidgets.QLineEdit()

        self.root_line_edit.setText(self.default_root)
        self.company_line_edit.setText('default')

        self.company_name = ''
        self.setup_mb_button = QtWidgets.QPushButton('Set Up Magic Browser')

        button_layout.addStretch(1)
        button_layout.addWidget(self.setup_mb_button)

        grid_layout.addWidget(company_label, 0, 0)
        grid_layout.addWidget(self.company_line_edit, 0, 1)
        grid_layout.addWidget(root_label, 2, 0)
        grid_layout.addWidget(self.root_line_edit, 2, 1)

        layout.addLayout(grid_layout)
        layout.addLayout(button_layout)
        layout.addStretch(1)
        self.on_company_name_changed()

        self.company_line_edit.editingFinished.connect(self.on_company_name_changed)
        self.setup_mb_button.clicked.connect(self.set_up_magic_browser)

    def on_company_name_changed(self):
        """
        Check for sync spreadsheet
        :return:
        """
        self.company_name = self.company_line_edit.text()
        print('Attempting sync with {}'.format(self.company_name))

    def set_up_magic_browser(self):
        """
        checks s3 for the existance of a globals file and alchemists_cookbook files.
        :return:
        """
        # create_user_globals(self.root_line_edit.text())
        setup_sync()
        # set_up_workstation()
        self.accept()
        # Launch Magic Browser


def create_default_globals():
    code_root = user_config()['paths']['code_root']
    code_root = os.path.join(code_root, 'resources', 'default_globals')
    cfg = ProjectConfig()
    if not os.path.exists(cfg.project_config_file):
        config_folder = os.path.dirname(cfg.project_config_file)
        print('Copying {} to {}'.format(code_root, config_folder))
        cgl_copy(code_root, config_folder)


def setup_sync():
    import cgl.plugins.syncthing.utils as st_utils
    print('Setup Sync')
    st_utils.setup_workstation()
    st_utils.kill_syncthing()
    st_utils.launch_syncthing(True)


def create_user_globals(root=None):
    print('Checking for root: {}'.format(root))
    user_globals = get_user_config_file()
    if root:
        if not os.path.exists(os.path.dirname(user_globals)):
            os.makedirs(os.path.dirname(user_globals))
        d = {
             "previous_path": "",
             "previous_paths": {},
             "methodology": "local",
             "my_tasks": {},
             "paths": {"ari_convert": "arc_cmd",
                        "code_root": find_glob_path(r"C:\\Users\\*\\PycharmProjects\\cglumberjack"),
                        "convert": find_glob_path(r'C:\\*\\ImageMagick*\\magick.exe'),
                        "deadline": find_glob_path(r"C:\\*\\Thinkbox\\Deadline10\\bin\\deadlinecommand.exe"),
                        "ffmpeg": find_file_path("C:\\ProgramData\\chocolatey\\lib\\ffmpeg\\tools\\ffmpeg\\bin\\ffmpeg.exe"),
                        "ffplay": find_file_path("C:\\ProgramData\\chocolatey\\lib\\ffmpeg\\tools\\ffmpeg\\bin\\ffplay.exe"),
                        "ffprobe": find_file_path("C:\\ProgramData\\chocolatey\\lib\\ffmpeg\\tools\\ffmpeg\\bin\\ffprobe.exe"),
                        "magick": find_glob_path(r"C:\\*\\ImageMagick*\\magick.exe"),
                        "maketx": find_glob_path(r"C:\\OpenImage*\\bin\\maketx.exe"),
                        "mayapy": find_glob_path(r"C:\\*\\Autodesk\\Maya*\\bin\\mayapy.exe"),
                        "nuke": find_glob_path(r"C:\\*\\Nuke*\\*.exe"),
                        "oiiotool": find_glob_path(r"C:\\OpenImage*\\bin\\oiiotool.exe"),
                        "root": root,
                        "smedge": find_glob_path(r"C:\\*\\Smedge\\Submit.exe"),
                        "wget": find_file_path("C:\\ProgramData\\chocolatey\\lib\\Wget\\tools\\wget.exe")
                       }
             }
        logging.debug("saving user_globals to %s" % user_globals)
        save_json(get_user_config_file(), d)


def find_glob_path(glob_string):
    file_ = glob.glob(glob_string)
    if file_:
        return file_[0]
    else:
        print('Cant find file {}'.format(glob_string))
        return ""


def find_file_path(file_path):
    if os.path.exists(file_path):
        return file_path
    else:
        return ""


if __name__ == "__main__":
    #app = QtWidgets.QApplication([])
    #form = QuickSync()
    #form.show()
    #app.exec_()
    # setup_sync()
    create_default_globals()
