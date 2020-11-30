import os
import re
from cgl.plugins.Qt import QtCore, QtWidgets
from .smart_task import SmartTask
from cgl.ui.widgets.dialog import InputDialog
from cgl.ui.widgets.base import LJDialog
from cgl.plugins.houdini.lumbermill import LumberObject
from cgl.core.config import shader_config, app_config
from cgl.ui.widgets.widgets import AdvComboBox
import hou


DEFAULT_SHADER = 'principledshader'  # TODO - add this in the globals.
DEFAULT_SG = 'materialbuilder'
DEFAULT_EXT = 'exr'  # TODO - add this in the globals
SHADER_CONFIG = shader_config()['shaders']
ROOT = app_config()['paths']['root']

class Task(SmartTask):

    def __init__(self, path_object=None):
        if not path_object:
            from cgl.plugins.houdini.lumbermill import scene_object
            self.path_object = scene_object()

    def build(self):
        print('No Build Script defined for textures, this would belong in Substance Painter most likely')
        pass

    def _import(self, ref_node):
        """
        Main Parent Function for importing textures.  In our context importing textures consists of a
        full usable series of events that leads to a useable baseline of textures.  In this instance that would be:
        1) Create A Shader for the Material Group
        2) Import and connect relevant textures to material group
        3) Set any default values based off our shader dictionaries.
        :param filepath:
        :return:
        """
        main_import(ref_node)

    def import_latest(self, ref_node=None):
        #assign_shaders_to_asset(model_ref)
        main_import(ref_node)

"""
Files Required to make the textures pipeline work.

config_/shaders.json - 
    this is a config file containing shader settings for specific shaders, this allows us
    to be software agnostic with our shader assembly.

get_shading_dict() - this gives us a dictionary to work with that makes it easy to process textures. Eventually this 
will likely become a file that is published with a texture publish.  

Basic order for these functions:

1) get_latest_tex_publish_from_filepath() - gets the latest published textures file based off a filepath
2) get_shading_dict() - gets a dictionary describing the published textures that we use later.
3) create_and_attach_shader() creates a shader and attaches it to the mtl_group of an asset
4) import_and_connect_textures() creates all texture nodes, and connects them to the proper slot, with the proper 
    Settings on the mtl_group shader. 

main_import() - this is a convenience function - it makes testing in the application incredibly easy because
you can just reload tex.py in the app rather than all the other dependencies.   This isn't necessary but it's easier 
for writing/testing code than to include the coe in TaskObject()._import()

"""


def main_import(ref_node):
    """
    Main Parent Function for importing textures.  In a Production Alchemy Context importing textures consists of a
    full usable series of events that leads to a useable baseline of textures.  In this instance that would be:
    1) Create A Shader for the Material Group
    2) Import and connect relevant textures to material group
    3) Set any default values based off our shader dictionaries.
    :param ref_node: takes a reference node from maya
    :return:
    """
    from cgl.plugins.houdini.lumbermill import scene_object
    if not ref_node:
        ref_node = scene_object().path_root
    filepath = str(ref_node)

    tex_root = get_latest_tex_publish_from_filepath(filepath)
    shading_dict = get_shading_dict(tex_root)  # these should be made at texture publish time.
    for mtl_group in shading_dict:
        shader = create_and_attach_shader(mtl_group)
        import_and_connect_textures(shader, shading_dict=shading_dict)


def get_latest_tex_publish_from_filepath(filepath):
    """
    given an asset filepath return the latest published textures for the asset.
    :param filepath:
    :return:
    """
    # TODO - could i do this from just the asset name alone?
    path_object = LumberObject(filepath).copy(task='tex', context='render', user='publish',
                                              latest=True, resolution='high')
    return os.path.dirname(path_object.path_root)

def objExists(shader_name):
    path = 'mat/'

    object = hou.node('{}/{}'.format(path, shader_name))

    if object:
        return True
    else:
        return False

def get_shading_dict(tex_root):
    """
    Expects a Folder with the following structure:
    ../{resolution}/{material_group}/texture_file_{channel_name}.ext

    Produces a shading dictionary with the following structure:
    Material Group ("material_mtl")
        Channel Name ("BaseColor")
            Extension ("exr", "tx")
                Texture Path (Relative)
    :param tex_root:
    :return:
    """
    udim_pattern = r"[0-9]{4}"
    ignore = ['cgl_info.json']
    ignore_ext = ['json']
    mtl_groups = os.listdir(tex_root)
    dict_ = {}
    for g in mtl_groups:
        if g in ignore:
            mtl_groups.remove(g)
        else:
            dict_[g] = {}
            for tex in os.listdir(os.path.join(tex_root, g)):
                channel_name = tex.split("_")[-1].split('.')[0]
                if channel_name not in dict_[g].keys():
                    dict_[g][channel_name] = {}
                ext = os.path.splitext(tex)[-1].replace('.', '')
                if ext not in ignore_ext:
                    if re.search(udim_pattern, tex):
                        new_t = re.sub(udim_pattern, '<UDIM>', tex)
                        tex = os.path.join(tex_root, g, new_t).replace('\\', '/')
                    dict_[g][channel_name][ext] = tex
    return dict_


def objExists(shader_name):
    path = 'mat/'

    object = hou.node('{}/{}'.format(path, shader_name))

    if object:
        return True
    else:
        return False

def create_and_attach_shader(mtl_group, name_space=None, source_shader=DEFAULT_SHADER, source_sg=DEFAULT_SG):
    """
    Creates a Shader for the mtl_group and attaches it to said group.
    :param mtl_group: string representing mtl group - comes from the texture publish
    :param name_space: string representing namespace of asset we're working with.
    :param source_shader: string representing the shader we're creating (aiStandard, blinn, lambert. etc...)
    :return:
    """
    print("Found Published Textures for {}: Creating Shader".format(mtl_group))
    materials = hou.node('mat/')

    material = '{}:{}_mtl'.format(name_space, mtl_group)
    shader_name = "{}_shd".format(mtl_group)
    sg_name = "{}_SG".format(mtl_group)

    # Creates shading group

    shading_group = materials.createNode(source_sg, sg_name)

    # Creates material

    if shader_name not in get_node_children(shading_group):
        shader = shading_group.createNode(source_shader, shader_name)

    else:
        shader = shading_group.node(shader_name)

    if source_sg == 'materialbuilder':
        nodes_to_delete = ('surface_globals',
                           'surface_output',
                           'displacement_output',
                           'displacement_globals')

        use_textures = ('basecolor_useTexture',
                        'rough_useTexture',
                        'metallic_useTexture',
                        'reflecttint_useTexture',
                        'baseBumpAndNormal_enable')

        shading_group.node('output_collect').setInput(0, shader, 0)

        for node in nodes_to_delete:
            try:

                shading_group.node(node).destroy()
            except:
                pass

        for parameter in use_textures:
            shader.parm(parameter).set(True)

        shader.parm('rough').set(1)
        shader.parm('metallic').set(1)

    assign_material_to_children(shader_name)
    return shader_name





def get_selected_namespace():
    """
    gets the namespace of the selected object.
    :return:
    """
    sel = pm.ls(sl=True)[0]
    if ':' in sel:
        name_space = sel.split(':')
    else:
        print('{} has no namespace'.format(sel))
        return None
    return name_space


def get_attr_dict_for_tex_channel(tex_channel, shader=DEFAULT_SHADER):
    """
    queries the current texture channel against our shader dictionaries, returns the proper channel
    to plug the texture into.
    :param tex_channel:
    :param shader:
    :return:
    """
    # TODO - this would be the place to allow for people to add to the dictionary.
    for parameter in SHADER_CONFIG[shader]['parameters']:
        if tex_channel in SHADER_CONFIG[shader]['parameters'][parameter]['name_match']:
            return SHADER_CONFIG[shader]['parameters'][parameter]
    print("\tshading.json - No shading config match found for texture channel: {}".format(tex_channel))
    return None


def import_and_connect_textures(shader_node, shading_dict, mtl_group=None,
                                ext=DEFAULT_EXT):
    """
    creates the proper texture nodes for the texture_path in the scene.
    :param shader_node:
    :param mtl_group:
    :param shading_dict:
    :param ext:
    :param shader:
    :return:
    """
    if not mtl_group:
        mtl_group = shader_node.replace('_shd', '')
    for tex_channel in shading_dict[mtl_group]:
        if list(shading_dict[mtl_group][tex_channel].keys()):
            if ext not in list(shading_dict[mtl_group][tex_channel].keys()):
                ext = list(shading_dict[mtl_group][tex_channel].keys())[0]
            texture_path = shading_dict[mtl_group][tex_channel][ext]
            # TODO - take relative path and make it absolute
            # full_path = os.path.join(ROOT, texture_path)
            full_path = texture_path
            channel_ = get_attr_dict_for_tex_channel(tex_channel)
            if channel_:
                attr_ = channel_['attr']
                try:
                    normal = channel_['normal']
                except KeyError:
                    normal = False
                try:
                    channel = channel_['channel']
                except KeyError:
                    channel = None
                try:
                    shader_attrs = channel_['shader_attrs']
                except KeyError:
                    shader_attrs = None
                try:
                    color_space = channel_['colorspace']
                except KeyError:
                    color_space = None
                assign_texture_to_shader(full_path, shader_node, attr_, channel=channel,
                                         normal=normal, color_space=color_space, shader_attrs=shader_attrs)
    hou.node('/mat').layoutChildren()

def assign_texture_to_shader(tex_path, shader, attr, channel=False, normal=False, color_space=None, shader_attrs=None):
    """
    Creates texture nodes and connects them to shaders.  Works with the Shader.json config file to understand
    what to do with various types of shaders.
    :param tex_path:
    :param shader:
    :param attr:
    :param channel:
    :param normal:
    :param color_space:
    :param shader_attrs:
    :return:
    """

    # print('\tAttaching texture {} to shader {} at attr {}'.format(tex_path, shader, attr))
    tex_path = r'%s' % tex_path

    # print(1111111111111111)
    # print('mat/{}_SG'.format(shader))
    shading_group = hou.node('mat/{}'.format(shader.replace('_shd', '_SG')))
    shader = shading_group.node(shader)

    texture = shading_group.node(attr)
    if not texture:
        texture = shading_group.createNode('texture', attr)

    texture.parm('map').set(tex_path.replace('<UDIM>', '%(UDIM)d'))
    texture.setDetailLowFlag(True)

    input = shader.inputIndex(attr)
    shader.setInput(input, texture)
    shading_group.layoutChildren()


def get_node_children(node):
    children = node.children()
    list = []
    for child in children:
        list.append(child.name())
    return list


def assign_material_to_children(shader):
    mtl_name = shader.replace('shd', 'mtl')
    SG_path = '/mat/{}'.format(shader.replace('shd', 'SG'))
    object = hou.node('obj/{}'.format(mtl_name))

    for obj in object.outputs():
        obj.parm('shop_materialpath').set(SG_path)