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


def create_thumbnail(filepath):
    from cgl.plugins.maya.utils import create_thumb
    print('Opening: {}'.format(filepath))
    pm.openFile(filepath, f=True, loadReferenceDepth='all')
    create_thumb()


# RUN THE CODE
def run(path_object):
    load_cgl_env()
    previs = ['rig', 'mdl', 'anim', 'lay']
    render = ['shd', 'lite']
    if path_object.task in previs:
        create_thumbnail(path_object.thumb_path)
    if path_object.task == render:
        print('need arnold render script')


if __name__ == '__main__':
    run(sys.argv[1], sys.argv[2])
