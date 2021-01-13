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

    def set_proxy_resolution(self):
        """
        sets nuke proxy resolution according to project globals
        :return:
        """

        if str(self.project).lower() in CONFIG['default']['proxy_resolution'].keys():
            proxy_resolution = CONFIG['default']['proxy_resolution'][self.project.lower()]
        else:
            proxy_resolution = CONFIG['default']['proxy_resolution']['default']
        self.proxy_resolution = proxy_resolution

    def set_frame_range(self):
        """
        sets frame range of the PATH_OBJECT based off the current nuke script's frame range
        :return:
        """
        sframe = nuke.knob("root.first_frame")
        eframe = nuke.knob("root.last_frame")
        self.frame_range = '%s-%s' % (sframe, eframe)

    def render(self, selected=True, processing_method=PROCESSING_METHOD):
        """
        :param selected: If True render selected, if False, give use a choice as to which one to render.
        :param processing_method: app, local, smedge, or deadline.  App - render in gui.  local - render through
        command line locally.  smedge/deadline - submit the job to a render manager for farm rendering.
        :return:
        """
        process_info_list = []
        process_info = {'command': 'cgl_nuke.NukePathObject().render()',
                        'command_name': 'Nuke GUI Render',
                        'start_time': time.time(),
                        'methodology': PROCESSING_METHOD,
                        'farm_processing_end': '',
                        'farm_processing_time': '',
                        'job_id': None}
        if selected:
            if not nuke.selectedNodes():
                print('render() set to selected, please select a write node and try again')
                return
            for s in nuke.selectedNodes():
                if s.Class() == 'Write':
                    node_name = s.name()
                    file_name = s['file'].value()
                    dir_ = os.path.dirname(file_name)
                    CreateProductionData(dir_, project_management='lumbermill')
                    sequence = Sequence(file_name)
                    if sequence.is_valid_sequence():
                        file_name = sequence.hash_sequence
                    if processing_method == 'local':
                        from cgl.plugins.nuke.gui import render_node
                        render_node(s)
                        process_info['file_out'] = file_name
                        process_info['artist_time'] = time.time() - process_info['start_time']
                        process_info['end_time'] = time.time()
                        write_to_cgl_data(process_info)
                        process_info_list.append(process_info)
                    else:
                        # add write node to the command
                        command = '%s -F %s -sro -x %s %s' % (CONFIG['paths']['nuke'], self.frame_range,
                                                              node_name, self.path_root)
                        command_name = '"%s: NukePathObject.render()"' % self.command_base
                        if processing_method == 'local':
                            process_info = cgl_execute(command, methodology=processing_method,
                                                       command_name=command_name,
                                                       new_window=True)
                        elif processing_method == 'smedge':
                            command = "-Type Nuke -Name %s -Range %s -Scene %s -WriteNode %s" % (command_name,
                                                                                                 self.frame_range,
                                                                                                 self.path_root,
                                                                                                 node_name)
                            process_info = cgl_execute(command, methodology=processing_method,
                                                       command_name=command_name)
                        process_info['file_out'] = file_name
                        process_info['artist_time'] = time.time() - process_info['start_time']
                        process_info['end_time'] = time.time()
                        try:
                            write_to_cgl_data(process_info)
                        except ValueError:
                            print('CGL_data file too big, skipping for now')
                        process_info_list.append(process_info)
            return process_info_list
        else:
            print('this is what happens when selected is set to False')


def scene_object():
    """
    returns PathObject of curent scene
    :return:
    """
    return PathObject(nuke.root().name())


'___________________SCENE_________________'


def open_file(filepath):
    return nuke.scriptOpen(filepath)


def save_file(filepath=None):
    if not filepath:
        filepath = get_file_name()
    return nuke.scriptSave(filepath)


def save_file_as(filepath):
    return nuke.scriptSaveAs(filepath)


def version_up(write_nodes=True):
    from cgl.ui.widgets.dialog import InputDialog
    path_object = PathObject(nuke.Root().name())
    next_minor = path_object.new_minor_version_object()
    message = ('Versioning Up From v%s ->  v%s' % (path_object.version, next_minor.version))
    dialog = InputDialog(title='Version Up', message=message)
    dialog.exec_()
    if dialog.button == 'Ok':
        CreateProductionData(next_minor, project_management='lumbermill')
        nuke.scriptSaveAs(next_minor.path_root)
        if write_nodes:
            match_scene_version()


def get_scene_name():
    return nuke.Root().name()


def create_scene_write_node():
    """
    This function specifically assumes the current file is in the pipeline and that you want to make a write node for
    that.  We can get more complicated and tasks from here for sure.
    :return:
    """
    padding = '#' * get_biggest_read_padding()
    path_object = PathObject(get_file_name())
    path_object.set_attr(context='render')
    path_object.set_attr(ext='%s.exr' % padding)
    write_node = nuke.createNode('Write')
    write_node.knob('file').fromUserText(path_object.path_root)
    return write_node


def get_main_window():
    return QtWidgets.QApplication.activeWindow()


''''___________________IMPORT______________________'''


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


def import_script(filepath):
    return nuke.nodePaste(filepath)


def import_geo(filepath):
    n = nuke.createNode("ReadGeo")  # should maybe be readGeo2
    n.knob('file').setText(filepath)


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


''''____________________UI_______________'''


def confirm_prompt(title='title', message='message', button=None):
    p = nuke.Panel(title)
    p.addNotepad('', message)
    if button:
        for b in button:
            p.addButton(b)
    else:
        p.addButton('OK')
        p.addButton('Cancel')
    return p.show()


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
