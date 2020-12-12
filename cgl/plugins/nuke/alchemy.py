import os
import logging
from cgl.plugins.Qt import QtWidgets
import time
import nuke
from cgl.core.utils.general import cgl_execute, write_to_cgl_data
from cgl.core.path import PathObject, Sequence, CreateProductionData, lj_list_dir
from cgl.core.config import app_config, UserConfig

CONFIG = app_config()
PROJ_MANAGEMENT = CONFIG['account_info']['project_management']
PADDING = CONFIG['default']['padding']
PROCESSING_METHOD = UserConfig().d['methodology']
X_SPACE = 120
Y_SPACE = 120


class NukePathObject(PathObject):

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


        if isinstance(path_object, bytes):
            path_object = str(path_object)
        if isinstance(path_object, dict):
            self.process_info(path_object)
        elif isinstance(path_object, str):
            self.process_string(path_object)
        elif isinstance(path_object, PathObject):
            self.process_info(path_object.data)
        else:
            logging.error('type: %s not expected' % type(path_object))
        self.set_frame_range()
        self.set_proxy_resolution()




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


def scene_object():
    """
    returns PathObject of curent scene
    :return:
    """
    return PathObject(nuke.root().name())


def set_comp_default_settings():

    proxy_res = get_proxy_resolution()
    readNode = nuke.toNode('plate_Read')

    if not readNode:
        if nuke.selectedNode():
            readNode = nuke.selectedNode()


    if readNode:

        selectedFormat = readNode['format'].value()
        firstFrame = int(readNode.knob('first').getValue())
        lastFrame = int(readNode.knob('last').getValue())

        proxy_width = proxy_res.split('x')[0]
        proxy_height = proxy_res.split('x')[1]

        # Setup proxy settings
        lc_format = []

        print(lc_format)

        for f in nuke.formats():

            if f.name() == 'DEFAULT_PROXY':
                f.setName('DEFAULT_PROXY_OLD')
                f.setWidth(int(proxy_width))
                f.setHeight(int(proxy_width))
            lc_format.append(f)

        DEFAULT_PROXY = '%s DEFAULT_PROXY' % proxy_res.replace('x', ' ')
        nuke.addFormat(DEFAULT_PROXY)

        nuke.root()['proxy_type'].setValue('format')
        nuke.root()['proxy_format'].setValue('DEFAULT_PROXY')
        nuke.root()['proxySetting'].setValue('if nearest')
        readNode['proxy_format'].setValue('DEFAULT_PROXY')
        nuke.root()['proxySetting'].setValue('if nearest')
        nuke.root()['format'].setValue(selectedFormat)
        nuke.frame(firstFrame)

        nuke.alert("Comp Size, duration and proxy set")


def import_media(filepath, name=None):
    """
    imports the filepath.  This assumes that sequences are formated as follows:
    [sequence] [sframe]-[eframe]
    sequence.####.dpx 1-234
    regular files are simply listed as a string with no frame numbers requred:
    bob.jpg
    this will also look for an HD proxy file, first jpgs and then exrs.
    :param filepath:
    :return:
    """
    read_node = nuke.createNode('Read')
    if name:
        read_node.knob('name').setValue(name)
    read_node.knob('file').fromUserText(filepath)
    path_object = NukePathObject(filepath)
    proxy_object = PathObject(filepath).copy(resolution=path_object.proxy_resolution, ext='exr')
    dir_ = os.path.dirname(proxy_object.path_root)
    if os.path.exists(dir_):
        read_node.knob('proxy').fromUserText(proxy_object.path_root)
    return read_node



def import_directory(filepath):
    path_object = NukePathObject(filepath)
    if path_object.task == 'lite':
        import_lighting_renders(filepath)
    else:
        for root, dirs, files in os.walk(filepath):
            for name in dirs:
                for sequence in lj_list_dir(os.path.join(root, name)):
                    node_path = os.path.join(root, name, sequence)
                    if not os.path.isdir(node_path):
                        temp_object = NukePathObject(node_path)
                        if temp_object.aov:
                            name = temp_object.aov
                        elif temp_object.shotname:
                            name = temp_object.shotname
                        else:
                            name = None
                        import_media(node_path, temp_object.aov)



def get_proxy_resolution():
    CONFIG = app_config()
    current_shot = scene_object()
    project = str(current_shot.project).lower()
    print(project.lower())
    if project.lower() in CONFIG['default']['proxy_resolution'].keys():
        if CONFIG['default']['proxy_resolution'][project]:

            proxy_resolution = CONFIG['default']['proxy_resolution'][project]
        else:
            proxy_resolution = CONFIG['default']['proxy_resolution']['default']
            print('No proxy resolution Found, using default')
    else:
        proxy_resolution = CONFIG['default']['proxy_resolution']['default']
        print('No proxy resolution Found, using default')
        print(project)

    return proxy_resolution
