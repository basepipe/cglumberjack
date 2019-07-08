import os
import sys
import yaml
import json
import shutil
from Qt import QtWidgets, QtCore, QtGui


class InitializeConfig(object):
    """
    This creates globals for companies.
    """
    def __init__(self, default_company=None, default_pm='', server_url=None, api_key=None, api_user=None,
                 api_script=None):
        self.server_url = server_url
        self.api_key = api_key
        self.api_user = api_user
        self.api_script = api_script
        self.user_dir = os.path.expanduser("~")
        self.default_company = default_company
        self.default_pm = default_pm
        # first priority - figure out where the cgl_directory is going to be, or currently is.
        self.cgl_dir = self.get_default_cgl_dir()
        self.user_globals = os.path.join(self.cgl_dir, 'config.json')
        self.default_globals_json = self._load_json(self.user_globals)['globals']
        self.cgl_dir = os.path.dirname(self.default_globals_json)

    def local_config_not_set(self):
        config_not_set = False
        config = self._load_json(self.default_globals_json)
        # If the config exists and has valid values just continue on
        company = config['account_info']['default_company']
        user_directory = config['account_info']['user_directory']
        project_management = config['account_info']['project_management']
        root_ = config['paths']['root']

        if project_management:
            if project_management == 'ftrack':
                if not config['ftrack']['server_url']:
                    config_not_set = True
                if not config['ftrack']['api_key']:
                    config_not_set = True
                if not config['ftrack']['api_user']:
                    config_not_set = True
            if project_management == 'shotgun':
                if not config['shotgun']['url']:
                    config_not_set = True
                if not config['shotgun']['api_key']:
                    config_not_set = True
                if not config['shotgun']['api_script']:
                    config_not_set = True
                if not config['shotgun']['username']:
                    config_not_set = True
        return config_not_set

    def get_default_cgl_dir(self):
        if 'Documents' in self.user_dir:
            cg_lumberjack_dir = os.path.join(self.user_dir, 'cglumberjack')
        else:
            cg_lumberjack_dir = os.path.join(self.user_dir, 'Documents', 'cglumberjack')
        return cg_lumberjack_dir

    def create_default_globals(self):
        """
        Creates default globals in the correct direcgory if they don't exist - this will pull from the default CGL
        configuration.
        :return:
        """
        base = os.path.join(os.path.dirname(os.path.dirname(__file__)), "cfg", "global_template.json")
        to_path = self.default_globals_json
        if os.path.exists(os.path.dirname(self.default_globals_json)):
            # make the "studio level" global.yaml
            if 'global.json' not in os.listdir(self.cgl_dir):
                print 'cant find global.json in %s' % self.cgl_dir
                shutil.copy2(base, to_path)
                print 'Created Global: %s' % to_path
            else:
                print 'Found Globals at: %s' % to_path
        else:
            os.makedirs(os.path.dirname(self.default_globals_json))
            shutil.copy2(base, to_path)
            print 'Created Global: %s' % to_path

    def set_default_location(self):
        config_ = self._load_json(self.default_globals_json)
        config_['account_info']['user_directory'] = self.cgl_dir
        # self._write_yaml(self.default_globals, config)
        self._write_json(self.default_globals_json, config_)

    def set_proj_management_details(self):
        if self.default_pm != 'lumbermill':
            from cglui.startup import do_gui_init
            if self.local_config_not_set():
                app = do_gui_init()
                config_ = self._load_json(self.default_globals_json)
                dialog = CheckGlobalsDialog(company=config_['account_info']['default_company'],
                                            project_management=config_['account_info']['project_management'],
                                            user_directory=config_['account_info']['user_directory'],
                                            config_dict=config_)
                dialog.show()
                app.exec_()
                contents = dialog.contents

                self.default_pm = contents['project_management']
                self.server_url = contents['api_server']
                self.api_key = contents['api_key']
                self.api_user = contents['api_user']
                self.default_company = contents['company']

                config_['account_info']['default_company'] = self.default_company
                config_['paths']['root'] = contents['root']
                config_['account_info']['project_management'] = self.default_pm

                if self.default_pm == 'ftrack':
                    config_['ftrack']['server_url'] = self.server_url
                    config_['ftrack']['api_key'] = self.api_key
                    config_['ftrack']['api_user'] = self.api_user
                    # self._write_yaml(self.default_globals, config)
                    print config_['ftrack']
                    print config_['paths']
                    self._write_json(self.default_globals_json, config_)
                elif self.default_pm == 'shotgun':
                    config_['shotgun']['url'] = self.server_url
                    config_['shotgun']['api_key'] = self.api_key
                    config_['shotgun']['api_script'] = self.api_script
                    config_['shotgun']['username'] = self.api_user
                    # self._write_yaml(self.default_globals, config)
                    self._write_json(self.default_globals_json, config_)

    @staticmethod
    def _write_json(filepath, data):
        print filepath, '---------------------------'
        with open(filepath, 'w') as outfile:
            json.dump(data, outfile, indent=4, sort_keys=True)

    @staticmethod
    def _load_json(filepath):
        with open(filepath) as jsonfile:
            data = json.load(jsonfile)
        return data


class Configuration(object):
    """

    This asssumes that proper config files are in place - at minimum a default globals script to read from.

    """
    LOADED_CONFIG = {}
    user_dir = os.path.expanduser("~")
    if 'Documents' in user_dir:
        cg_lumberjack_dir = os.path.join(user_dir, 'cglumberjack')
    else:
        cg_lumberjack_dir = os.path.join(user_dir, 'Documents', 'cglumberjack')
    user_config = os.path.join(cg_lumberjack_dir, 'config.json')

    def __init__(self, company=None, proj_management=None):
        if not os.path.exists(self.user_config):
            dialog = 'tests'
            print 'User Config Not Found: %s' % self.user_config
        self.globals = self._load_json(self.user_config)['globals']
        if not os.path.exists(self.globals):
            print 'No Globals Found at %s' % self.globals
            return
        else:
            self.cg_lumberjack_dir = os.path.dirname(self.globals)
        self.proj_management = None
        if proj_management:
            self.proj_management = proj_management
        if company:
            Configuration.LOADED_CONFIG = {}
        if not Configuration.LOADED_CONFIG:
            self.make_cglumberjack_dir()
            if company:
                self.company_global_dir = os.path.join(self.cg_lumberjack_dir, 'companies', company)
            else:
                self.company_global_dir = None
            global_cfg, app_cfg = self._find_config_file()
            print 'Global Config:', global_cfg
            cfg = {}
            cfg['cg_lumberjack_dir'] = os.path.dirname(self.globals)
            if os.path.isfile(global_cfg):
                cfg.update(self._load_json(global_cfg))
            if os.path.isfile(app_cfg):
                cfg.update(self._j(app_cfg))
            Configuration.LOADED_CONFIG['app'] = cfg

    def make_cglumberjack_dir(self):
        base = os.path.join(os.path.dirname(os.path.dirname(__file__)), "cfg", "global_template.json")
        to_path = os.path.join(self.cg_lumberjack_dir, 'global.json')
        if os.path.exists(self.cg_lumberjack_dir):
            # make the "studio level" global.yaml
            if 'global.json' not in os.listdir(self.cg_lumberjack_dir):
                # shutil.copy2(base, to_path
                pass
        else:
            os.makedirs(self.cg_lumberjack_dir)
            # shutil.copy2(base, to_path)

    def make_company_global_dir(self):
        default_global = os.path.join(self.cg_lumberjack_dir, 'global.json')
        to_path = os.path.join(self.company_global_dir, 'global.json')
        if os.path.exists(self.company_global_dir):
            print 'Copying from %s to %s' % (default_global, to_path)
            if 'global.json' not in os.listdir(self.company_global_dir):
                shutil.copy2(default_global, to_path)
                if self.proj_management:
                    self.update_proj_management()
        else:
            print '%s does not exist' % self.company_global_dir
            os.makedirs(self.company_global_dir)
            shutil.copy2(default_global, to_path)
            if self.proj_management:
                self.update_proj_management()

    def update_proj_management(self):
        json_file = os.path.join(self.company_global_dir, 'global.json')
        config_dict = self._load_json(json_file)
        config_dict['account_info']['project_management'] = self.proj_management
        self._write_json(json_file, config_dict)

    def _find_config_file(self):
        template_folder = os.path.join(os.path.dirname(os.path.dirname(__file__)), "cfg")
        app_name = os.path.basename(sys.argv[0])
        # this doesn't seem to be used but it's a great idea
        app_cfg = os.path.join(template_folder, os.path.splitext(app_name)[0] + ".json")
        global_cfg = os.path.join(self.cg_lumberjack_dir, 'global.json')
        """
        This is for when we want to start having globals for each company
        if self.company_global_dir:
            if os.path.exists(self.company_global_dir):
                global_cfg = os.path.join(self.company_global_dir, 'global.json')
                if not os.path.exists(global_cfg):
                    self.make_company_global_dir()
            else:
                self.make_company_global_dir()
                global_cfg = os.path.join(self.company_global_dir, 'global.json')
        else:
            if os.path.exists(self.cg_lumberjack_dir):
                global_cfg = os.path.join(self.cg_lumberjack_dir, 'global.json')
            else:
                self.make_cglumberjack_dir()
                global_cfg = os.path.join(self.cg_lumberjack_dir, 'global.json')

        print 'Global Config Location: ', global_cfg
        """
        return global_cfg, app_cfg

    @staticmethod
    def _load_json(filepath):
        with open(filepath) as jsonfile:
            data = json.load(jsonfile)
        return data

    @staticmethod
    def _write_json(filepath, data):
        with open(filepath, 'w') as outfile:
            json.dump(data, outfile, indent=4, sort_keys=True)


class UserConfig(object):
    user_config_path = Configuration().user_config

    def __init__(self, company=None, user_email=None, user_name=None, current_path=None):
        if os.path.exists(self.user_config_path):
            self.d = self._load_json(self.user_config_path)
        else:
            return None
        self.current_path = current_path
        if company:
            self.company = company
        else:
            self.company = self.d['company']
        if user_email:
            self.user_email = user_email
        else:
            self.user_email = self.d['user_email']
        if user_name:
            self.user_name = user_name
        else:
            self.user_name = self.d['user_name']

    def update_all(self):
        self.update_path()
        self.update_user_email()
        self.update_user_name()
        self.update_company()
        self._write_json(self.d)

    def update_path(self):
        if self.current_path:
            self.d['previous_path'] = self.current_path
            number = 1
            try:
                if self.current_path in self.d['previous_paths']:
                    number = self.d['previous_paths'][self.current_path]
                    number += 1
                self.d['previous_paths'][self.current_path] = number
            except KeyError:
                self.d['previous_paths'] = {self.current_path: number}

    def update_user_email(self):
        if self.user_email:
            self.d['user_email'] = self.user_email

    def update_user_name(self):
        if self.user_name:
            self.d['user_name'] = self.user_name

    def update_company(self):
        if self.company:
            self.d['company'] = self.company

    def _write_json(self, data):
        with open(self.user_config_path, 'w') as outfile:
            json.dump(data, outfile, indent=4, sort_keys=True)

    @staticmethod
    def _load_json(filepath):
        with open(filepath) as jsonfile:
            data = json.load(jsonfile)
        return data


class CheckGlobalsDialog(QtWidgets.QDialog):

    def __init__(self, company, project_management, user_directory, config_dict):
        QtWidgets.QDialog.__init__(self)
        self.app_config = config_dict
        self.proj_management_label = QtWidgets.QLabel('Project Management')
        self.contents = {}
        self.company = company
        self.root = ''
        layout = QtWidgets.QVBoxLayout(self)
        self.proj_management_combo = QtWidgets.QComboBox()
        self.proj_management_combo.addItems(['', 'lumbermill', 'ftrack', 'shotgun', 'google_docs'])
        self.red_palette = QtGui.QPalette()
        self.red_palette.setColor(self.foregroundRole(), QtGui.QColor(255, 0, 0))
        self.green_palette = QtGui.QPalette()
        self.green_palette.setColor(self.foregroundRole(), QtGui.QColor(0, 255, 0))
        self.black_palette = QtGui.QPalette()
        self.black_palette.setColor(self.foregroundRole(), QtGui.QColor(0, 0, 0))

        company_label = QtWidgets.QLabel('Your Company')
        self.company_line_edit = QtWidgets.QLineEdit()
        self.server_label = QtWidgets.QLabel('server url:')
        self.api_key_label = QtWidgets.QLabel('api key:')
        self.api_user_label = QtWidgets.QLabel('api user:')
        self.api_script_label = QtWidgets.QLabel('api script:')
        self.root_label = QtWidgets.QLabel('root on disk:')
        self.server_line_edit = QtWidgets.QLineEdit()
        self.api_key_line_edit = QtWidgets.QLineEdit()
        self.api_user_line_edit = QtWidgets.QLineEdit()
        self.api_script_line_edit = QtWidgets.QLineEdit()
        self.root_line_edit = QtWidgets.QLineEdit()
        self.choose_folder_button = QtWidgets.QToolButton()
        self.choose_folder_button.setText('...')

        self.api_key = self.api_key_line_edit.text()
        self.api_script = self.api_script_line_edit.text()
        self.api_user = self.api_user_line_edit.text()
        self.project_management = self.proj_management_combo.currentText()
        self.api_server = self.server_line_edit.text()

        self.cancel_button = QtWidgets.QPushButton('Cancel')
        self.ok_button = QtWidgets.QPushButton('Ok')
        self.button = ''
        self.ok_button.setEnabled(False)

        self.root_line_edit.setText(self.app_config['paths']['root'])
        self.company_line_edit.setText(self.app_config['account_info']['default_company'])

        self.project_management = self.app_config['account_info']['project_management']
        if self.project_management:
            index = self.proj_management_combo.findText(self.project_management)
            self.proj_management_combo.setCurrentIndex(index)
        if self.project_management == 'ftrack' or self.project_management == 'shotgun':
            self.api_key_line_edit.setText(self.app_config[self.project_management]['api_key'])
            self.api_script_line_edit.setText(self.app_config['shotgun']['api_script'])
            self.api_user_line_edit.setText(self.app_config[self.project_management]['api_user'])
            self.server_line_edit.setText(self.app_config[self.project_management]['server_url'])

        button_layout = QtWidgets.QHBoxLayout()
        button_layout.addStretch(1)
        button_layout.addWidget(self.cancel_button)
        button_layout.addWidget(self.ok_button)


        self.message = QtWidgets.QLabel()

        self.grid_layout = QtWidgets.QGridLayout()
        self.grid_layout.addWidget(company_label, 0, 0)
        self.grid_layout.addWidget(self.company_line_edit, 0, 1)
        self.grid_layout.addWidget(self.root_label, 1, 0)
        self.grid_layout.addWidget(self.root_line_edit, 1, 1)
        self.grid_layout.addWidget(self.choose_folder_button, 1, 2)
        self.grid_layout.addWidget(self.proj_management_label, 2, 0)
        self.grid_layout.addWidget(self.proj_management_combo, 2, 1)
        self.grid_layout.addWidget(self.server_label, 3, 0)
        self.grid_layout.addWidget(self.server_line_edit, 3, 1)
        self.grid_layout.addWidget(self.api_key_label, 4, 0)
        self.grid_layout.addWidget(self.api_key_line_edit, 4, 1)
        self.grid_layout.addWidget(self.api_user_label, 5, 0)
        self.grid_layout.addWidget(self.api_user_line_edit, 5, 1)
        self.grid_layout.addWidget(self.api_script_label, 6, 0)
        self.grid_layout.addWidget(self.api_script_line_edit, 6, 1)


        layout.addLayout(self.grid_layout)
        layout.addWidget(self.message)
        layout.addLayout(button_layout)

        self.proj_management_combo.currentIndexChanged.connect(self.on_pm_changed)
        self.server_line_edit.textChanged.connect(self.on_line_edit_changed)
        self.api_user_line_edit.textChanged.connect(self.on_line_edit_changed)
        self.api_script_line_edit.textChanged.connect(self.on_line_edit_changed)
        self.api_key_line_edit.textChanged.connect(self.on_line_edit_changed)
        self.ok_button.clicked.connect(self.on_ok_clicked)
        self.cancel_button.clicked.connect(self.cancel_clicked)
        self.choose_folder_button.clicked.connect(self.on_get_folder_clicked)
        self.get_input()
        self.hide_api_info()
        self.on_pm_changed()

    def on_get_folder_clicked(self):
        folder = QtWidgets.QFileDialog.getExistingDirectory()
        self.root_line_edit.setText(folder)

    def cancel_clicked(self):
        self.accept()

    def hide_api_info(self):
        self.server_label.hide()
        self.api_key_label.hide()
        self.api_user_label.hide()
        self.server_line_edit.hide()
        self.api_key_line_edit.hide()
        self.api_user_line_edit.hide()
        self.api_script_label.hide()
        self.api_script_line_edit.hide()

    def show_api_info(self):
        self.server_label.show()
        self.api_key_label.show()
        self.api_user_label.show()
        self.server_line_edit.show()
        self.api_key_line_edit.show()
        self.api_user_line_edit.show()

    def on_pm_changed(self):
        self.api_key_line_edit.setText('')
        self.api_script_line_edit.setText('')
        self.api_user_line_edit.setText('')
        self.server_line_edit.setText('')
        if self.project_management == 'ftrack' or self.project_management == 'shotgun':
            self.api_key_line_edit.setText(self.app_config[self.project_management]['api_key'])
            self.api_script_line_edit.setText(self.app_config['shotgun']['api_script'])
            self.api_user_line_edit.setText(self.app_config[self.project_management]['api_user'])
            self.server_line_edit.setText(self.app_config[self.project_management]['server_url'])
        if self.proj_management_combo.currentText() == 'lumbermill':
            self.hide_api_info()
        elif self.proj_management_combo.currentText() == 'ftrack':
            self.show_api_info()
        elif self.proj_management_combo.currentText() == 'shotgun':
            self.show_api_info()
            self.api_script_label.show()
            self.api_script_line_edit.show()
        self.get_input()
            
    def get_input(self):
        self.api_key = self.api_key_line_edit.text()
        self.api_script = self.api_script_line_edit.text()
        self.api_user = self.api_user_line_edit.text()
        self.project_management = self.proj_management_combo.currentText()
        self.api_server = self.server_line_edit.text()
        self.company = self.company_line_edit.text()
        self.root = self.root_line_edit.text()

    def on_line_edit_changed(self):
        # TODO make these dictionairies
        self.get_input()

        print self.project_management

        if self.project_management == 'ftrack':
            info = {'api_server': self.api_server,
                    'api_key': self.api_key,
                    'api_user': self.api_user,
                    'company': self.company,
                    'api_script': self.api_script,
                    'project_management': 'ftrack',
                    'root': self.root
                    }
        if self.project_management == 'shotgun':
            info = {'api_server': self.api_server,
                    'api_key': self.api_key,
                    'api_user': self.api_user,
                    'api_script': self.api_script,
                    'company': self.company,
                    'project_management': 'shotgun',
                    'root': self.root
                    }
        elif self.project_management == 'lumbermill':
            info = {'api_server': self.api_server,
                    'api_key': self.api_key,
                    'api_user': self.api_user,
                    'api_script': self.api_script,
                    'company': self.company,
                    'project_management': 'lumbermill',
                    'root': self.root
                    }
        if '' in info:
            self.ok_button.setEnabled(False)
        else:
            self.ok_button.setEnabled(True)
        self.contents = info

    def on_ok_clicked(self):
        self.accept()
        return self.contents
        

def config():
    """
    get the whole configuration

    Returns: dict


    """
    return Configuration().LOADED_CONFIG


def app_config(company=None, proj_management=None):
    """
    get the app configuration

    Returns: dict

    """
    return Configuration(company=company, proj_management=proj_management).LOADED_CONFIG['app']


def user_config():
    """
    get the location of the user_config()
    :return: string of path
    """
    return Configuration().user_config





