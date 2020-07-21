import os
import glob
from cgl.plugins.Qt import QtCore, QtWidgets
from apps.lumbermill.main import CGLumberjack, CGLumberjackWidget
from cgl.core.utils.general import current_user
import logging
from cgl.core.utils.general import create_file_dirs
from cgl.core.path import PathObject
from cgl.core.config import app_config, UserConfig
from cgl.plugins.maya.utils import get_namespace, create_tt, clean_tt, basic_playblast
import pymel.core as pm

CONFIG = app_config()
PROJ_MANAGEMENT = CONFIG['account_info']['project_management']
PADDING = CONFIG['default']['padding']
PROCESSING_METHOD = UserConfig().d['methodology']


class BrowserWidget(CGLumberjackWidget):
    def __init__(self, parent=None, path=None,
                 show_import=False):
        super(BrowserWidget, self).__init__(parent=parent, path=path, show_import=show_import)

    def open_clicked(self):
        print('Opening: %s' % self.path_object.path_root)

    def import_clicked(self):
        for selection in self.source_selection:
            base_, ext = os.path.splitext(selection)
            import_file(selection, namespace=None)
        self.parent().parent().accept()

    def reference_clicked(self):
        for selection in self.source_selection:
            base_, ext = os.path.splitext(selection)
            reference_file(selection, namespace=None)
        self.parent().parent().accept()


class AppMainWindow(CGLumberjack):
    def __init__(self, parent=None, path=None, user_info=None):
        CGLumberjack.__init__(self, parent, user_info=user_info, previous_path=path, sync_enabled=False)
        print('Application Path path is %s' % path)
        self.setCentralWidget(BrowserWidget(self, show_import=True, path=path))


class LumberObject(PathObject):

    def __init__(self, path_object=None):
        if not path_object:
            path_object = get_scene_name()
        self.data = {}
        self.root = CONFIG['paths']['root'].replace('\\', '/')
        self.company = None
        self.project = None
        self.scope = None
        self.context = None
        self.seq = None
        self.shot = None
        self.type = None
        self.asset = None
        self.variant = None
        self.user = None
        self.version = None
        self.major_version = None
        self.minor_version = None
        self.ext = None
        self.filename = None
        self.filename_base = None
        self.resolution = None
        self.frame = None
        self.aov = None
        self.render_pass = None
        self.shotname = None
        self.assetname = None
        self.task = None
        self.camera = None
        self.file_type = None
        self.frame_padding = CONFIG['default']['padding']
        self.scope_list = CONFIG['rules']['scope_list']
        self.context_list = CONFIG['rules']['context_list']
        self.path = None  # string of the properly formatted path
        self.path_root = None  # this gives the full path with the root
        self.thumb_path = None
        self.preview_path = None
        self.preview_seq = None
        self.hd_proxy_path = None
        self.start_frame = None
        self.end_frame = None
        self.frame_rate = None
        self.frame_range = None
        self.template = []
        self.filename_template = []
        self.actual_resolution = None
        self.date_created = None
        self.date_modified = None
        self.project_config = None
        self.company_config = None
        self.software_config = None
        self.asset_json = None
        self.shot_json = None
        self.task_json = None
        self.command_base = ''
        self.project_json = None
        self.status = None
        self.due = None
        self.assigned = None
        self.priority = None
        self.ingest_source = '*'
        self.processing_method = PROCESSING_METHOD
        self.proxy_resolution = '1920x1080'
        self.path_template = []
        self.version_template = []

        if isinstance(path_object, unicode):
            path_object = str(path_object)
        if isinstance(path_object, dict):
            self.process_info(path_object)
        elif isinstance(path_object, str):
            self.process_string(path_object)
        elif isinstance(path_object, PathObject):
            self.process_info(path_object.data)
        else:
            logging.error('type: %s not expected' % type(path_object))


    def render(self, processing_method=PROCESSING_METHOD):
        """
        :param processing_method: app, local, smedge, or deadline.  App - render in gui.  local - render through
        command line locally.  smedge/deadline - submit the job to a render manager for farm rendering.
        :return:
        """
        print('what is my render path?')
        pass


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
    return LumberObject(pm.sceneName())


def open_file(filepath):
    """
    Open File: filepath
    :param filepath:
    :return:
    """
    if os.path.isfile(filepath):
        return pm.openFile(filepath, f=True, loadReferenceDepth='all')


def save_file(filepath=None):
    """
    Save Current File
    :param filepath:
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
    if not namespace:
        namespace = get_namespace(filepath)
    if os.path.isfile(filepath):
        return pm.importFile(filepath, namespace=namespace)


def reference_file(filepath, namespace=None):
    """
    creates a "reference" of a file, this is a convenience function to be used in various software plugins
    to promote continuity accross plugins
    :param filepath:
    :return:
    """
    if not namespace:
        namespace = get_namespace(filepath)

    if os.path.isfile(filepath):
        print('filepath: ', filepath)
        return pm.createReference(filepath, namespace=namespace, ignoreVersion=True, loadReferenceDepth='all')


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


def version_up(vtype='minor'):
    """
    versions up the current scene
    :param vtype: minor or major
    :return:
    """
    path_object = LumberObject(pm.sceneName())
    if vtype == 'minor':
        new_version = path_object.new_minor_version_object()
    elif vtype == 'major':
        new_version = path_object.next_major_version()
    create_file_dirs(new_version.path_root)
    return save_file_as(new_version.path_root)


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

    if task:
        current_task = LumberObject(pm.sceneName()).task
        if not pm.objExists(task):
            confirm_prompt('No object %s found')
            return
        else:
            selected = task
    if not pm.ls(sl=True):
        confirm_prompt(title='Turntable', message='Nothing Selected. \nSelect an object and try again')
        return
    else:
        selected = pm.ls(sl=True)[0]

    create_tt(length=length, tt_object=selected)


def clean_turntable():
    po = LumberObject(pm.sceneName())
    clean_tt(po.task)
    pass


def export_usd_model(to_path):
    """

    :param to_path:
    :return:
    """
    pass


def export_usd_rig(to_path):
    """

    :param to_path:
    :return:
    """
    pass


def export_usd_asset(to_path):
    """

    :param to_path:
    :return:
    """
    pass


def export_usd_bundle(to_path):
    """

    :param to_path:
    :return:
    """
    pass


def export_usd_layout(to_path, lighting=False):
    """
    exports the layout of an entire scene, can include models, assets, rigged assets, bundles and lighting.
    :param to_path:
    :return:
    """
    pass


def render(preview=False):
    if preview:
        basic_playblast(path_object=LumberObject(pm.sceneName()))
    else:
        print('Rendering to Farm Now')


def review():
    from cgl.core.project import do_review
    playblast_seq = scene_object().copy(context='render', filename='playblast.####.jpg')
    if glob.glob(playblast_seq.path_root.replace('####', '*')):
        print('exists - reviewing')
        do_review(progress_bar=None, path_object=playblast_seq)


def launch_preflight(task=None):
    """
    Launches preflight window.
    :param task:
    :return:
    """
    from cgl.plugins.preflight.main import Preflight
    if not task:
        task = scene_object().task
    pf_mw = Preflight(parent=None, software='maya', preflight=task, path_object=scene_object())
    pf_mw.show()


def publish():
    """

    :return:
    """
    publish_object = scene_object().publish()
    return publish_object


def launch_():
    scene_name = get_scene_name()
    scene = LumberObject(scene_name)
    location = '%s/*' % scene.split_after('shot')
    project_management = CONFIG['account_info']['project_management']
    users = CONFIG['project_management'][project_management]['users']
    if current_user() in users:
        user_info = users[current_user()]
        app = QtWidgets.QApplication.instance()
        main_window = AppMainWindow(user_info=user_info, path=location)
        main_window.setWindowTitle('Lumbermill: Maya')
        main_window.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        main_window.show()
        main_window.raise_()
    app.exec_()