import os
import logging
import sys
import json


class Configuration(object):
    """

    This assumes that proper config files are in place - at minimum a default globals script to read from.

    """
    LOADED_CONFIG = {}
    user_dir = os.path.expanduser("~")
    if 'Documents' in user_dir:
        cg_lumberjack_dir = os.path.join(user_dir, 'cglumberjack')
    else:
        cg_lumberjack_dir = os.path.join(user_dir, 'Documents', 'cglumberjack')
    user_config = os.path.join(cg_lumberjack_dir, 'user_globals.json')

    def __init__(self, company=None, proj_management=None):
        if not os.path.exists(self.user_config):
            logging.info('User Config Not Found: %s' % self.user_config)
        self.globals = self._load_json(self.user_config)['globals']
        if not os.path.exists(self.globals):
            logging.info('No Globals Found at %s' % self.globals)
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
            logging.debug('Global Config: %s' % global_cfg)
            cfg = {'cg_lumberjack_dir': os.path.dirname(self.globals)}
            if os.path.isfile(global_cfg):
                cfg.update(self._load_json(global_cfg))
            if os.path.isfile(app_cfg):
                cfg.update(self._load_json(app_cfg))
            Configuration.LOADED_CONFIG['app'] = cfg

    def make_cglumberjack_dir(self):
        if not os.path.exists(self.cg_lumberjack_dir):
            os.makedirs(self.cg_lumberjack_dir)

    def make_company_global_dir(self):
        from src.core.util import cgl_copy
        default_global = os.path.join(self.cg_lumberjack_dir, 'globals.json')
        to_path = os.path.join(self.company_global_dir, 'globals.json')
        if os.path.exists(self.company_global_dir):
            print 'Copying from %s to %s' % (default_global, to_path)
            if 'globals.json' not in os.listdir(self.company_global_dir):
                cgl_copy(default_global, to_path)
                if self.proj_management:
                    self.update_proj_management()
        else:
            print '%s does not exist' % self.company_global_dir
            os.makedirs(self.company_global_dir)
            cgl_copy(default_global, to_path)
            if self.proj_management:
                self.update_proj_management()

    def update_proj_management(self):
        json_file = os.path.join(self.company_global_dir, 'globals.json')
        config_dict = self._load_json(json_file)
        config_dict['account_info']['project_management'] = self.proj_management
        self._write_json(json_file, config_dict)

    def _find_config_file(self):
        template_folder = os.path.join(os.path.dirname(os.path.dirname(__file__)), "cfg")
        app_name = os.path.basename(sys.argv[0])
        # this doesn't seem to be used but it's a great idea
        app_cfg = os.path.join(template_folder, os.path.splitext(app_name)[0] + ".json")
        global_cfg = os.path.join(self.cg_lumberjack_dir, 'globals.json')
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

    def __init__(self, user_email=None, user_name=None, current_path=None, my_tasks=None):
        if os.path.exists(self.user_config_path):
            self.d = self._load_json(self.user_config_path)
        self.current_path = current_path
        if my_tasks:
            self.my_tasks = my_tasks
        else:
            self.my_tasks = self.d['my_tasks']

    def update_all(self):
        self.update_path()
        self.update_my_tasks()
        self._write_json(self.d)

    def update_my_tasks(self):
        if self.my_tasks:
            self.d['my_tasks'] = self.my_tasks
        else:
            self.d['my_tasks'] = {}

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

    @staticmethod
    def update_company():
        print 'Skipping company for now'
        # if self.company:
        #     self.d['company'] = self.company

    def _write_json(self, data):
        with open(self.user_config_path, 'w') as outfile:
            json.dump(data, outfile, indent=4, sort_keys=True)

    @staticmethod
    def _load_json(filepath):
        with open(filepath) as jsonfile:
            data = json.load(jsonfile)
        return data
        

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





