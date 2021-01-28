import os
import glob
from cgl.plugins.Qt import QtCore, QtWidgets
from cgl.apps.magic_browser.main import CGLumberjack, CGLumberjackWidget
from cgl.core.utils.general import current_user, cgl_execute
from cgl.ui.widgets.dialog import InputDialog
import logging
from cgl.core.utils.general import create_file_dirs, cgl_copy
from cgl.core.path import PathObject
from cgl.core.config.config import ProjectConfig, user_config
from cgl.plugins.maya.utils import get_namespace, create_tt, clean_tt, basic_playblast
try:
    import pymel.core as pm
except:
    print('Skipping pymel.core, outside of maya')


class BrowserWidget(CGLumberjackWidget):
    def __init__(self, parent=None, path=None,
                 show_import=False, show_reference=False, set_to_publish=True, cfg=None):
        super(BrowserWidget, self).__init__(parent=parent, path=path, show_import=show_import,
                                            show_reference=show_reference, set_to_publish=set_to_publish, cfg=cfg)

    def open_clicked(self):
        print('Opening: %s' % self.path_object.path_root)

    def import_clicked(self):
        for selection in self.source_selection:
            # base_, ext = os.path.splitext(selection)
            import_file(selection, namespace=None)

    def reference_clicked(self):
        for selection in self.source_selection:
            # base_, ext = os.path.splitext(selection)
            reference_file(selection, namespace=None)


class AppMainWindow(CGLumberjack):
    def __init__(self, parent=None, path=None, user_info=None, cfg=None):
        CGLumberjack.__init__(self, parent, user_info=user_info, previous_path=path, sync_enabled=False, cfg=cfg)
        print('Application Path path is %s' % path)
        self.setCentralWidget(BrowserWidget(self, show_import=True, show_reference=True, path=path, cfg=cfg))


def get_scene_name():
    """
    get current scene name
    :return:
    """
    return pm.sceneName()


def scene_object():
    """
    returns PathObject of curent scene
    :return:
    """
    return PathObject(pm.sceneName())


def open_file(filepath):
    """
    Open File: filepath
    :param filepath:
    :return:
    """
    if os.path.isfile(filepath):
        return pm.openFile(filepath, f=True, loadReferenceDepth='all')


def save_file():
    """
    Save Current File
    :return:
    """
    return pm.saveFile()


def save_file_as(filepath):
    """
    save current file as
    :param filepath:
    :return:
    """
    return pm.saveAs(filepath)


def import_file(filepath, namespace=None):
    """
    imports file into a scene.
    :param filepath:
    :param namespace:
    :return:
    """
    print(filepath)
    file_object = PathObject(filepath)
    if file_object.context == 'source':
        dialog = InputDialog(message='Are you sure you want to import a source file? This is not recommended')
        if dialog.button == 'Cancel':
            return
    if not namespace:
        namespace = get_namespace(filepath)
    if os.path.isfile(filepath):
        if file_object.task == 'bndl':
            if filepath.endswith('.json') or filepath.endwith('.msa'):
                from cgl.plugins.maya.tasks.bndl import bundle_import
                bundle_import(filepath)
                return filepath
        if file_object.task == 'lay':
            if filepath.endswith('.json') or filepath.endswith('.msa'):
                from cgl.plugins.maya.tasks.lay import main_import
                main_import(filepath)
                return filepath
        if filepath.endswith('.mb') or filepath.endswith('.ma'):
            return pm.importFile(filepath, namespace=namespace)


def import_task(task=None, reference=False, **kwargs):
    """
    imports the latest version of the specified task into the scene.
    :param task:
    :param reference:
    :return:
    """
    if not task:
        task = scene_object().task
    class_ = get_task_class(task)
    print(class_)
    if reference:
        print(1)
        return class_().import_latest(task=task, reference=reference, **kwargs)
    else:
        print(2)
        return class_().import_latest(**kwargs)


def reference_file(filepath, namespace=None):
    """
    creates a "reference" of a file, this is a convenience function to be used in various software plugins
    to promote continuity accross plugins
    :param filepath:
    :return:
    """
    if not namespace:
        namespace = get_namespace(filepath)
    print(filepath)
    if os.path.exists(filepath):
        print('filepath: ', filepath)
        return pm.createReference(filepath, namespace=namespace, ignoreVersion=True, loadReferenceDepth='all')
    else:
        print('File does not exist: {}'.format(filepath))


def confirm_prompt(title='title', message='message', button='Ok'):
    """
    standard confirm prompt, this is an easy wrapper that allows us to do
    confirm prompts in the native language of the application while keeping conventions
    :param title:
    :param message:
    :param button: single button is created with a string, multiple buttons created with array
    :return:
    """
    from utils import confirm_prompt as cp
    cp(title=title, message=message, button=button)


def select(nodes=None, d=True):
    """
    allows us to select something in the scene.
    :param nodes: node to select (or string)
    :param d: if true - deselect everything
    :return:
    """
    pm.select(nodes)


def version_up(vtype='minor', copy_render=False):
    """
    versions up the current scene
    :param vtype: minor or major
    :param copy_render: if True it copies everything in the render folder as part of the version up.
    :return:
    """
    path_object = scene_object()
    current_render_folder = path_object.copy(context='render', filename=None, ext=None).path_root
    if vtype == 'minor':
        new_version = path_object.new_minor_version_object()
    elif vtype == 'major':
        new_version = path_object.next_major_version()

    if new_version.context == 'source':
        new_source = new_version.copy()
        new_render = new_version.copy(context='render')
    else:
        new_render = new_version.copy()
        new_source = new_version.copy(context='source')

    new_render_folder = os.path.dirname(new_render.path_root)
    new_source_folder = os.path.dirname(new_source.path_root)
    print('Creating Version Dirs: {}'.format(new_source_folder))
    print('Creating Version Dirs: {}'.format(new_render_folder))
    create_file_dirs(new_source.path_root)
    create_file_dirs(new_render_folder)
    if copy_render:
        print('Copying {} to {}'.format(current_render_folder, new_render_folder))
        cgl_copy(current_render_folder, new_render_folder)
    return save_file_as(new_source.path_root)


def export_selected(to_path, ext='mb'):
    """
    exports selected geometry to specified type.
    :param to_path: path to export to
    :param type: type of geo to export according to ext: obj, fbx, abc, usd, blnd
    :return:
    """
    geo = pm.ls(sl=True)
    if geo:
        create_file_dirs(to_path)
        if ext == 'mb':
            return pm.export(pm.exportSelected(to_path, typ='mayaBinary'))
        elif ext == 'ma':
            return pm.export(pm.exportSelected(to_path, typ='mayaAscii'))


def create_turntable(length=180, task=False):
    """
    Creates a turntable around the given "task" object (for example 'mdl')
    :param length:
    :param task: if True creates a turntable around existing geo that bears the task's name. Rig or mdl for example.
    :return:
    """
    if task:
        if not pm.objExists(task):
            confirm_prompt('No object %s found')
            return
        else:
            pm.select(task)
    if not pm.ls(sl=True):
        confirm_prompt(title='Turntable', message='Nothing Selected. \nSelect an object and try again')
        return
    else:
        selected = pm.ls(sl=True)[0]

    create_tt(length=length, tt_object=selected)


def clean_turntable():
    """
    removes the turntable from the scene
    :return:
    """
    po = PathObject(pm.sceneName())
    clean_tt(po.task)
    pass


def render(preview=False):
    if preview:
        basic_playblast(path_object=scene_object())
    else:
        launch_preflight(task='render')


def review():
    from cgl.core.project import do_review
    playblast_seq = scene_object().copy(context='render', filename='playblast.####.jpg')
    if glob.glob(playblast_seq.path_root.replace('####', '*')):
        print('exists - reviewing')
        do_review(progress_bar=None, path_object=playblast_seq)


def launch_preflight(path_object=None, task=None):
    """
    Launches preflight window.
    :param task:
    :param path_object:
    :return:
    """
    import cgl.plugins.preflight.main as main
    reload(main)
    if not path_object:
        path_object = scene_object()
    if not task:
        task = path_object.task
    pf_mw = main.Preflight(parent=None, software='maya', preflight=task, path_object=path_object)
    pf_mw.show()


def publish():
    """

    :return:
    """
    # Try a Preflight First
    launch_preflight()
    # If no preflight - let them know that we need one.
    # Check if there is a preflight publish option under the tasks
    # publish_object = scene_object().publish()
    # return publish_object


def launch_():
    scene_name = get_scene_name()
    scene = PathObject(scene_name)
    location = '%s/*' % scene.split_after('shot')
    cfg = ProjectConfig(scene_object())
    config = cfg.project_config
    project_management = config['account_info']['project_management']
    users = config['project_management'][project_management]['users']
    if current_user() in users:
        user_info = users[current_user()]
        app = QtWidgets.QApplication.instance()
        main_window = AppMainWindow(user_info=user_info, path=location, cfg=cfg)
        main_window.setWindowTitle('MagicBrowser: Maya')
        main_window.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        main_window.show()
        main_window.raise_()
    app.exec_()


def build(path_object=None):
    """
    runs build command for the specified task.
    :param task:
    :return:
    """
    if not path_object:
        path_object = scene_object()
    task = path_object.task
    task_class = get_task_class(task)
    task_class().build()


def get_task_class(task):
    """
    gets the class that relates to the specified task, if no task is specified the task for the current scene will
    be used.
    :param task:
    :return:
    """
    import importlib
    software = os.path.split(os.path.dirname(__file__))[-1]
    module = 'cgl.plugins.{}.tasks.{}'.format(software, task)
    module_name = task
    try:
        # python 2.7 method
        loaded_module = __import__(module, globals(), locals(), module_name, -1)
    except ValueError:
        import importlib
        # Python 3+
        loaded_module = importlib.import_module(module, module_name)
    class_ = getattr(loaded_module, 'Task')
    return class_


def screen_grab():
    """
    pops open a screen capture window and when you grab the screen it does the following:
    1) Create preview file for current scene_object()
    2) Creates thumb_file for current scene_object()
    3) Updates Project Management with new thumbnail.
    :return:
    """
    from cgl.core.utils.general import screen_grab
    screen_grab(scene_object())


def cl_update_msd(filepath):

    msd_ready = ['cam', 'anim']
    path_object = PathObject(filepath).copy(context='source', set_proper_filename=True, ext='mb')
    task = path_object.task
    if task in msd_ready:
        mayapy = user_config()['paths']['mayapy']
        update_msd = os.path.join(os.path.dirname(__file__), 'cli', 'update_msd.py')
        command = "{} {} {} {}".format(mayapy, update_msd, path_object.path_root, path_object.task)
        cgl_execute(command, new_window=True)
    else:
        print('{} not found in tasks ready for command line msd update: {}'.format(task, msd_ready))


def cl_create_thumb(filepath):
    path_object = PathObject(filepath)
    mayapy = user_config()['paths']['mayapy']
    update_preview = os.path.join(os.path.dirname(__file__), 'cli', 'create_thumb.py')
    command = "{} {} {} {}".format(mayapy, update_preview, filepath, path_object.task)
    cgl_execute(command, new_window=True)


def cl_create_preview(filepath):
    path_object = PathObject(filepath)
    mayapy = user_config()['paths']['mayapy']
    update_preview = os.path.join(os.path.dirname(__file__), 'cli', 'create_preview.py')
    command = "{} {} {} {}".format(mayapy, update_preview, filepath, path_object.task)
    cgl_execute(command, new_window=True)


if __name__ == '__main__':
    filepath = r'Z:/Projects/cmpa-animation/render/02BTH_2021_Kish/master/shots/001/0600/cam/default/publish/018.000/high/001_0600_cam.msd'
    cl_create_thumb(filepath)




