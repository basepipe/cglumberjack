import sphinx
import os
import sys
import subprocess
import webbrowser
from core.config import app_config
from core.utils.general import cgl_execute

CONFIG = app_config()
html_root = os.path.join(CONFIG['paths']['code_root'], 'docs', 'build', 'html')


def add_to_path(file_name):
    sys.path.insert(0, file_name)


def make_build():
    os.chdir(os.path.dirname(__file__))
    p = subprocess.Popen('make.bat html')


def open_html(file_name):
    url = file_name
    webbrowser.open(url)


if __name__ == '__main__':
    make_build()
    open_html(os.path.join(html_root, 'index.html'))