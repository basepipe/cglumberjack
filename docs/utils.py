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
    os.chdir('../../../docs')
    p = subprocess.Popen('make.bat html')


def open_html(file_name):
    url = file_name
    webbrowser.register('chrome', None, webbrowser.BackgroundBrowser("C://Program Files (x86)//Google//Chrome//Application//chrome.exe"))
    webbrowser.get('chrome').open(url)


if __name__ == '__main__':
    make_build()
    open_html(os.path.join(html_root, 'index.html'))