import cgl.plugins.nuke.alchemy as alc
import nuke
from cgl.core.path import PathObject
from cgl.plugins.nuke.tasks.smart_task import SmartTask

class Task(SmartTask):

    def __init__(self, path_object=None):
        if not path_object:
            from cgl.plugins.nuke.alchemy import scene_object
            self.path_object = scene_object()

    def build(self):
        """
        would do the equivalent of a lighting build in Nuke's 3d tools.
        """
        pass

    def _import(self, filepath):
        # determine if this is a sequence or a folder.
        print(filepath)

    def import_latest(self):
        pass


def get_latest_folder():
    # gets the latest published render folder as a root for all the lighting renders.
    path_object = lm.scene_object().copy(task='lite', context='render', user='publish', latest=True,
                                          set_proper_filename=True, ext='msd')



def import_lighting_renders(render_folder):
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
    beauty_nodes = []
    z_node = None
    render_pass = PathObject(render_folder).render_pass
    for root, dirs, files in os.walk(render_folder):
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
                                beauty_nodes.append(node)
                                print('creating beauty node')
                            if temp_object.aov in shaders:
                                shader_nodes.append(node)
            else:
                pass
    if z_node:
        z_nodes = setup_z_node(z_node)
        for each in z_nodes:
            utility_nodes.append(each)
    all_nodes = light_nodes+utility_nodes+shader_nodes
    select(all_nodes)
    auto_place()
    select(d=True)
    backdrop(name='%s Lights' % render_pass[0:3], nodes=light_nodes, move_offset=(biggest_x(), 0))
    util_biggest = biggest_x()
    backdrop(name='%s Utilities' % render_pass[0:3], nodes=utility_nodes, move_offset=(util_biggest, 0))
    backdrop(name='%s Beauty' % render_pass[0:3], nodes=beauty_nodes, move_offset=(util_biggest, 0),
             move=(0, 400))
    backdrop(name='%s Shading' % render_pass[0:3], nodes=shader_nodes, move_offset=(biggest_x(), 0))


    return light_nodes, utility_nodes, shader_nodes, beauty_nodes
    #light_merge = create_merge(nodes=light_nodes, operation='plus')
    #light_nodes.append(light_merge)
    select(light_nodes)

    auto_place(light_nodes)
    x_offset = biggest_x()
    # move_nodes(plus_x=0, plus_y=100, start_x=x_offset, start_y=y_offset, nodes=light_nodes)

    select(d=True)
    select(utility_nodes)
    auto_place(utility_nodes)
    x_offset = biggest_x()
    move_nodes(start_x=x_offset, nodes=utility_nodes)

    select(d=True)
    #shader_merge = create_merge(nodes=shader_nodes, operation='plus')
    #shader_nodes.append(shader_merge)
    select(shader_nodes)
    auto_place(shader_nodes)
    x_offset = biggest_x()

    select(d=True)


def auto_place(nodes=False):
    if not nodes:
        nodes = nuke.selectedNodes()
    for n in nodes:
        nuke.autoplace(n)


def move_nodes(plus_x=0, plus_y=0, start_x=0, start_y=0, nodes=None, padding=True):
    if start_x:
        x_multiplier = X_SPACE
        if padding:
            x_padding = x_multiplier*3
    else:
        x_multiplier = 0
        x_padding = 0
    if start_y:
        y_multiplier = Y_SPACE
        if padding:
            y_padding = y_multiplier*2.25
    else:
        y_multiplier = 0
        y_padding = 0
    if not nodes:
        nodes = nuke.selectedNodes()
    for i, n in enumerate(nodes):
        print(n['name'].value())
        if not start_x:
            start_x2 = n['xpos'].value()
        else:
            start_x2 = start_x
        if not start_y:
            start_y2 = n['ypos'].value()
        else:
            start_y2 = start_y
        new_x = (int(start_x2 + (x_multiplier*(i+1)) + x_padding + plus_x))
        new_y = (int(start_y2 - (y_multiplier*(i+1)) - y_padding - plus_y))
        print('moving x:%s to %s' % (n['xpos'].value(), new_x))
        print('moving y:%s to %s' % (n['ypos'].value(), new_y))
        n.setXpos(new_x)
        if start_y or plus_y:
            n.setYpos(new_y)


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
        elif y_val > n['ypos'].value():
            y_val = n['ypos'].value()
    return y_val
