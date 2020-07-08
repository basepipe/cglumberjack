import os
import logging
# from cgl.apps.lumbermill.main import CGLumberjack, CGLumberjackWidget
from cgl.core.utils.general import current_user
from cgl.core.utils.general import create_file_dirs
from cgl.core.path import PathObject
from cgl.core.config import app_config, UserConfig
import bpy


CONFIG = app_config()
PROJ_MANAGEMENT = CONFIG['account_info']['project_management']
PADDING = CONFIG['default']['padding']
PROCESSING_METHOD = UserConfig().d['methodology']
SOFTWARE = os.path.basename(os.path.dirname(__file__))

#
# class BrowserWidget(CGLumberjackWidget):
#     def __init__(self, parent=None, path=None,
#                  show_import=False):
#         super(BrowserWidget, self).__init__(parent=parent, path=path, show_import=show_import)
#
#     def open_clicked(self):
#         print('Opening: %s' % self.path_object.path_root)
#         open_file(self.path_object.path_root)
#
#     def import_clicked(self):
#         for selection in self.source_selection:
#             base_, ext = os.path.splitext(selection)
#             import_file(selection, namespace=None)
#         self.parent().parent().accept()
#
#     def reference_clicked(self):
#         for selection in self.source_selection:
#             base_, ext = os.path.splitext(selection)
#             reference_file(selection, namespace=None)
#         self.parent().parent().accept()
#
#
# class AppMainWindow(CGLumberjack):
#     def __init__(self, parent=None, path=None, user_info=None):
#         CGLumberjack.__init__(self, parent, user_info=user_info, previous_path=path, sync_enabled=False)
#         print('Application Path path is %s' % path)
#         self.setCentralWidget(BrowserWidget(self, show_import=True, path=path))


class BlenderConfirmDialog(bpy.types.Operator):
    bl_idname = 'ui.blender_confirm_dialog'
    bl_label = 'Title'
    message = 'this is the message'

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        self.layout.label(text=self.message)

    def execute(self, context):
        return {"FINISHED"}


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

        try:
            if isinstance(path_object, unicode):
                path_object = str(path_object)
        except NameError:
            print('Python3 does not support unicode, skipping')
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
    return bpy.data.filepath


def scene_object():
    """
    returns LumberObject of curent scene
    :return:
    """
    return LumberObject(get_scene_name())


def save_file_as(filepath):
    """
    save current file as
    :param filepath:
    :return:
    """
    bpy.ops.wm.save_as_mainfile(filepath=filepath)
    return filepath


def version_up(vtype='minor'):
    """
    versions up the current scene
    :param vtype: minor or major
    :return:
    """
    path_object = LumberObject(get_scene_name())
    if vtype == 'minor':
        new_version = path_object.new_minor_version_object()
    elif vtype == 'major':
        new_version = path_object.next_major_version()
    create_file_dirs(new_version.path_root)
    return save_file_as(new_version.path_root)


def import_file(filepath='', namespace=None):
    """
    imports file into a scene.
    :param filepath:
    :param namespace:
    :return:
    """
    if filepath.endswith('fbx'):
        bpy.ops.import_scene.fbx(filepath)
    elif filepath.endswith('obj'):
        bpy.ops.import_scene.obj(filepath)



def open_file(filepath):
    """
    Open File: filepath
    :param filepath:
    :return:
    """
    return bpy.ops.wm.open_mainfile(filepath)


def save_file(filepath=''):
    """
    Save Current File
    :param filepath:
    :return:
    """
    return bpy.ops.wm.save_mainfile()


def reference_file(filepath='', namespace=None):
    """
    creates a "reference" of a file, this is a convenience function to be used in various software plugins
    to promote continuity accross plugins
    :param filepath:
    :return:
    """
    print(filepath)
    pass


def confirm_prompt(title='Lumber message:', message='This is a message', button='Ok'):
    """
    standard confirm prompt, this is an easy wrapper that allows us to do
    confirm prompts in the native language of the application while keeping conventions
    :param title:
    :param message:
    :param button: single button is created with a string, multiple buttons created with array
    :return:
    """
    try:
        bpy.utils.unregister_class(BlenderConfirmDialog)
    except RuntimeError:
        print('no class registered')
    BlenderConfirmDialog.bl_label = title
    BlenderConfirmDialog.message = message
    bpy.utils.register_class(BlenderConfirmDialog)
    bpy.ops.ui.blender_confirm_dialog('INVOKE_DEFAULT')


def select(nodes=None, d=True):
    """
    allows us to select something in the scene.
    :param nodes: node to select (or string)
    :param d: if true - deselect everything
    :return:
    """
    pass


def export_selected(to_path, ext='mb'):
    """
    exports selected geometry to specified type.
    :param to_path: path to export to
    :param type: type of geo to export according to ext: obj, fbx, abc, usd, blnd
    :return:
    """
    pass


def create_turntable(length=180, task=False):
    """
    Creates a Turntable of length around the selected object, or around a "task" object.
    This is specific to 3d applications.
    :param length:
    :param task:
    :return:
    """
    pass


def clean_turntable():
    """
    cleans up the turntable
    :return:
    """
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
    """
    renders the current scene.
    :param preview: option to render a less intensive version of the scene - a playblast from maya or a low
    quality real time render for example.
    :return:
    """
    pass


def review(file_base_name):
    """
    submit a review of the current scene.  (Requires a render to be present)
    :return:
    """
    from cgl.core.project import do_review
    sequence = scene_object().copy(context='render', filename='%s.####.jpg' % file_base_name)
    if glob.glob(playblast_seq.path_root.replace('####', '*')):
        print('exists - reviewing')
        do_review(progress_bar=None, path_object=sequence)


def launch_preflight(task=None, software=None):
    """
    Launches preflight window.
    :param task:
    :return:
    """
    from plugins.preflight.main import Preflight
    if not task:
        task = scene_object().task
    pf_mw = Preflight(parent=None, software=SOFTWARE, preflight=task, path_object=scene_object())
    pf_mw.exec_()


def publish():
    """

    :return:
    """
    publish_object = scene_object().publish()
    return publish_object


class CustomWindowOperator(QtWindowEventLoop):
    bl_idname = 'screen.lumbermill_window'
    bl_label = 'Lumbermill For Blender'

    def __init__(self):
        super().__init__(AppMainWindow)


def launch_():
    # https://github.com/vincentgires/blender-scripts/blob/master/scripts/addons/qtutils/example.py
    bpy.utils.register_class(CustomWindowOperator)
    bpy.ops.screen.lumbermill_window()


if __name__ == "__main__":
    print(SOFTWARE)
