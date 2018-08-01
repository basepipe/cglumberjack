import os
import sys
import yaml


class Configuration(object):
    """

    class for storing config values from files, usable simply as a dictionary

    """
    LOADED_CONFIG = {}

    def __init__(self):
        if not Configuration.LOADED_CONFIG:
            global_cfg, app_cfg = self._find_config_file()
            cfg = {}
            if os.path.isfile(global_cfg):
                cfg.update(self._load_yaml(global_cfg))
            if os.path.isfile(app_cfg):
                cfg.update(self._load_yaml(app_cfg))
            Configuration.LOADED_CONFIG['app'] = cfg

    def _find_config_file(self):
        base = os.path.join(os.path.dirname(os.path.dirname(__file__)),
                            "cfg")
        app_name = os.path.basename(sys.argv[0])
        app_cfg = os.path.join(base, os.path.splitext(app_name)[0] + ".yaml")
        # need a place here to decide where to pull 'global.yaml' from
        # load config.yaml['location']
        config_ = os.path.join(base, 'config.yaml')
        location = self._load_yaml(config_)
        loc = location['location']
        if loc == 'default':
            global_cfg = os.path.join(base, 'global.yaml')
        else:
            global_cfg = location[loc]
        return global_cfg, app_cfg

    @staticmethod
    def _load_yaml(path):
        with open(path, 'r') as stream:
            try:
                result = yaml.load(stream)
                if result:
                    return result
                else:
                    return {}
            except yaml.YAMLError as exc:
                print(exc)
                sys.exit(99)


def config():
    """
    get the whole configuration

    Returns: dict


    """
    return Configuration().LOADED_CONFIG


def app_config():
    """
    get the app configuration

    Returns: dict

    """
    return Configuration().LOADED_CONFIG['app']
