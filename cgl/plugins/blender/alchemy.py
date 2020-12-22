import glob
import logging
import os
import bpy
from cgl.core.config import app_config, UserConfig
from cgl.core.path import PathObject as CorePathObject
from cgl.core.utils.general import create_file_dirs
from cgl.plugins.blender.main_window import CGLumberjack as MagicBrowser
from cgl.apps.lumbermill.main import CGLumberjackWidget

CONFIG = app_config()
PROJ_MANAGEMENT = CONFIG['account_info']['project_management']
PADDING = CONFIG['default']['padding']
PROCESSING_METHOD = UserConfig().d['methodology']
SOFTWARE = os.path.basename(os.path.dirname(__file__))


class MagicBrowser(MagicBrowser):
    def __init__(self, parent=None, path=None, user_info=None):
        CGLumberjack.__init__(self, parent, user_info=user_info, previous_path=path, sync_enabled=False)
        print('Application Path path is %s' % path)
        # self.setCentralWidget(BrowserWidget(self, show_import=True, path=path))

class BrowserWidget(CGLumberjackWidget):
    def __init__(self, parent=None,
                 project_management=None,
                 user_email=None,
                 company=None,
                 path=None,
                 radio_filter=None,
                 show_import=True,
                 show_reference=True):
        super(BrowserWidget, self).__init__(parent=parent,
                                            project_management=project_management,
                                            user_email=user_email,
                                            company=company,
                                            path=path,
                                            radio_filter=radio_filter,
                                            show_import=True,
                                            show_reference=True)


    def open_clicked(self):
        """
        Re-implementation of the open_clicked function in lumbermill.  This allows us to customize it to
        this app's specific needs
        :return:
        """
        from cgl.plugins.blender.lumbermill import open_file
        selection = self.path_widget.path_line_edit.text()
        if os.path.exists(selection):
            open_file(selection)
        else:
            logging.info('{0} does not exist!'.format(selection))

    def import_clicked(self):
        """
        Re-implemenation of the import_clicked function in lumbermill.  This allows us to customize it to
        this app's specific needs.  Typically the default will work if you've defined the import_file() function
        in this plugin.
        :return:
        """
        from cgl.plugins.blender.lumbermill import import_file, LumberObject
        selection = self.path_widget.path_line_edit.text()
        path_object = LumberObject(selection)
        if os.path.exists(selection):
            import_file(selection, namespace=path_object.asset)
        else:
            logging.info('{0} does not exist!'.format(selection))
        # close lumbermill.
        # self.parent().parent().accept()

    def reference_clicked(self):
        """
        Re-implemenation of the reference_clicked function in lumbermill.  This allows us to customize it to
        this app's specific needs.  Typically the default will work if you've defined the reference_file() function
        in this plugin.
        :return:
        """
        print('reference clicked! Referencing not yet implemented in Blender.')
        from cgl.plugins.blender.lumbermill import reference_file, LumberObject
        selection = self.path_widget.path_line_edit.text()
        path_object = LumberObject(selection)
        if os.path.exists(selection):
            reference_file(selection, namespace=path_object.asset)
        else:
            logging.info('{0} does not exist!'.format(selection))
        # selection = self.path_widget.path_line_edit.text()
        # if os.path.exists(selection)::
        #     reference_file(selection, namespace=None)
        # else:
        #     logging.info('{0} does not exist!'.format(selection))
        ## close lumbermill
        # self.parent().parent().accept()

class ConfirmDialog(bpy.types.Operator):
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

class InputDialog(bpy.types.Operator):
    bl_idname = "message.inputdialog"
    bl_label = "Enter input"
    bl_context = "scene"
    passes_re = False

    message = bpy.props.StringProperty(
        name="message",
        description="message",
        default=''
    )

    operator = bpy.props.StringProperty(
        name="TEST_OPERATOR",
        description="TEST_OPERATOR",
        default=''
    )

    example = bpy.props.StringProperty(
        name="example",
        description="example",
        default=''
    )

    selection = bpy.props.StringProperty(
        name="selection",
        description="selection",
        default=''
    )

    title = bpy.props.StringProperty(
        name="title",
        description="title",
        default='')

    bl_label = title[1]['default']

    buttons = bpy.props.StringProperty(name="buttons",
                                       description="buttons",
                                       default='ok')

    def execute(self, context):
        bpy.types.Scene.inputDialogText = self.selection
        bpy.types.Scene.inputDialogSelectionRegex = bpy.props.BoolProperty(default=self.passes_re)

        eval(self.operator)

        return {'PASS_THROUGH'}

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self, width=600)

    def draw(self, context):
        import re
        props = bpy.types.Scene.inputDialogText
        layout = self.layout

        col = layout.column(align=True)

        col.label(text=self.title)

        col.label(text=self.message)

        col = layout.column()
        col = col.row()

        rexpression = '^([a-z]{3,}, *)*[a-z]{3,}'

        col.label(text=self.example)

        if re.match(rexpression, self.selection):
            col.label(text='{} passes'.format(self.selection))
            self.passes_re = True



        else:
            col.label(text='{} does not pass '.format(self.selection))
            self.passes_re = False

        col2 = layout.column()

        row2 = col2.row()
        row2.prop(self, 'selection', text='')

        row3 = col2.row()

class PathObject(CorePathObject):

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
        self.path_relative = None
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
        self.name = None

        def process_string(self, path_object):
            path_object = path_object.replace('\\', '/')
            self.get_company(path_object)
            self.unpack_path(path_object)
            self.set_data_from_attrs()
            self.set_project_config()
            self.set_json()
            self.set_relative_path()

        def process_dict(self, path_object):
            self.set_attrs_from_dict(path_object)
            self.set_path()
            self.set_project_config()
            self.set_preview_path()
            self.set_json()
            self.set_relative_path()

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

    def set_relative_path(self):
        import os
        from cgl.plugins.blender.lumbermill import scene_object
        self.path_relative = os.path.relpath( self.path_root, scene_object().path_root)

    def set_render_paths(self):
        padding = '#' * self.frame_padding
        previewRenderTypes = ['anim', 'rig', 'mdl', 'lay', 'remsh', 'grmnt']

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

def import_file(filepath, namespace=None, collection_name=None):
    from cgl.plugins.blender import lumbermill as lm
    import bpy

    if filepath.endswith('fbx'):
        bpy.ops.import_scene.fbx(filepath=filepath)
    elif filepath.endswith('blend'):

        path_object = lm.PathObject(filepath)

        if collection_name == None:
            collection_name = path_object.asset

        with bpy.data.libraries.load(filepath, link=False) as (data_from, data_to):
            # data_to.collections = [c for c in data_from.collections if c == collection_name]

            for c in data_from.collections:
                if c == collection_name:
                    print(c)
                    data_to.collections = [c]

        imported_collection = bpy.data.collections[collection_name]
        bpy.context.scene.collection.children.link(imported_collection)
        imported_collection.name = path_object.task

        if namespace:
            imported_collection.name = '{}:{}'.format(namespace,path_object.task )
            for obj in imported_collection.objects:
                obj.name = '{}:{}'.format(namespace,obj.name)
                obj['source_path'] = path_object.path

                if obj.type =='MESH':
                    obj.data.name = '{}:{}'.format(namespace, obj.data.name)
                    material = obj.material_slots[0].material
                    if ':' not in material.name:
                        material.name = '{}:{}'.format(namespace,material.name)


def render(preview=False, audio=False):
    """
    renders the current scene.  Based on the task we can derive what kind of render and specific render settings.
    :param preview: determines if exr is used or not
    :param audio: if True renders an  mov and setups the audio settings
    :return:
    """
    previewRenderTypes = ['anim', 'rig', 'mdl', 'lay']
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



def reference_file(filepath, namespace=None, collection_name=None):
    from cgl.plugins.blender import lumbermill as lm

    import bpy

    path_object = lm.PathObject(filepath)

    if collection_name == None:
        collection_name = path_object.asset

    with bpy.data.libraries.load(filepath, link=True) as (data_from, data_to):
        for c in data_from.collections:
            if c == collection_name:
                print(c)
                data_to.collections = [c]
    if namespace:
        object_name = '{}:{}'.format(namespace, path_object.task)
    else:
        object_name = path_object.task
    obj = bpy.data.objects.new(object_name, None)
    obj.instance_type = 'COLLECTION'
    obj['source_path'] = path_object.path
    obj.instance_collection = bpy.data.collections[collection_name]
    bpy.context.collection.objects.link(obj)
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    return obj

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

def export_selected(to_path):
    """
    exports selected geometry to specified type.
    :param to_path: path to export to
    :param type: type of geo to export according to ext: obj, fbx, abc, usd, blnd
    :return:
    """
    if to_path.endswith('fbx'):
        bpy.ops.export_scene.fbx(filepath=to_path,
                                 use_selection=True,
                                 bake_anim=True,
                                 bake_anim_use_nla_strips=False,
                                 bake_anim_use_all_actions=False,
                                 )
    elif to_path.endswith('obj'):
        bpy.ops.export_scene.obj(filepath=to_path, use_selection=True)
    elif to_path.endswith('blend'):
        bpy.ops.export_scene.blend(filepath=to_path, use_selection=True)

def save_file_as(filepath):
    """
    save current file as
    :param filepath:
    :return:
    """
    bpy.ops.wm.save_as_mainfile(filepath=filepath)
    return filepath

def get_scene_name():
    """
    get current scene name
    :return:
    """
    return bpy.data.filepath

def set_relative_paths(set = True):
    if set:
        bpy.ops.file.make_paths_relative()
    else:
        bpy.ops.file.make_paths_absolute()

def scene_object():
    """
    returns PathObject of curent scene
    :return:
    """
    return PathObject(get_scene_name())

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

def review():
    """
    submit a review of the current scene.  (Requires a render to be present)
    :return:
    """
    from cgl.core.project import do_review
    padding = scene_object().frame_padding
    render_files = glob.glob(scene_object().render_path.replace('#' * padding, '*'))
    if render_files:
        path_object = PathObject(scene_object().render_path)
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
        print(11111111111111111)
        print(reference)
        return class_().import_latest(task=task, reference=reference, **kwargs)
    else:
        print(2)
        return class_().import_latest(**kwargs)

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
    task_class(path_object).build()

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

def publish():
    """

    :return:
    """
    publish_object = scene_object().publish()
    # TODO - i'd like to have a lumbermill controlled popup here.  The blender one doesn't work.
    return publish_object

def version_up(vtype='minor'):
    """
    versions up the current scene
    :param vtype: minor or major
    :return:
    """
    path_object = PathObject(get_scene_name())
    if vtype == 'minor':
        new_version = path_object.new_minor_version_object()
    elif vtype == 'major':
        new_version = path_object.next_major_version()
    create_file_dirs(new_version.path_root)
    create_file_dirs(new_version.copy(context = 'render').path_root)
    return save_file_as(new_version.path_root)

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

def unlink_asset(selection=None):
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

def get_object(name):
    obj = bpy.data.objects[name]
    return obj

def check_obj_exists(obj):

    if isinstance(obj, str):

        obj = bpy.data.objects[obj]

    if obj:
        return True

def launch():
    BlenderJack.show()

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
        # bpy.utils.unregister_class(BlenderConfirmDialog)
        bpy.utils.register_class(ConfirmDialog)
    except ValueError:
        print('class already registered')

    bpy.ops.message.messagebox('INVOKE_DEFAULT', message=message)

def input_dialog(parent=None, title='Attention:', message="message",
                buttons=None, line_edit=False, line_edit_text=False, combo_box_items=None,
                combo_box2_items=None, regex=None, name_example=None, button_a='ok', button_b='cancel', command=None):
    import bpy

    try:
        bpy.utils.register_class(InputDialog)
    except ValueError:
        print('class already registered')

    if buttons:
        button_a = buttons[0]
        button_b = buttons[1]
        buttons = buttons[0]
    else:
        buttons = ''

    bpy.types.Scene.inputDialogText = bpy.props.StringProperty(default='')
    bpy.types.Scene.inputDialogSelection = bpy.props.StringProperty(default='ok')
    bpy.types.Scene.inputDialogSelectionRegex = bpy.props.BoolProperty(default=False)
    value = bpy.ops.message.inputdialog('INVOKE_DEFAULT', message=message, example=name_example, title=title,
                                        operator=command)



if __name__ == "__main__":
    print(SOFTWARE)
