import os
import logging
from cgl.plugins.Qt import QtGui, QtWidgets
import time
import nuke
from cgl.core.util import cgl_execute, write_to_cgl_data
from cgl.core.path import PathObject, Sequence, CreateProductionData
from cgl.core.config import app_config, UserConfig

CONFIG = app_config()
PROJ_MANAGEMENT = CONFIG['account_info']['project_management']
PADDING = CONFIG['default']['padding']
PROCESSING_METHOD = UserConfig().d['methodology']


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
        self.task = None
        self.cam = None
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
        self.set_frame_range()
        self.set_proxy_resolution()

    def set_proxy_resolution(self):
        """
        sets nuke proxy resolution according to project globals
        :return:
        """
        if self.project.lower() in CONFIG['default']['proxy_resolution'].keys():
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
                print 'render() set to selected, please select a write node and try again'
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
                    if processing_method == 'gui':
                        from gui import render_node
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
                        write_to_cgl_data(process_info)
                        process_info_list.append(process_info)
            return process_info_list
        else:
            print 'this is what happens when selected is set to False'


def get_main_window():
    return QtWidgets.QApplication.activeWindow()


def get_scene_name():
    return nuke.Root().name()


def normpath(filepath):
    return filepath.replace('\\', '/')


def get_file_name():
    return unicode(nuke.Root().name())


def open_file(filepath):
    return nuke.scriptOpen(filepath)


def save_file(filepath=None):
    if not filepath:
        filepath = get_file_name()
    return nuke.scriptSave(filepath)


def save_file_as(filepath):
    return nuke.scriptSaveAs(filepath)


def import_media(filepath):
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
    readNode = nuke.createNode('Read')
    readNode.knob('file').fromUserText(filepath)
    path_object = NukePathObject(filepath)
    proxy_object = PathObject(filepath).copy(resolution=path_object.proxy_resolution, ext='exr')
    dir_ = os.path.dirname(proxy_object.path_root)
    if os.path.exists(dir_):
        readNode.knob('proxy').fromUserText(proxy_object.path_root)


def create_scene_write_node():
    """
    This function specifically assumes the current file is in the pipeline and that you want to make a write node for
    that.  We can get more complicated and build from here for sure.
    :return:
    """
    padding = '#'*get_biggest_read_padding()
    path_object = PathObject(get_file_name())
    path_object.set_attr(context='render')
    path_object.set_attr(ext='%s.exr' % padding)
    write_node = nuke.createNode('Write')
    write_node.knob('file').fromUserText(path_object.path_root)
    return write_node


def get_biggest_read_padding():
    biggest_padding = 0
    for n in nuke.allNodes('Read'):
        temp = os.path.splitext(n['file'].value())[0]
        if '%' in temp:
            padding = int(temp.split('%')[1].replace('d', ''))
        else:
            padding = 0
        if padding > biggest_padding:
            biggest_padding = padding
    return biggest_padding


def check_write_padding():
    """
    Checks all read nodes in the scene to find the largest num padding.  then checks all write nodes to ensure they
    comply.
    :return:
    """
    edited_nodes = []
    scene_padding = get_biggest_read_padding()
    for n in nuke.allNodes('Write'):
        temp, ext = os.path.splitext(n['file'].value())
        base_file = temp.split('%')[0]
        padding = int(temp.split('%')[1].replace('d', ''))
        if padding < scene_padding:
            if scene_padding < 10:
                numformat = '%0'+str(scene_padding)+'d'
            elif scene_padding < 100 and scene_padding > 9:
                numformat = '%'+str(scene_padding)+'d'
            new_file_name = '%s%s%s' % (base_file, numformat, ext)
            edited_nodes.append(new_file_name)
            n.knob('file').fromUserText(new_file_name)
    return edited_nodes


def import_script(filepath):
    return nuke.nodePaste(filepath)


def import_read_geo(filepath):
    n = nuke.createNode("ReadGeo2")
    n.knob('file').setText(filepath)


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


def deselected():
    nuke.selectAll()
    nuke.invertSelection()


def check_write_node_version(selected=True):
    scene_object = NukePathObject()
    if selected:
        for s in nuke.selectedNodes():
            if s.Class() == 'Write':
                if 'elem' not in s.name():
                    path = s['file'].value()
                    path_object = NukePathObject(path)
                    if scene_object.version != path_object.version:
                        print 'scene %s, render %s, versions do not match' % (scene_object.version, path_object.version)
                        return False
                    else:
                        return True


def write_node_selected():
    """
    if write node is selected returns it.
    :return:
    """
    write_nodes = []
    for s in nuke.selectedNodes():
        if s.Class() == 'Write':
            write_nodes.append(s)
        else:
            return False
    return write_nodes


def match_scene_version():
    """
    ajdusts version number on the main write node, or all write nodes to version
    :param main: if true this only effects the version number of the main write node
    :param version: the version to set write node(s) at.
    :return:
    """

    padding = '#'*get_biggest_read_padding()
    path_object = PathObject(get_file_name())
    for n in nuke.allNodes('Write'):
        write_output = PathObject(n['file'].value())
        if write_output.version == path_object.version:
            print('Write Node version %s matches scene version' % write_output.version)
        else:
            print n.name()
            if not 'elem' in n.name():
                print('Changing Write Version %s to %s') % (write_output.version, path_object.version)
                write_output.set_attr(version=path_object.version)
                n.knob('file').fromUserText(write_output.path_root)
    nuke.scriptSave()

"""
def version_up(write_nodes=True):
    path_object = PathObject(nuke.Root().name())
    next_minor = path_object.new_minor_version_object()
    print('Versioning Up %s: %s' % (next_minor.version, next_minor.path_root))
    CreateProductionData(next_minor, project_management='lumbermill')
    nuke.scriptSaveAs(next_minor.path_root)
    if write_nodes:
        match_scene_version()
"""


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


def version_up_selected_write_node():
    """
    Versions Up the Output path in the selected Write Node
    :return:
    """
    if nuke.selectedNodes():
        s = nuke.selectedNodes()[0]
        if s.Class() == 'Write':
            path = s['file'].value()
            path_object = NukePathObject(path)
            next_minor = path_object.new_minor_version_object()
            print 'Setting File to %s' % next_minor.path_root
            s.knob('file').fromUserText(next_minor.path_root)


def get_write_paths_as_path_objects():
    """
    returns a list of pathObject items for the selected write nodes.
    :return:
    """
    write_objects = []
    if nuke.selectedNodes():
        for s in nuke.selectedNodes():
            if s.Class() == 'Write':
                if 'elem' not in s.name():
                    path = s['file'].value()
                    path_object = NukePathObject(path)
                    write_objects.append(path_object)
    return write_objects
