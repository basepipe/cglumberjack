import os
import re
from cgl.plugins.Qt import QtCore, QtWidgets
import pymel.core as pm
from .smart_task import SmartTask
from cgl.ui.widgets.dialog import InputDialog
from cgl.ui.widgets.base import LJDialog
from cgl.plugins.maya.alchemy import PathObject
from cgl.core.config import shader_config, app_config
from cgl.ui.widgets.widgets import AdvComboBox

DEFAULT_SHADER = 'aiStandardSurface'  # TODO - add this in the globals.
DEFAULT_EXT = 'tx'  # TODO - add this in the globals
SHADER_CONFIG = shader_config()['shaders']
ROOT = app_config()['paths']['root']


class Task(SmartTask):

    def __init__(self, path_object=None):
        if not path_object:
            from cgl.plugins.maya.alchemy import scene_object
            self.path_object = scene_object()

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

    def import_latest(self, ref_node):
        self._import(ref_node)


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
    filepath = str(ref_node)
    name_space = ref_node.namespace
    tex_root = get_latest_tex_publish_from_filepath(filepath)
    shading_dict = get_shading_dict(tex_root)  # these should be made at texture publish time.
    for mtl_group in shading_dict:

        shader = create_and_attach_shader(mtl_group, name_space=name_space)
        import_and_connect_textures(shader, shading_dict=shading_dict)


def get_latest_tex_publish_from_filepath(filepath):
    """
    given an asset filepath return the latest published textures for the asset.
    :param filepath:
    :return:
    """
    # TODO - could i do this from just the asset name alone?
    path_object = PathObject(filepath).copy(task='tex', context='render', user='publish',
                                            latest=True, resolution='high')
    return os.path.dirname(path_object.path_root)


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


def create_and_attach_shader(mtl_group, name_space=None, source_shader=DEFAULT_SHADER):
    """
    Creates a Shader for the mtl_group and attaches it to said group.
    :param mtl_group: string representing mtl group - comes from the texture publish
    :param name_space: string representing namespace of asset we're working with.
    :param source_shader: string representing the shader we're creating (aiStandard, blinn, lambert. etc...)
    :return:
    """
    print("Found Published Textures for {}: Creating Shader".format(mtl_group))
    material = '{}:{}_mtl'.format(name_space, mtl_group)
    shader_name = "{}_shd".format(mtl_group)
    sg_name = "{}_SG".format(mtl_group)
    if pm.objExists(shader_name):
        shader = shader_name
    else:
        shader = pm.shadingNode(str(source_shader), asShader=True, name=shader_name)
    if not pm.objExists(sg_name):
        pm.sets(renderable=True, noSurfaceShader=True, empty=True, name=sg_name)
        pm.connectAttr('%s.outColor' % shader, '%s.surfaceShader' % sg_name)
    pm.select(d=True)
    pm.select(material)
    pm.sets(sg_name, forceElement=True)
    pm.select(d=True)
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
    file_node = pm.shadingNode('file', asTexture=True, isColorManaged=True)
    place_tex = pm.shadingNode('place2dTexture', asUtility=True)
    pm.connectAttr(place_tex.coverage, file_node.coverage, force=True)
    pm.connectAttr(place_tex.translateFrame, file_node.translateFrame, force=True)
    pm.connectAttr(place_tex.rotateFrame, file_node.rotateFrame, force=True)
    pm.connectAttr(place_tex.mirrorV, file_node.mirrorV, force=True)
    pm.connectAttr(place_tex.stagger, file_node.stagger, force=True)
    pm.connectAttr(place_tex.wrapU, file_node.wrapU, force=True)
    pm.connectAttr(place_tex.wrapV, file_node.wrapV, force=True)
    pm.connectAttr(place_tex.repeatUV, file_node.repeatUV, force=True)
    pm.connectAttr(place_tex.offset, file_node.offset, force=True)
    pm.connectAttr(place_tex.rotateUV, file_node.rotateUV, force=True)
    pm.connectAttr(place_tex.noiseUV, file_node.noiseUV, force=True)
    pm.connectAttr(place_tex.vertexUvOne, file_node.vertexUvOne, force=True)
    pm.connectAttr(place_tex.vertexUvTwo, file_node.vertexUvTwo, force=True)
    pm.connectAttr(place_tex.vertexUvThree, file_node.vertexUvThree, force=True)
    pm.connectAttr(place_tex.vertexCameraOne, file_node.vertexCameraOne, force=True)
    pm.connectAttr(place_tex.outUV, file_node.uv)
    pm.connectAttr(place_tex.outUvFilterSize, file_node.uvFilterSize)
    # pm.defaultNavigation -force true -connectToExisting -source file_node -destination shd.outColor)
    #  window -e -vis false createRenderNodeWindow)
    if not normal:
        if not channel:
            pm.connectAttr(file_node.outColor, '%s.%s' % (shader, attr), force=True)
        elif channel == 'r':
            # TODO - fix single channel .txmake stuff - it errors out with the current settings.
            tex_path = tex_path.replace('.tx', '.exr')
            pm.connectAttr(file_node.outColor.outColorR, '%s.%s' % (shader, attr), force=True)
        elif channel == 'g':
            pm.connectAttr(file_node.outColor.outColorG, '%s.%s' % (shader, attr), force=True)
        elif channel == 'b':
            pm.connectAttr(file_node.outColor.outColorB, '%s.%s' % (shader, attr), force=True)
    else:
        bump_node = pm.shadingNode('bump2d', asUtility=True)
        pm.setAttr('%s.alphaIsLuminance' % file_node, True)
        pm.connectAttr(file_node.outAlpha, '%s.bumpValue' % bump_node)
        pm.connectAttr('%s.outNormal' % bump_node, '%s.normalCamera' % shader)
        pm.setAttr('%s.aiFlipR' % bump_node, 0)
        pm.setAttr('%s.aiFlipG' % bump_node, 0)
        pm.setAttr('%s.bumpInterp' % bump_node, 1)
        #
        if shader_attrs:
            shader = bump_node

    pm.setAttr(file_node.fileTextureName, tex_path)
    if shader_attrs:
        for each in shader_attrs:
            attr = '%s.%s' % (shader, each)
            value = shader_attrs[each]
            pm.setAttr(attr, value)
    if color_space:
        pm.setAttr(file_node.colorSpace, color_space)

