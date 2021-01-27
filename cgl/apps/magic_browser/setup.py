import getpass
import glob
import os
import logging
import urllib.request
import requests
from cgl.plugins.Qt import QtCore, QtGui, QtWidgets
from cgl.core.utils.general import save_json, load_json, cgl_copy
from cgl.core.utils import read_write, web
from cgl.core.config.config import get_user_config_file, get_sync_config_file, ProjectConfig, user_config

DEFAULT_ROOT = r"C:\CGLUMBERJACK\COMPANIES"
DEFAULT_CODE_ROOT = os.path.join(os.path.expanduser("~"), 'PycharmProjects', 'cglumberjack')
DEFAULT_HOME = os.path.join(os.path.expanduser("~"), 'Documents', 'cglumberjack')
AWS_PATH = os.path.join(os.path.expanduser("~"), ".aws")


class QuickSync(QtWidgets.QDialog):

    def __init__(self, parent=None):
        QtWidgets.QDialog.__init__(self, parent)
        self.setMinimumWidth(500)
        self.setMinimumHeight(200)
        self.setWindowTitle('Magic Browser Quick Setup')
        self.default_user_globals = get_user_config_file()
        self.default_root = DEFAULT_ROOT
        self.default_code_root = DEFAULT_CODE_ROOT
        self.client_file_download_path = "~\\Documents\\cglumberjack\\sync\\client.json"
        self.config_folder_path = os.path.join(self.default_root, 'master', 'config', 'master')
        self.aws_master_globals_url = ''
        self.aws_client_file_url = ''
        self.company_name_s3 = ''
        self.company_name_disk = ''
        self.aws_globals = ''
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
        self.aws_globals_label = QtWidgets.QLabel()

        self.root_line_edit.setText(self.default_root)
        self.company_line_edit.setText('default')

        self.company_name = ''
        self.setup_mb_button = QtWidgets.QPushButton('Set Up Magic Browser')
        button_layout.addWidget(self.aws_globals_label)
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
        if self.company_name:
            self.company_name_s3 = self.company_name.replace(' ', '-').replace('_', '-')
            self.company_name_disk = self.company_name_s3.replace('-', '_')
            self.aws_client_file_url = "https://{}.s3.amazonaws.com/sync/client.json".format(self.company_name)
            self.aws_master_globals_url = "https://{}.s3.amazonaws.com/config.zip".format(self.company_name)
            if web.url_exists(self.aws_client_file_url):
                self.aws_globals_label.setText('Found Company Sync Info on cloud')
                self.aws_globals_label.setStyleSheet("color: rgb(0, 255, 0);")
            else:
                self.aws_globals_label.setText('No Shared Globals Found - skipping')
                self.aws_globals_label.setStyleSheet("color: rgb(255, 0, 0);")
            self.aws_globals_label.show()

    def aws_download(self):
        """
        Pulls company specific information down for globals and syncing.
        :return:
        """
        if self.aws_globals_label.text() == 'Found Shared Company Globals on Cloud':
            if not os.path.exists(self.config_folder_path):
                if web.url_exists(self.aws_master_globals_url):
                    print('Downloading default globals to {}'.format(self.config_folder_path))
                    # download the aws master globals for this company
                    # we can save the config on AWS until we figure something out with Github.

    def set_up_magic_browser(self):
        """
        checks s3 for the existance of a globals file and alchemists_cookbook files.
        :return:
        """
        create_user_globals(self.root_line_edit.text())
        add_aws_credentials()
        setup_sync()
        set_up_workstation()
        self.accept()

    def download_globals_from_cloud(self):

        if self.aws_globals_label.text() == 'Found Shared Company Globals on Cloud':
            globals_path = os.path.join(DEFAULT_HOME, 'downloads', 'globals.json')
            cgl_tools_path = os.path.join(DEFAULT_HOME, 'downloads', 'cgl_tools.zip')
            self.globals_path = globals_path
            self.cgl_tools_path = cgl_tools_path
            if not os.path.exists(os.path.dirname(globals_path)):
                os.makedirs(os.path.dirname(globals_path))
            if os.path.exists(globals_path):
                os.remove(globals_path)
            try:
                # save the globals to globals_path
                urllib.request.urlretrieve(self.aws_globals, globals_path)
                return True
            except ImportError:  # Python 2
                r = requests.get(self.aws_globals, allow_redirects=True)
                logging.debug(r.content)
                if '<Error>' in str(r.content):
                    logging.debug('No File %s for company: %s' % (self.aws_globals, self.company_name))
                else:
                    logging.debug('Saving Globals file to: %s' % globals_path)
                    with open(globals_path, 'w+') as f:
                        f.write(r.content)
                self.accept()
                return True
            else:
                logging.error('Problem downloading %s' % self.aws_globals)
        else:
            logging.debug('No Globals Found - Get your Studio to publish their globals, or Create new ones?')
            return False
    # Launch Magic Browser


class AWSDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        QtWidgets.QDialog.__init__(self, parent)
        self.setWindowTitle('Enter AWS Information')
        self.layout = QtWidgets.QVBoxLayout(self)
        grid_layout = QtWidgets.QGridLayout()
        button_layout = QtWidgets.QHBoxLayout()

        self.id_line_edit = QtWidgets.QLineEdit()
        self.access_key_line_edit = QtWidgets.QLineEdit()
        self.region_line_edit = QtWidgets.QLineEdit()
        self.region_line_edit.setText("us-east-1")

        id_label = QtWidgets.QLabel('aws_access_key_id: ')
        access_key_label = QtWidgets.QLabel('aws_secret_access_key: ')
        region_label = QtWidgets.QLabel('region: ')

        self.submit_button = QtWidgets.QPushButton("Submit")

        grid_layout.addWidget(id_label, 0, 0)
        grid_layout.addWidget(self.id_line_edit, 0, 1)
        grid_layout.addWidget(access_key_label, 1, 0)
        grid_layout.addWidget(self.access_key_line_edit, 1, 1)
        grid_layout.addWidget(region_label, 2, 0)
        grid_layout.addWidget(self.region_line_edit, 2, 1)

        button_layout.addWidget(self.submit_button)

        self.layout.addLayout(grid_layout)
        self.layout.addLayout(button_layout)

        self.submit_button.clicked.connect(self.submit_pressed)

    def submit_pressed(self):
        if os.path.exists(AWS_PATH):
            print("HE EXIST: %s" % AWS_PATH)
        else:
            os.mkdir(AWS_PATH)
            print("HE GONE KID: %s" % AWS_PATH)

        with open(os.path.join(AWS_PATH, "config"), "w") as openFile:
            openFile.write("[default]\n")
            openFile.write("region = %s" % self.region_line_edit.text())
            openFile.close()

        with open(os.path.join(AWS_PATH, "credentials"), "w") as openFile:
            openFile.write("[default]\n")
            openFile.write("aws_access_key_id = %s\n" % self.id_line_edit.text())
            openFile.write("aws_secret_access_key = %s" % self.access_key_line_edit.text())

        self.hide()


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


def setup_sync_globals(aws_company_name):
    print('Make sure aws credentials are here')
    print('Download the google docs json file')
    print('create the sync.json file')
    config_folder = os.path.dirname(user_config())
    sheets_name = '{}_SYNC_THING'.format(aws_company_name.upper().replace('-', '_'))
    d_ = {
            "sync": {
                "syncthing": {
                    "aws_bucket_url": "https://{}.s3.amazonaws.com".format(aws_company_name),
                    "aws_company_name": aws_company_name,
                    "sheets_config_path": "{}\\sync\\client.json".format(config_folder),
                    "sheets_name": sheets_name,
                }
            }
         }


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
             "default_branch": {},
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


def add_aws_credentials():
    """
    Checks for AWS credentials, if it doesn't find them it launches a dialog
    :return:
    """
    if not os.path.exists(os.path.join(AWS_PATH, 'credentials')):
        dialog = AWSDialog()
        dialog.exec_()
    else:
        print('Found AWS Credentials!')


if __name__ == "__main__":
    app = QtWidgets.QApplication([])
    form = QuickSync()
    form.show()
    app.exec_()
    # setup_sync()
    # $create_default_globals()
