import sys
import os
import maya.standalone
maya.standalone.initialize("Python")
import pymel.core as pm


# IMPORT THE CGL STUFF
def load_cgl_env():
    source_dir = r"C:\Users\tmikota\PycharmProjects\cglumberjack\cgl"
    sys.path.insert(0, source_dir)
    python_dev_packages = r'C:\Python27\Lib\site-packages'
    sys.path.insert(0, python_dev_packages)


def create_preview(filepath, task):
    from cgl.plugins.maya.utils import create_still_preview
    print('Opening: {}'.format(filepath))
    pm.openFile(filepath, f=True, loadReferenceDepth='all')
    create_still_preview(task)


# RUN THE CODE
def run(filepath, task):
    load_cgl_env()
    create_preview(filepath, task)


if __name__ == '__main__':
    run(sys.argv[1], sys.argv[2])
