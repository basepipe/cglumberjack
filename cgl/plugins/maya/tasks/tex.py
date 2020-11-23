import os
import re
from cgl.plugins.Qt import QtCore, QtWidgets
import pymel.core as pm
from .smart_task import SmartTask
from cgl.ui.widgets.dialog import InputDialog
from cgl.ui.widgets.base import LJDialog
from cgl.plugins.maya.lumbermill import LumberObject
from cgl.core.config import shader_config
from cgl.ui.widgets.widgets import AdvComboBox


class Task(SmartTask):

    def __init__(self, path_object=None):
        if not path_object:
            from cgl.plugins.maya.lumbermill import scene_object
            self.path_object = scene_object()

    def build(self):
        pass

    def import_latest(self, model_ref=None):
        from cgl.plugins.maya.lumbermill import import_task
        from cgl.plugins.maya.utils import load_plugin
        load_plugin('mtoa')
        # turn off render thumbnail update in hypershade!
        pm.renderThumbnailUpdate(False)
        # if i get a path - i need to pull the asset name out of it.
        assign_shaders_to_asset(model_ref)


def assign_shaders_to_asset(mdl_path, res='high'):

    # mdl_path = pm.referenceQuery('%s:mdl' % asset, filename=True, wcn=True)
    mdl_object = LumberObject(str(mdl_path))
    res = '%s:%s' % (mdl_object.asset, res)
    tex_object = mdl_object.copy(task='tex', context='render', latest=True, set_proper_filename=True)
    tex_path = os.path.dirname(tex_object.path_root)
    if os.path.exists(tex_path):
        for mat in pm.listRelatives(res, children=True):
            pm.select(d=True)
            pm.select(mat)
            sel = pm.ls(sl=True)[0]
            d_ = ShaderSetup(material=sel, tex_root=tex_path, tx_only=True)
            d_.exec_()
    else:
        print('Could not find tex path %s' % tex_path)


def assign_shader_to_selected_mtl_group():
    sel = pm.ls(sl=True)
    for s in sel:
        if '_mtl' in str(s):
            asset = s.split(':')[0]
            mdl_path = pm.referenceQuery('%s:mdl' % asset, filename=True, wcn=True)
            mdl_object = LumberObject(mdl_path)
            tex_object = mdl_object.copy(context='render', task='tex', resolution='high', latest=True)
            tex_path = os.path.dirname(tex_object.path_root)
            dialog.ShaderSetup(material=s, tex_root=tex_path, tx_only=True).exec_()
        else:
            print('%s is not a proper _mtl group' % s)


def tag_shaders():
    this_file = pm.sceneName()
    pub_version = PathParser().get_next_version_number(this_file, pub=True)
    pub_location = PathParser().copy_path(this_file, user='publish', version=pub_version)
    sg_list = pm.ls(type='shadingEngine')
    for sg in sg_list:
        shaderobjects = []
        attached = pm.sets(sg, query=1)
        if attached:
            for mesh in attached:
                shaderobjects.append(mesh.getParent())
            stamp_attr(sg, 'assigned_to', shaderobjects)
            stamp_attr(sg, 'published_at', pub_location)


def stamp_attr(node, attr, value_):
    check = pm.attributeQuery(attr, n=node, ex=True)
    attrname = '%s.%s' % (node, attr)
    try:
        if check:
            if isinstance(value_, list):
                pm.setAttr(attrname, l=False)
                pm.setAttr(attrname, value_, type='stringArray')
                pm.setAttr(attrname, l=True)
            else:
                pm.setAttr(attrname, l=False)
                pm.setAttr(attrname, value_, type='string')
                pm.setAttr(attrname, l=True)
        else:
            if isinstance(value_, list):
                pm.addAttr(node, ln=attr, dt='stringArray')
                pm.setAttr(attrname, value_)
                pm.setAttr(attrname, l=True)
            else:
                pm.addAttr(node, ln=attr, dt='string')
                pm.setAttr(attrname, value_)
                pm.setAttr(attrname, l=True)
    except RuntimeError:
        print('%s is from a referenced shader %s' % (attr, node))


def tag_attr(obj, attr, value, type_='bool', is_ref=True):
    if is_ref:
        top_node = obj.nodes()[0]
    else:
        top_node = obj
    types = ['string', 'stringArray']
    if not pm.hasAttr(top_node, attr):
        if type_ in types:
            pm.addAttr(top_node, ln=attr, dt=type_)
        else:
            pm.addAttr(top_node, ln=attr, at=type_)
    pm.setAttr('%s.%s' % (top_node.name(), attr), value)
    return top_node.attr(attr)


def assign_texture_to_shader(tex_path, shader, attr, channel=False, normal=False, color_space=None, shader_attrs=None):
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


def apply_shader_attrs(shader, shader_attrs):
    if shader_attrs:
        for each in shader_attrs:
            attr = '%s.%s' % (shader, each)
            value = shader_attrs[each]
            try:
                pm.setAttr(attr, value)
            except:
                print('Could not find {}, skipping'.format(attr))


class ShaderSetup(LJDialog):

    def __init__(self, parent=None, material=None, tex_root=None, tx_only=False, default_shader='aiStandardSurface'):
        LJDialog.__init__(self, parent)
        from cgl.plugins.maya.utils import get_maya_window

        main_maya_window = get_maya_window()
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose, True)
        self.parent = main_maya_window
        self.material = material
        self.width = 500
        self.shader_dict = shader_config()['shaders']
        udim_pattern = r"[0-9]{4}"
        textures = []
        tex_root_material = r'%s' % os.path.join(tex_root, self.material.split(':')[-1].split('_')[0])
        if os.path.exists(tex_root_material):
            tex_root = tex_root_material
        for t in os.listdir(tex_root):
            if tx_only:
                if t.endswith('tx'):
                    if re.search(udim_pattern, t):
                        _, ext_ = os.path.splitext(t)
                        new_t = re.sub(udim_pattern, '<UDIM>', t)
                        t = new_t
                    if t not in textures:
                        textures.append(t)
            else:
                textures.append(t)
        self.tex_root = tex_root
        shaders = ['']
        for each in self.shader_dict:
            shaders.append(each)
        if len(shaders) == 2:
            shaders.pop(0)
        self.create_shader = QtWidgets.QPushButton('Create Shader')
        v_layout = QtWidgets.QVBoxLayout()
        self.button_row = QtWidgets.QHBoxLayout()
        self.button_row.addItem(QtWidgets.QSpacerItem(0, 0, QtWidgets.QSizePolicy.Expanding,
                                                      QtWidgets.QSizePolicy.Minimum))
        self.button_row.addWidget(self.create_shader)
        self.material_row = QtWidgets.QHBoxLayout()
        if ":" in material:
            material = material.split(':')[-1]
        self.mat_name = QtWidgets.QLabel("<b>%s</b>" % material)
        self.mat_label = QtWidgets.QLabel("Choose a Shader:")
        self.textures_label = QtWidgets.QLabel("<b>Connect Textures</b>")
        self.mat_combo = AdvComboBox()
        self.mat_shaders = shaders
        self.mat_combo.addItems(self.mat_shaders)

        self.material_row.addWidget(self.mat_name)
        self.material_row.addItem(QtWidgets.QSpacerItem(0, 0, QtWidgets.QSizePolicy.Expanding,
                                                        QtWidgets.QSizePolicy.Minimum))
        self.material_row.addWidget(self.mat_label)
        self.material_row.addWidget(self.mat_combo)
        v_layout.addLayout(self.material_row)
        v_layout.addItem(QtWidgets.QSpacerItem(0, 0, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum))
        v_layout.addWidget(self.textures_label)
        self.row_dict = {}
        for each in textures:
            self.label = QtWidgets.QLabel('%s' % each)
            combo = AdvComboBox()
            # combo.currentIndexChanged.connect(self.on_parameter_changed)
            if len(shaders) == 1:
                combo.addItems(shaders)
            # find a match in shaders for to_match
            item_row = QtWidgets.QHBoxLayout()
            item_row.addWidget(self.label)
            item_row.addWidget(combo)
            self.row_dict.update({self.label: combo})
            v_layout.addLayout(item_row)
        v_layout.addLayout(self.button_row)
        self.setLayout(v_layout)
        self.setWindowTitle("Assign Textures to Shader Attr")
        self.mat_combo.currentIndexChanged.connect(self.on_shader_changed)
        if default_shader:
            index = self.mat_combo.findText(default_shader)
            if index != -1:
                self.mat_combo.setCurrentIndex(index)
        self.create_shader.clicked.connect(self.on_create_shader)
        if default_shader:
            self.on_shader_changed()
        else:
            self.hide_textures()

    def hide_textures(self, show=False):
        if show:
            self.textures_label.show()
            self.create_shader.show()
        else:
            self.textures_label.hide()
            self.create_shader.hide()
        for key in self.row_dict:
            if show:
                key.show()
                self.row_dict[key].show()
            else:
                key.hide()
                self.row_dict[key].hide()

    def on_shader_changed(self):

        shader_name = self.mat_combo.currentText()
        print(shader_name)
        params = self.shader_dict[shader_name]['parameters']
        for key in self.row_dict:
            item_num = 'Null'
            to_match = key.text().split("_")[-1].split('.')[0]
            self.row_dict[key].clear()
            i = -1
            for p in params:
                i += 1
                try:
                    if str(to_match) in params[p]['name_match']:
                        item_num = i
                except KeyError:
                    pass
                self.row_dict[key].addItem(p)
            if item_num != 'Null':
                self.row_dict[key].setCurrentIndex(item_num)
            else:
                self.row_dict[key].insertItem(0, '')
                self.row_dict[key].setCurrentIndex(0)
        self.hide_textures(show=True)

    def on_parameter_changed(self):
        text = self.sender().currentText()
        for key in self.row_dict:
            if self.row_dict[key] == self.sender():
                print(key.text().split(':  ')[-1], text)

    def on_create_shader(self):
        source_shader = self.mat_combo.currentText()
        shader_name = '%s_shd' % self.material.name().split(':')[-1].split('_mtl')[0]
        if pm.objExists(shader_name):
            shader = shader_name
        else:
            shader = pm.shadingNode(str(source_shader), asShader=True, name=shader_name)
        default_attrs = self.shader_dict[self.mat_combo.currentText()]['default_shader_attrs']
        if default_attrs:
            apply_shader_attrs(shader, shader_attrs=default_attrs)
        sg_name = shader_name.replace('shd', 'SG')
        if not pm.objExists(sg_name):
            sg = pm.sets(renderable=True, noSurfaceShader=True, empty=True, name=sg_name)
            pm.connectAttr('%s.outColor' % shader, '%s.surfaceShader' % sg)
        pm.select(self.material)
        pm.sets(sg_name, forceElement=True)
        self.accept()
        testy = ['diffuse', 'normal', 'specRough', 'metalness']
        # testy = ['specRough']
        for key in self.row_dict:
            file_name = key
            attr = self.row_dict[key]
            if attr.currentText() != '':
                if attr.currentText() in testy:
                    full_path = os.path.join(self.tex_root, file_name.text())
                    channel_ = self.shader_dict[self.mat_combo.currentText()]['parameters'][attr.currentText()]
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
                    assign_texture_to_shader(full_path, shader, attr_, channel=channel, normal=normal,
                                             color_space=color_space, shader_attrs=shader_attrs)

        self.accept()


# all the new stuff goes below this line -----------------------------------------------------------------------------

# --------------------------------------------------------------------------------------------------------------------


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


def import_textures(filepath):
    """
    Main Parent Function for importing textures.  In a Production Alchemy Context importing textures consists of a
    full usable series of events that leads to a useable baseline of textures.  In this instance that would be:
    1) Create A Shader for the Material Group
    2) Import and connect relevant textures to material group
    3) Set any default values based off our shader dictionaries.
    :param filepath:
    :return:
    """
    tex_root = get_latest_tex_publish_from_filepath(filepath)
    print('tex_root {}'.format(tex_root))
    shading_dict = get_shading_dict(tex_root)  # these should be made at texture publish time.
    for mtl_group in shading_dict:
        attach_textures_to_geometry(mtl_group, shading_dict)


def get_shading_dict(tex_root):
    """
    Expects a Folder with the following structure:
    ../{resolution}/{material_group}/texture_file_{channel_name}.ext

    Produces a shading dictionary with the following structure:
    Material Group
        Channel Name
            Extension
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


def attach_textures_to_geometry(mtl_group, dict_, ext='tx'):
    """
    Creates a Shader, attaches that to gemoetry group.
    Imports all textures relevant to this geometry, and connects them to the shader.

    :param mtl_group:
    :param dict_:
    :param ext:
    :return:
    """
    shader = create_and_attach_shader(mtl_group)
    for tex_channel in dict_[mtl_group]:
        if list(dict_[mtl_group][tex_channel].keys()):
            if ext not in list(dict_[mtl_group][tex_channel].keys()):
                ext = list(dict_[mtl_group][tex_channel].keys())[0]
            connect_textures(mtl_group, tex_channel, dict_[mtl_group][tex_channel][ext])
            edit_additional_parameters(shader, tex_channel)
            # TODO  - set any additional per parameter values determined by our shader globals


def create_and_attach_shader(mtl_group):
    """
    Creates a Shader for the mtl_group and attaches it to said group.
    :param mtl_group:
    :return:
    """
    print('Creating Shader for {}'.format(mtl_group))
    return(mtl_group)


def get_shader_parameter_for_tex_channel(tex_channel):
    """
    queries the current texture channel against our shader dictionaries, returns the proper channel
    to plug the texture into.
    :param shader:
    :param parameter:
    :return:
    """
    # TODO - this would be the place to allow for people to add to the dictionary.
    print('\tQuerying Shader Parameter for {}'.format(tex_channel))
    return tex_channel


def edit_additional_parameters(shader_node, tex_channel):
    """
    sets additional parameters depending on defaults for the tex channel
    :param shader_node:
    :param tex_channel:
    :return:
    """
    print('\tSetting additional parameters for {} on shader_node {}'.format(tex_channel, shader_node))


def connect_textures(shader_node, tex_channel, texture_path):
    """
    creates the proper texture nodes for the texture_path in the scene.
    :param shader_node:
    :param tex_channel:
    :param texture_path:
    :return:
    """
    print('\tImporting {} into scene'.format(texture_path))
    parameter = get_shader_parameter_for_tex_channel(tex_channel)
    print('\tAttaching texture {} to shader {} at parameter {}'.format(texture_path, shader_node, parameter))

