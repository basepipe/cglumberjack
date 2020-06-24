import sphinx
import os
import sys
import subprocess
import webbrowser
from core.config import app_config
from core.utils.general import cgl_execute

CONFIG = app_config()
html_root = os.path.join(CONFIG['paths']['code_root'], 'docs', 'build', 'html')


def setup_path():
    root_ = CONFIG['paths']['code_root']
    sys.path.append(root_)
    sys.path.append(os.path.join(root_, 'cgl'))
    sys.path.append(os.path.join(root_, 'cgl', 'core'))


def make_build():
    os.chdir(os.path.dirname(__file__))
    c = subprocess.call(['make', 'clean'], shell=True)
    p = subprocess.call(['make', 'html'], shell=True)


def open_html(file_name):
    url = file_name
    webbrowser.open(url)


if __name__ == '__main__':
    make_build()
    html_file = os.path.join(html_root, 'index.html')
    open_html(html_file)
