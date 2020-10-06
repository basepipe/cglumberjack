import os
import glob
import logging
from cgl.core.utils.general import current_user
from cgl.core.utils.general import create_file_dirs
from cgl.core.path import PathObject
from cgl.core.config import app_config, UserConfig
from cgl.apps.lumbermill.main import CGLumberjackWidget
from cgl.plugins.blender.main_window import CGLumberjack
import bpy



CONFIG = app_config()
PROJ_MANAGEMENT = CONFIG['account_info']['project_management']
PADDING = CONFIG['default']['padding']
PROCESSING_METHOD = UserConfig().d['methodology']
SOFTWARE = os.path.basename(os.path.dirname(__file__))


class BlenderJack(CGLumberjack):
    def __init__(self, parent=None, path=None, user_info=None):
        CGLumberjack.__init__(self, parent, user_info=user_info, previous_path=path, sync_enabled=False)
        print('Application Path path is %s' % path)
        # self.setCentralWidget(BrowserWidget(self, show_import=True, path=path))


class BlenderConfirmDialog(bpy.types.Operator):
    bl_idname = "message.messagebox"
    bl_label = ""
    message = bpy.props.StringProperty(
        name="message",
        description="message",
        default=''
    )

    def execute(self, context):
        self.report({'INFO'}, self.message)
        print(self.message)
        return {'FINISHED'}

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self, width=400)

    def draw(self, context):
        self.layout.label(text=self.message)


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
        self.playblast_path = None
        self.render_path = None
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
            pass
        if isinstance(path_object, dict):
            self.process_dict(path_object)
        elif isinstance(path_object, str):
            self.process_string(path_object)
        elif isinstance(path_object, PathObject):
            self.process_dict(path_object.data)
        else:
            logging.error('type: %s not expected' % type(path_object))
        self.set_render_paths()

    def set_render_paths(self):
        padding = '#' * self.frame_padding
        previewRenderTypes = ['anim', 'rig', 'mdl', 'lay','remsh','grmnt']

        if self.task in previewRenderTypes:
            render_path = self.copy(context='render', ext='jpg', set_proper_filename=True).path_root
            self.render_path = render_path.replace('.jpg', '.{}.jpg'.format(padding))
        else:
            render_path = self.copy(context='render', ext='exr', set_proper_filename=True).path_root
            self.render_path = render_path.replace('.exr', '.{}.exr'.format(padding))

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


def import_file(filepath='', namespace=None, collection_name=None, append=True, linked=True, type='COLLECTION',snap_to_cursor= False):
    """
    imports file into a scene.
    :param snap_to_cursor: if true imports the object where the cursor is palced
    :param type: 'COLLECTION' , 'GROUP', 'ANIM' , 'CAMERA'
    :param linked: when collection type instanced , links collection to scene
    :param append: Imports file to scene
    :param collection_name:
    :param filepath:
    :param namespace:
    :return:
    """

    if filepath.endswith('fbx'):
        bpy.ops.import_scene.fbx(filepath=filepath)
    elif filepath.endswith('obj'):
        bpy.ops.import_scene.obj(filepath=filepath)
    elif filepath.endswith('blend'):

        if collection_name is None:
            collection = PathObject(filepath)
            collection_name = collection.asset

        if type == 'COLLECTION':
            print('collection selected')
            with bpy.data.libraries.load(filepath, link=append) as (data_from, data_to):
                data_to.collections = [c for c in data_from.collections if c.startswith(collection_name)]
                # for obj in data_to.groups[0].objects:
                #     bpy.context.scene.objects.link(obj)

        if type == 'GROUP':
            print('group Selected')
            with bpy.data.libraries.load(filepath, link=linked) as (data_from, data_to):
                data_to.node_groups = data_from.node_groups

        if type == 'ANIM':
            print('anim Import selected')
            with bpy.data.libraries.load(filepath, link=linked) as (data_from, data_to):
                data_to.actions = data_from.actions

        if type == 'CAMERA':

            with bpy.data.libraries.load(filepath, link=linked) as (data_from, data_to):
                # data_to.cameras = [c for c in data_from.cameras if c.startswith(collection_name)]
                data_to.objects = [c for c in data_from.objects if c.startswith(collection_name)]
            print('{} Cam imported '.format(collection_name))

        if type == 'MATERIAL':

            with bpy.data.libraries.load(filepath, link=linked) as (data_from, data_to):
                # data_to.cameras = [c for c in data_from.cameras if c.startswith(collection_name)]
                data_to.materials = [c for c in data_from.materials if c.startswith(collection_name)]
            print('{} material imported '.format(collection_name))

        if linked:
            obj = bpy.data.objects.new(collection_name, None)
            obj.instance_type = 'COLLECTION'
            obj.instance_collection = bpy.data.collections[collection_name]
            bpy.context.collection.objects.link(obj)
            bpy.ops.object.select_all(action='DESELECT')
            obj.select_set(True)

            if snap_to_cursor:
                obj.location = bpy.context.scene.cursor.location



def open_file(filepath):
    """
    Open File: filepath
    :param filepath:
    :return:
    """
    bpy.ops.wm.open_mainfile(filepath=filepath)
    return filepath


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
    :param namespace:
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
    import bpy
    try:
        #bpy.utils.unregister_class(BlenderConfirmDialog)
        bpy.utils.register_class(BlenderConfirmDialog)
    except ValueError:
        print('class already registered')


    bpy.ops.message.messagebox('INVOKE_DEFAULT',message=message)



def select(selection, d=True):
    """
    allows us to select something in the scene.
    :param selection: node to select (or string)
    :param d: if true - deselect everything
    :return:
    """
    if isinstance(nodes, list):
        print('{0} is a list'.format(selection))
    elif isinstance(nodes, string):
        bpy.data.objects[object_name].select_set(True)


def export_selected(to_path):
    """
    exports selected geometry to specified type.
    :param to_path: path to export to
    :param type: type of geo to export according to ext: obj, fbx, abc, usd, blnd
    :return:
    """
    if to_path.endswith('fbx'):
        bpy.ops.export_scene.fbx(filepath=to_path, use_selection=True)
    elif to_path.endswith('obj'):
        bpy.ops.export_scene.obj(filepath=to_path, use_selection=True)
    elif to_path.endswith('blend'):
        bpy.ops.export_scene.blend(filepath=to_path, use_selection=True)


def create_turntable(length=250, task=False, startFrame=1):
    """
    Creates a Turntable of length around the selected object, or around a "task" object.
    This is specific to 3d applications.
    :param startFrame:
    :param length:
    :param task:
    :return:
    """

    selectedObject = bpy.context.object
    objectDimensions = selectedObject.dimensions
    distanceFromObject = objectDimensions[0] * -4
    height = objectDimensions[2] / 2
    endFrame = startFrame - 1 + length

    # Creates locator top parent camera to
    locator = bpy.data.objects.new('TurnTableLocator', None)
    locator.empty_display_size = 2
    locator.empty_display_type = 'PLAIN_AXES'
    bpy.context.scene.collection.objects.link(locator)

    # Create camera
    turnTableCamObj = bpy.data.cameras.new('turnTable')
    turnTable = bpy.data.objects.new("TurnTableCam", turnTableCamObj)
    bpy.context.scene.collection.objects.link(turnTable)
    turnTable.parent = locator

    turnTable.location = (0, distanceFromObject, height)
    turnTable.rotation_euler = (1.5707963705062866, 0.0, 0.0)

    # Animates TurnTable
    locator.keyframe_insert("rotation_euler", frame=startFrame)
    locator.rotation_euler = (0, 0, 6.2831854820251465)
    locator.keyframe_insert("rotation_euler", frame=endFrame)

    locator.animation_data.action.fcurves[2].keyframe_points[0].interpolation = 'LINEAR'
    bpy.context.scene.frame_start = startFrame
    bpy.context.scene.frame_end = endFrame
    pass



def set_framerange(start=1, end=1, current=False):
    bpy.context.scene.frame_start = start
    bpy.context.scene.frame_end = end

    current = bpy.context.scene.frame_current
    if current:
        bpy.context.scene.frame_start = current
        bpy.context.scene.frame_end = current

def switch_overlays(visible=False):
    for window in bpy.context.window_manager.windows:
        screen = window.screen

        for area in screen.areas:
            if area.type == 'VIEW_3D':
                for space in area.spaces:
                    if space.type == 'VIEW_3D':
                        space.overlay.show_overlays = visible


def clean_turntable():
    """
    cleans up the turntable
    :return:
    """
    objs = bpy.data.objects
    remove = ['TurnTableLocator', 'TurnTableCam']

    for removeName in remove:
        for obj in objs:
            if removeName in obj.name:
                objs.remove(objs[obj.name], do_unlink=True)
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


def render(preview=False, audio=False):
    """
    renders the current scene.  Based on the task we can derive what kind of render and specific render settings.
    :param preview: determines if exr is used or not
    :param audio: if True renders an  mov and setups the audio settings
    :return:
    """
    previewRenderTypes = ['anim', 'rig', 'mdl','lay']
    file_out = scene_object().render_path.split('#')[0]

    if preview:
        bpy.context.scene.render.image_settings.file_format = 'JPEG'
        bpy.context.scene.render.filepath = file_out

        if audio:
            bpy.context.scene.render.image_settings.file_format = 'FFMPEG'
            bpy.context.scene.render.ffmpeg.format = 'QUICKTIME'
            bpy.context.scene.render.ffmpeg.audio_codec = 'MP3'

        bpy.ops.render.opengl('INVOKE_DEFAULT', animation=True, view_context=True)

    else:
        bpy.context.scene.render.image_settings.file_format = 'OPEN_EXR_MULTILAYER'
        bpy.context.scene.render.filepath = file_out
        bpy.ops.render.render(animation=True, use_viewport=True)


def review():
    """
    submit a review of the current scene.  (Requires a render to be present)
    :return:
    """
    from cgl.core.project import do_review
    padding = scene_object().frame_padding
    render_files = glob.glob(scene_object().render_path.replace('#' * padding, '*'))
    if render_files:
        path_object = LumberObject(scene_object().render_path)
        do_review(progress_bar=None, path_object=path_object)


def launch_preflight(task=None, software=None):
    """
    Launches preflight window.
    :param task:
    :return:
    """
    from .gui import PreflightOperator
    try:
        bpy.utils.unregister_class(PreflightOperator)
    except RuntimeError:
        print('no class registered')
    bpy.utils.register_class(PreflightOperator)
    bpy.ops.screen.preflight()


def publish():
    """

    :return:
    """
    publish_object = scene_object().publish()
    # TODO - i'd like to have a lumbermill controlled popup here.  The blender one doesn't work.
    return publish_object


def launch_():
    BlenderJack.show()


def unlink_asset(selection = None):
    if selection == None:
        selection = bpy.context.selected_objects

    for object in selection:
        if object.instance_collection:
            libname = bpy.context.object.instance_collection.library
        else:
            try:
                libname = object.data.library
            except AttributeError:
                print('object doesnt have library asset')


        if 'proxy' in bpy.context.object.name:
            name = bpy.context.object.name.split('_')[0]
        else:
            name = bpy.context.object.name


        obj = bpy.data.objects[name]
        bpy.data.batch_remove(ids=(libname, obj))



if __name__ == "__main__":
    print(SOFTWARE)
