import pprint
import os
import json
import sys
import shutil
import getpass
import datetime
from os.path import expanduser
import logging
import re
from cglcore.config import app_config


def pretty(obj):
    """
    return a pretty printed representation of an object
    Args:
        obj: the object to pretty print

    Returns:
        str:

    """
    pp = pprint.PrettyPrinter(indent=4)
    return pp.pformat(obj)


def app_name(str_=None, human=False):
    """
    return the name of the application used in settings files
    Args:
        str_: the name to map from defaults sys.argv[0]
        human: a human readable string

    Returns:
        str: name of application

    """
    supported_apps = ['maya', 'nuke', 'houdini', 'unreal', 'unity']
    if str_ is None:
        str_ = sys.argv[0]

    title = os.path.basename(str_)
    if human:
        title = title.replace("_", " ")
    title, _ = os.path.splitext(title)

    if title not in supported_apps:
        title = 'standalone'

    return title


def folder_size(folder, size=0):
    """
    gets the memory size of a folder, can also take files
    :param folder:
    :param size:
    :return:
    """

    if os.path.isdir(folder):
        for d, subdir, files in os.walk(folder):
            for name in files:
                size = size + os.path.getsize('%s/%s' % (d, name))
            for subfolder in subdir:
                folder_size('%s/%s' % (d, subfolder), size)
        return '%s mb' % (size/1000000)
    else:
        return '%s mb' % (os.path.getsize(folder)/1000000)


def current_user():
    """
    find the currently logged in user
    Returns:
        str: username

    """
    return getpass.getuser()


def timestamp():
    return datetime.datetime.now()


def home_dir():
    return expanduser("~")


def test_string_against_rules(test_string, rule, effected_label=None):
    """
    Test for any string to see if it passes any regex "rule" from the global.yaml file.
    :param test_string: string to be tested against regex
    :param rule: regex pattern to test against
    :param effected_label: PySide Label Object to effect color of.
    :return:
    """
    regex = re.compile(r'%s' % app_config()['paths']['rules'][rule])
    if re.findall(regex, test_string):
        if effected_label:
            effected_label.setStyleSheet("color: rgb(255, 255, 255);")
        return False
    else:
        if effected_label:
            effected_label.setStyleSheet("color: rgb(255, 50, 50);")
        return app_config()['paths']['rules']['%s_example' % rule]


def copy_file(src, dest):
    if not os.path.isdir(dest):
        dir_ = os.path.dirname(dest)
        if not os.path.exists(dir_):
            os.makedirs(dir_)
    if os.path.isdir(src):
        files = os.listdir(src)
        for f in files:
            copy_file(os.path.join(src, f), os.path.join(dest, f))
    else:
        logging.info('COPYING: %s -----> %s' % (src, dest))
        shutil.copyfile(src, dest)


def split_all(path):
    all_parts = []
    while 1:
        parts = os.path.split(path)
        if parts[0] == path:  # sentinel for absolute paths
            all_parts.insert(0, parts[0])
            break
        elif parts[1] == path:
            all_parts.insert(0, parts[1])
            break
        else:
            path = parts[0]
            all_parts.insert(0, parts[1])
    return all_parts


def save_json(filepath, data):
    with open(filepath, 'w') as outfile:
        json.dump(data, outfile, indent=4, sort_keys=True)


def load_json(filepath):
    with open(filepath) as jsonfile:
        data = json.load(jsonfile)
    return data


def _execute(command, return_output=False, print_output=True, methodology='local'):
    # TODO - we need to make sure this command is used everywhere we're passing commands if at all possible.
    if methodology == 'local':
        import subprocess
        logging.info('Executing Command: %s' % command)
        p = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)
        output_values = []
        if return_output or print_output:
            while True:
                output = p.stdout.readline()
                if output == '' and p.poll() is not None:
                    break
                if output:
                    if print_output:
                        print output.strip()
                    output_values.append(output.strip())
        rc = p.poll()
        if return_output:
            return output_values
        else:
            return rc
    elif methodology == 'deadline':
        # TODO - add deadline integration
        print 'deadline not yet supported'
    elif methodology == 'smedge':
        # TODO - add smedge integration
        print 'smedge not yet supported'


def check_for_latest_master(return_output=True, print_output=False):
    # TODO - probably need something in place to check if git is installed.
    code_root = app_config()['paths']['code_root']
    command = 'git remote show origin'
    os.chdir(code_root)
    output = _execute(command, return_output=return_output, print_output=print_output)

    for line in output:
        if 'pushes to master' in line:
            if 'up to date' in line:
                print 'cglumberjack code base up to date'
                return True
            else:
                print 'cglumberjack code base needs updated'
    return False


def update_master():
    code_root = app_config()['paths']['code_root']
    command = 'git pull'
    os.chdir(code_root)
    _execute(command)

