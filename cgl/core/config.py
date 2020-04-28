import os
import logging
import sys
import json
from cgl.core.utils.read_write import load_json


class Configuration(object):
    """

    This assumes that proper config files are in place - at minimum a default globals script to read from.

    """
    LOADED_CONFIG = {}

    def __init__(self, company=None, project=None, proj_management=None):
        self.user_config = os.path.join(os.path.expanduser('~'), 'Documents', 'cglumberjack', 'user_globals.json')
        print self.user_config
        if not os.path.exists(self.user_config):
            logging.info('User Config Not Found: %s' % self.user_config)
            return
        user_globals = load_json(self.user_config)
        if not os.path.exists(user_globals['globals']):
            logging.info('No Globals Found at %s' % self.globals)
            return
        self.globals = load_json(user_globals['globals'])
        print self.globals
        Configuration.LOADED_CONFIG['app'] = self.globals


    # def make_cglumberjack_dir(self):
    #     if not os.path.exists(self.cg_lumberjack_dir):
    #         os.makedirs(self.cg_lumberjack_dir)

    # def make_company_global_dir(self):
    #     from cgl.core.utils.general import cgl_copy
    #     default_global = os.path.join(self.cg_lumberjack_dir, 'globals.json')
    #     to_path = os.path.join(self.company_global_dir, 'globals.json')
    #     if os.path.exists(self.company_global_dir):
    #         print 'Copying from %s to %s' % (default_global, to_path)
    #         if 'globals.json' not in os.listdir(self.company_global_dir):
    #             cgl_copy(default_global, to_path)
    #             if self.proj_management:
    #                 self.update_proj_management()
    #     else:
    #         print '%s does not exist' % self.company_global_dir
    #         os.makedirs(self.company_global_dir)
    #         cgl_copy(default_global, to_path)
    #         if self.proj_management:
    #             self.update_proj_management()

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

    def __init__(self, user_email=None, user_name=None, current_path=None, my_tasks=None):
        # TODO - try the ENV VARS before this.
        self.user_config_path = user_config()
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
    return get_globals()


def user_config():
    """
    get the location of the user_config()
    :return: string of path
    """
    # do they have an env variable
    try:
        user_globals_path = os.getenv('cgl_user_globals')
        if os.path.exists(user_globals_path):
            return user_globals_path
    except TypeError:
        print('No cgl_user_globals ENV variable found. Assuming location.')
        return os.path.join(os.path.expanduser('~\\Documents'), 'cglumberjack', 'user_globals.json')


def get_user_globals():
    # do they have an env variable
    try:
        user_globals_path = os.getenv('cgl_user_globals')
        if os.path.exists(user_globals_path):
            return load_json(user_globals_path)
    except TypeError:
        print('No cgl_user_globals ENV variable found. Assuming location.')
        if os.path.exists(os.path.join(os.path.expanduser('~\\Documents'), 'cglumberjack', 'user_globals.json')):
            return load_json(os.path.join(os.path.expanduser('~\\Documents'), 'cglumberjack', 'user_globals.json'))
        else:
            print('No Globals Found at %s:' % os.path.join(os.path.expanduser('~\\Documents'), 'cglumberjack',
                                                           'user_globals.json'))
            return {}


def get_globals():
    if 'globals' in get_user_globals().keys():
        globals_path = get_user_globals()['globals']
        if globals_path:
            return load_json(globals_path)
        else:
            print('No user_globals found at %s' % user_config())
    else:
        print('No user_globals found at %s' % user_config())





