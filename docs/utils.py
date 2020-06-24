import sphinx
import os
import sys
import subprocess
import webbrowser
from core.config import app_config
from core.utils.general import cgl_execute

CONFIG = app_config()
code_root = os.path.join(CONFIG['paths']['code_root'])
html_root = os.path.join(code_root, 'docs', 'build', 'html')


def setup_path():
    """
    Sets up path object so sphinx can read cgl modules
    :return:
    """
    root_ = CONFIG['paths']['code_root']
    sys.path.append(root_)
    sys.path.append(os.path.join(root_, 'cgl'))
    sys.path.append(os.path.join(root_, 'cgl', 'core'))


def make_build():
    """
    Cleans and rebuilds documentation html file
    :return:
    """
    os.chdir(os.path.dirname(__file__))
    c = subprocess.call(['make', 'clean'], shell=True)
    p = subprocess.call(['make', 'html'], shell=True)


def open_html(file_name):
    """
    Opens index.html file in google chrome
    :param file_name: Path to html file
    :return:
    """
    url = file_name
    webbrowser.open(url)


def get_current_documented_modules(rst_name):
    """
    Function to get list of modules already listed in autodoc
     --- Modules MUST follow an automodule statement
    :param rst_name: Name of rst file containing auto documented modules
    :return: List of module names that have been documented
    """
    rst_path = os.path.join(code_root, 'docs', 'source', rst_name)
    module_list = []
    with open(rst_path) as text_file:
        lines = text_file.readlines()
        for line in lines:
            if "automodule::" in line:
                module = line.split('.')
                module_list.append(module[3].rstrip('\n'))
    return module_list


def get_directory_modules(dir_name):
    """
    Finds all python modules located in directory
    :param dir_name: Name of directory to search through
    :return: List of module names
    """
    return_list = []
    dir_path = os.path.join(code_root, 'cgl', dir_name)
    if os.path.isdir(dir_path):
        for file in os.listdir(dir_path):
            if file != "__init__.py":
                if '.py' in file and '.pyc' not in file:
                    file_split = file.split('.')
                    return_list.append(file_split[0])
    return return_list


def add_module_to_rst(rst_name, dir_name, module_name):
    rst_path = os.path.join(code_root, 'docs', 'source', rst_name)
    with open(rst_path, 'a') as f:
        f.write('\n\n%s\n========================' % module_name)
        f.write('\n.. automodule:: %s.%s\n' % (dir_name, module_name))
        f.write('\t:members:\n')


def document_directory(rst_name, dir_name):
    """
    Iterates through directory and autodocs each module found
    :param rst_name: Name of rst file to add modules to
    :param dir_name: Name of directory to iterate through
    :return:
    """
    doc_list = get_current_documented_modules(rst_name)
    dir_list = get_directory_modules(dir_name)
    for dir in dir_list:
        if dir in doc_list:
            pass
        else:
            add_module_to_rst(rst_name, dir_name, dir)


if __name__ == '__main__':
    pass
