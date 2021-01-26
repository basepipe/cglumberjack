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


def cam_msd(filepath):
    print(filepath)
    import cgl.plugins.maya.tasks.cam as cam
    print('Opening: {}'.format(filepath))
    pm.openFile(filepath, f=True, loadReferenceDepth='all')
    cam.Task().export_msd()


# RUN THE CODE
def run(filepath, task):
    load_cgl_env()
    if task == 'cam':
        cam_msd(filepath)


if __name__ == '__main__':
    run(sys.argv[1], sys.argv[2])




