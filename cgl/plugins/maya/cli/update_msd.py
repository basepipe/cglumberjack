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
    import cgl.plugins.maya.tasks.cam as cam
    print('Opening: {}'.format(filepath))
    pm.openFile(filepath, f=True, loadReferenceDepth='all')
    cam.Task().export_msd()


def fix_references(old_company, new_company, project):
    refs = pm.listReferences()
    for r in refs:
        if project in r.path:
            new_path = r.path.replace(old_company, new_company).replace(project, '{}/master'.format(project)).replace('/publish', '/default/publish')
            r.replaceWith(new_path)


def anim_msd(filepath):
    import cgl.plugins.maya.tasks.anim as anim
    pm.openFile(filepath, f=True, loadReferenceDepth='all')
    fix_references('VFX', 'cmpa-animation', '02BTH_2021_Kish')
    pm.saveFile()
    anim.Task().export_msd()


# RUN THE CODE
def run(filepath, task):
    load_cgl_env()
    if task == 'cam':
        cam_msd(filepath)
    if task == 'anim':
        anim_msd(filepath)


if __name__ == '__main__':
    run(sys.argv[1], sys.argv[2])




