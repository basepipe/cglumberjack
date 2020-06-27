import os
import shutil
import stat
from cgl.core.utils.general import cgl_copy
from core.config import app_config

CONFIG = app_config()

DEVROOT = os.path.join(__file__.split('cglumberjack')[0], 'cglumberjack')
ROOT = r'Z:\Projects'
RELEASEROOT = r'Z:\Projects\VFX\CGlumberjack\release2'
LATEST = r'Z:\Projects\VFX\CGlumberjack\release2\latest\cglumberjack'


def latest_version_number():
    ver_nums = []
    for each in os.listdir(RELEASEROOT):
        try:
            ver_nums.append(int(each))
        except ValueError:
            pass
    return int(max(ver_nums))


def del_rw(action, name, exc):
    os.chmod(name, stat.S_IWRITE)
    os.remove(name)


def next_release_folder():
    return os.path.join(RELEASEROOT, str(latest_version_number()+1), 'cglumberjack')


def copy_to_latest():
    # TODO this really needs to be robocopy, so slow!!!
    print('copying %s to %s' % (DEVROOT, LATEST))
    cgl_copy(DEVROOT, LATEST, dest_is_folder=True)
    # shutil.copytree(DEVROOT, LATEST)


def copy_to_next_version():
    print('copying %s to %s' % (DEVROOT, next_release_folder()))
    cgl_copy(DEVROOT, next_release_folder())
    # shutil.copytree(DEVROOT, next_release_folder())


def clear_latest():
    print('deleting %s' % LATEST)
    if os.path.isdir(LATEST):
        shutil.rmtree(LATEST, onerror=del_rw)
    else:
        pass


def safe_to_release():
    root_ = CONFIG['paths']['root']
    code_root = CONFIG['paths']['code_root']
    if code_root != LATEST:
        print('code_root = ', code_root, 'not safe to release')
        return False
    elif root_ != ROOT:
        print('root = ', root_, 'not safe to release')
        return False
    else:
        return True


def do_release():
    if safe_to_release():
        # copy_to_next_version()
        # clear_latest()
        copy_to_latest()


do_release()
