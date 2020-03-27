import os
import logging
from cgl.plugins.Qt import QtGui, QtWidgets
import time
import nuke, nukescripts
from cgl.core.util import cgl_execute, write_to_cgl_data
from cgl.core.path import PathObject, Sequence, CreateProductionData, lj_list_dir
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
                        try:
                            write_to_cgl_data(process_info)
                        except ValueError:
                            print('CGL_data file too big, skipping for now')
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


def import_lighting_renders(filepath):
    # change backdrop name to include render pass
    # fix the problem with my merge nodes.
    #
    utilities = ['N', 'P', 'Z', 'cputime']
    shaders = ['diffuse_direct', 'diffuse_indirect', 'specular_direct', 'specular_indirect', 'sss', 'transmission']
    z_depth = 'Z'
    lights_contain = 'RGBA'
    beauty = 'beauty'
    light_nodes = []
    utility_nodes = []
    shader_nodes = []
    z_node = None
    render_pass = PathObject(filepath).render_pass
    for root, dirs, files in os.walk(filepath):
        for name in dirs:
            stuff = lj_list_dir(os.path.join(root, name))
            if stuff:
                for sequence in stuff:
                    node_path = os.path.join(root, name, sequence)
                    if not os.path.isdir(node_path):
                        temp_object = NukePathObject(node_path)
                        if temp_object.filename:
                            node_name = '%s %s' % (temp_object.render_pass[0:3], temp_object.aov)
                            node = import_media(node_path, node_name)
                            if lights_contain in temp_object.aov:
                                light_nodes.append(node)
                            if temp_object.aov == z_depth:
                                z_node = node
                            if temp_object.aov in utilities:
                                utility_nodes.append(node)
                            if temp_object.aov == beauty:
                                print 'creating beauty node'
                            if temp_object.aov in shaders:
                                shader_nodes.append(node)
            else:
                pass
    if z_node:
        print 1
        z_nodes = setup_z_node(z_node)
        for each in z_nodes:
            utility_nodes.append(each)
    all_nodes = light_nodes+utility_nodes+shader_nodes
    select(all_nodes)
    auto_place()
    select(d=True)
    #light_merge = create_merge(nodes=light_nodes, operation='plus')
    #light_nodes.append(light_merge)
    select(light_nodes)

    auto_place(light_nodes)
    y_offset = biggest_y()
    x_offset = biggest_x()
    print x_offset
    print y_offset
    # move_nodes(plus_x=0, plus_y=100, start_x=x_offset, start_y=y_offset, nodes=light_nodes)
    backdrop(name='%s Lights' % render_pass[0:3], nodes=light_nodes, move=(0, -300))
    select(d=True)
    select(utility_nodes)
    auto_place(utility_nodes)
    x_offset = biggest_x(light_nodes)
    backdrop(name='%s Utilities' % render_pass[0:3], nodes=utility_nodes, move_offset=(x_offset, 0))
    select(d=True)
    """
    #shader_merge = create_merge(nodes=shader_nodes, operation='plus')
    #shader_nodes.append(shader_merge)
    select(shader_nodes)
    auto_place(shader_nodes)
    backdrop(name='%s Shading' % render_pass[0:3], move=(300, 0))
    select(d=True)
    """


def auto_place(nodes=False):
    if not nodes:
        nodes = nuke.selectedNodes()
    for n in nodes:
        nuke.autoplace(n)


def move_nodes(plus_x=0, plus_y=0, start_x=0, start_y=0, nodes=None, padding=True):
    if start_x:
        x_multiplier = 120
        if padding:
            x_padding = x_multiplier*3
    else:
        x_multiplier = 0
        x_padding = 0
    if start_y:
        y_multiplier = 120
        if padding:
            y_padding = 120
    else:
        y_multiplier = 0
        y_padding = 0

    print 'made it'
    if not nodes:
        nodes = nuke.selectedNodes()
    for i, n in enumerate(nodes):
        print n['name'].value, i
        if not start_x:
            start_x = n['xpos'].value()
            print start_x
        if not start_y:
            start_y = n['ypos'].value()
        n.setXpos(int(start_x + (x_multiplier*i+1) + x_padding + plus_x))
        n.setYpos(int(start_y + (y_multiplier*i+1) + y_padding + plus_y))


def biggest_x(nodes=None):
    if not nodes:
        nodes = nuke.allNodes()
    x_val = 0
    for n in nodes:
        if x_val == 0:
            x_val = n['xpos'].value()
        elif x_val < n['xpos'].value():
            x_val = n['xpos'].value()
    return x_val


def biggest_y(nodes=None):
    if not nodes:
        nodes = nuke.allNodes()
    y_val = 0
    for n in nodes:
        if y_val == 0:
            y_val = n['ypos'].value()
        elif y_val < n['ypos'].value():
            y_val = n['ypos'].value()
    return y_val


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


def find_node(name):
    nodes = nuke.allNodes()
    for n in nodes:
        if name in n['name'].value():
            print 'found name'
            return n
    return None


def setup_z_node(z_node):
    """
    This assumes we're using arnold AOVs when setting up this z network
    :param node:
    :return:
    """
    nodes = []
    z_object = PathObject(z_node['file'].value())
    beauty = find_node('beauty')
    min, max = get_min_max(z_node)
    mult_node = nuke.createNode('Multiply')
    mult_node['value'].setValue(1 / max)
    mult_node['name'].setValue('%s Z Preview' % z_object.render_pass[0:3])
    nodes.append(mult_node)

    select([z_node])
    sc = nuke.createNode('ShuffleCopy')
    sc['in2'].setValue('depth')
    sc['out'].setValue('depth')
    sc['red'].setValue('red')
    if beauty:
        sc.setInput(0, beauty)
    sc.setInput(1, z_node)
    nodes.append(sc)

    z_defocus = nuke.createNode('ZDefocus2')
    z_defocus['z_channel'].setValue('depth.Z')
    z_defocus['math'].setValue('depth')
    z_defocus['output'].setValue('focal_plane_setup')
    z_defocus['size'].setValue(20)
    z_defocus['max_size'].setExpression('size')
    nodes.append(z_defocus)
    select()
    mult_node.setInput(0, z_node)

    return nodes



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


def import_geo(filepath):
    n = nuke.createNode("ReadGeo") # should maybe be readGeo2
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


def select(nodes=None, d=True):
    if d:
        nuke.selectAll()
        nuke.invertSelection()
    if nodes:
        nuke.selectAll()
        nuke.invertSelection()
        [x['selected'].setValue(True) for x in nodes]


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


def auto_backdrop(label=None):
    n = nukescripts.autoBackdrop()
    if label:
        n['label'].setValue(label)
    # change the padding on the backdrop node


def backdrop(name, bg_color=(.267, .267, .267), text_color=(.498, .498, .498), nodes=None, move=(0, 0),
             move_offset=(0, 0)):

    z_index = get_highest_z_index()+1
    bg_r, bg_g, bg_b = bg_color
    t_r, t_g, t_b = text_color

    # Define Colors. The numbers have to be integers, so there's some math to convert them.
    bg_color_int = int('%02x%02x%02x%02x' % (bg_r * 255, bg_g * 255, bg_b * 255, 255), 16)
    text_color_int = int('%02x%02x%02x%02x' % (t_r * 255, t_g * 255, t_b * 255, 255), 16)

    if nodes is None:
        nodes = nuke.selectedNodes()
        # move_nodes(plus_x=move[0], plus_y=move[1], start_x=move_offset[0], start_y=move_offset[1])
    if len(nodes) == 0:
        n = nuke.createNode("BackdropNode")
        return n


    # Calculate bounds for the backdrop node.
    bd_x = min([node.xpos() for node in nodes])
    bd_y = min([node.ypos() for node in nodes])
    bd_w = max([node.xpos() + node.screenWidth() for node in nodes]) - bd_x
    bd_h = max([node.ypos() + node.screenHeight() for node in nodes]) - bd_y

    # Expand the bounds to leave a little border.
    # Elements are offsets for left, top, right and bottom edges respectively
    left, top, right, bottom = (-70, -140, 70, 70)
    bd_x += left
    bd_y += top
    bd_w += (right - left)
    bd_h += (bottom - top)

    # Set backdrop parameters
    n = nuke.nodes.BackdropNode(xpos=bd_x,
                                bdwidth=bd_w,
                                ypos=bd_y,
                                bdheight=bd_h,
                                z_order=int(z_index),
                                tile_color=bg_color_int,
                                note_font_color=text_color_int,
                                note_font_size=100,
                                label=name,
                                name=name,
                                note_font='Courrier New')

    # Revert to previous selection
    for node in nodes:
        node['selected'].setValue(True)

    # Ensure backdrop is selected, to make moving easier
    n['selected'].setValue(True)
    move_nodes(plus_x=move[0], plus_y=move[1], start_x=move_offset[0], start_y=move_offset[1])
    nuke.show(n)

    return n


def get_highest_z_index():
    z_index = -10
    bd_nodes = nuke.allNodes('BackdropNode')
    for node in bd_nodes:
        print node['label'].value()
        if node['z_order'].value() > z_index:
            z_index = node['z_order'].value()
    return int(z_index)


def create_merge(nodes=None, operation='over'):
    a = nuke.createNode('Merge2')
    if not nodes:
        nodes = nuke.selectedNodes()
    if nodes:
        x = 0
        for n in nodes:
            a.setInput(x, n)
            x += 1
        a['operation'].setValue(operation)
    nuke.autoplace(a)
    return a


def get_min_max(node=None):
    if not node:
        node = nuke.selectedNodes()[0]
    min_color = nuke.nodes.MinColor(target=0, inputs=[node])
    inv = nuke.nodes.Invert(inputs=[node])
    max_color = nuke.nodes.MinColor(target=0, inputs=[inv])

    cur_frame = nuke.frame()
    nuke.execute(min_color, cur_frame, cur_frame)
    min_ = -min_color['pixeldelta'].value()

    nuke.execute(max_color, cur_frame, cur_frame)
    max_ = max_color['pixeldelta'].value() + 1

    for n in (min_color, max_color, inv):
        nuke.delete(n)
    return min_, max_

