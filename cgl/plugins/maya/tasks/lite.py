import os
from .smart_task import SmartTask
from .shd import import_and_attach_shaders_for_references
from .cam import get_camera_names
import cgl.plugins.maya.alchemy as lm
from cgl.plugins.maya.utils import load_plugin, get_shape_name, get_frame_end, get_frame_start
from cgl.core.utils.general import cgl_copy
from cgl.ui.widgets.base import LJDialog
from cgl.ui.widgets.dialog import InputDialog, MagicList
from cgl.ui.widgets.widgets import AdvComboBox

from cgl.plugins.Qt import QtCore, QtWidgets
import pymel.core as pm
import maya.mel

import click

LIGHT_TYPES = [u'VRayLightDomeShape', u'VRayLightIESShape', u'VRayLightMesh', u'VRayLightMeshLightLinking',
               u'VRayLightRectShape', u'VRayLightSphereShape', u'VRayPluginNodeLightShape', u'VRaySunShape',
               u'aiAreaLight', u'aiBarndoor', u'aiGobo', u'aiLightBlocker', u'aiLightDecay', u'aiPhotometricLight',
               u'aiSkyDomeLight', u'ambientLight', u'areaLight', u'directionalLight', u'pointLight', u'spotLight',
               u'volumeLight']


class Task(SmartTask):

    def __init__(self, path_object=None):
        if not path_object:
            from cgl.plugins.maya.alchemy import scene_object
            self.path_object = scene_object()

    def build(self):
        """
        1. Reference the latest model for this asset
        2. Import latest textures for this asset (and assemble a shader network)
        :return:
        """
        lm.import_task(task='lite')
        lm.import_task(task='cam')
        lm.import_task(task='anim')
        import_and_attach_shaders_for_references()
        set_up_render_settings()
        # TODO set view to shot camera.
        lm.save_file()

    def _import(self, filepath):
        lm.import_file(filepath, namespace='LGT')

    def import_latest(self):
        light_rig_path = get_latest_publish()
        self._import(light_rig_path)


def get_latest_publish():
    """
    checks for sequence publish, if that doesn't exist, checks for global publish
    :return:
    """
    seq_light_publish_render = lm.scene_object().copy(context='render', shot='0000', latest=True, user='publish',
                                                      filename='light_rig.mb', ext='mb')
    if os.path.exists(seq_light_publish_render.path_root):
        print('Sequence Lighting Found at: {}'.format(seq_light_publish_render.path_root))
        return seq_light_publish_render.path_root
    else:
        print('No Sequence Lighting Found at: {}\n\tUsing Project Lighting'.format(seq_light_publish_render.path_root))
        project_light_publish_render = lm.scene_object().copy(context='render', seq='000', shot='0000',
                                                              latest=True, user='publish', filename='light_rig.mb')
        if os.path.exists(project_light_publish_render.path_root):
            print('Project Lighting Found at: {}'.format(project_light_publish_render.path_root))
            return project_light_publish_render.path_root
        else:
            print('No Project Lighting Found at: {}, '
                  '\n\tPublish Light rigs!!!'.format(project_light_publish_render.path_root))


def get_render_folder():
    path_object = lm.scene_object().copy(context='render', filename=None, ext=None)
    return path_object.path_root


def organize_lights():
    """
    organizes all lights in a scene into a "LIGHTS" folder.
    this is a bit of a sledge hammer though, if you have an orginization you like this will blow it away.
    :return:
    """
    pm.select(d=True)
    if not pm.objExists('LIGHTS'):
        pm.group(name='LIGHTS')
    # TODO - make this smart enough not to reorganize stuff that's already in the "LIGHTS" group.
    for each in get_scene_lights(shape=True):
        pm.parent(each, 'LIGHTS')
    pm.select(d=True)


def get_scene_lights(shape=True):
    """
    creates a list of all lights in the scene.
    :param shape:
    :return:
    """
    scene_lights = []
    for each in LIGHT_TYPES:
        lights = pm.ls(type=each)
        for l in lights:
            if shape:
                l = pm.listRelatives(l, type='transform', p=True)[0]
            scene_lights.append(l)
    return scene_lights


def get_light_rig_path():
    light_rig_path = lm.scene_object().copy(context='render', filename='light_rig.mb', ext='mb').path_root
    return light_rig_path


def export_light_rig():
    pm.select(d=True)
    if pm.objExists('LIGHTS'):
        light_rig_path = get_light_rig_path()
        pm.select('LIGHTS')
        pm.exportSelected(light_rig_path, typ='mayaBinary')
        # TODO - export a lighting .msd to go with this.
    else:
        print('Organize Lights')


def publish_light_rig(global_rig=False):
    current_light_rig = get_light_rig_path()
    if os.path.exists(current_light_rig):
        # TODO - this is a bug in the core system.  Need to fix it. these should be identical.
        seq_light_publish_source = lm.PathObject(current_light_rig).copy(context='source', shot='0000',
                                                                         user='publish', filename='light_rig.mb')
        seq_light_publish_render = lm.PathObject(current_light_rig).copy(context='render', shot='0000',
                                                                         user='publish')
        cgl_copy(current_light_rig, seq_light_publish_source.path_root)
        cgl_copy(current_light_rig, seq_light_publish_render.path_root)
        if global_rig:
            global_light_publish_source = lm.PathObject(current_light_rig).copy(context='source', seq='000',
                                                                                shot='0000', latest=True,
                                                                                user='publish',
                                                                                filename='light_rig.mb')
            global_light_publish_render = lm.PathObject(current_light_rig).copy(context='render', seq='000',
                                                                                shot='0000', latest=True,
                                                                                user='publish')
            cgl_copy(current_light_rig, global_light_publish_source.path_root)
            cgl_copy(current_light_rig, global_light_publish_render.path_root)


def set_up_render_settings():
    set_renderer()
    turn_off_env_bg()
    set_render_globals()
    set_file_type()
    set_up_aovs()
    create_light_passes()


def set_renderer():
    """
    ensure the renderer is set properly within the scene
    :return:
    """
    maya.mel.eval('unifiedRenderGlobalsWindow;')
    load_plugin('mtoa')
    pm.setAttr("defaultRenderGlobals.currentRenderer", "arnold", type="string")


def set_render_globals(gui=True):
    """
    set up render globals for the scene.  This launches a GUI.
    :return:
    """
    if gui:
        this = RenderDialog(auto_set=True)
        this.exec_()
    else:
        print('this is what happens if gui mode is false')
    pass


def set_file_type(ext='exr'):
    """
    sets file type to exr by default, but can be changed by the user
    :param ext:
    :return:
    """
    pm.setAttr("defaultArnoldDriver.ai_translator", ext, type="string")


def set_up_aovs():
    """
    Sets up default passes
    :return:
    """
    # debugging passes
    safe_aiaov_create('diffuse_direct', 'rgb')
    safe_aiaov_create('diffuse_indirect', 'rgb')
    safe_aiaov_create('specular_direct', 'rgb')
    safe_aiaov_create('specular_indirect', 'rgb')
    safe_aiaov_create('sss', 'rgb')
    safe_aiaov_create('transmission', 'rgba')
    # handy comp passes
    safe_aiaov_create('N', 'vector')
    safe_aiaov_create('P', 'vector')
    safe_aiaov_create('Z', 'vector')
    # handy debug passes
    safe_aiaov_create('cputime', 'float')
    pass


def turn_off_env_bg():
    env_lights = pm.ls(type='aiSkyDomeLight')
    if env_lights:
        for e in env_lights:
            pm.setAttr('%s.camera' % e, 0)
    #     dialog = InputDialog(title='Env Light Found', message='I found an Env Light, \n'
    #                                                           'Do you want to turn off Visibility to Camera?',
    #                          buttons=['Keep My Settings', 'Turn Off Visibility'])
    #     dialog.exec_()
    #     if dialog.button == 'Turn Off Visibility':
    #         for e in env_lights:
    #             pm.setAttr('%s.camera' % e, 0)
    #         print('turned off sky dome camera visibility')
    #         return True
    #     else:
    #         print("Keeping your env light settings")
    #         return False
    # else:
    #     return True


def safe_aiaov_create(name, aov_type):
    import mtoa.aovs as aovs
    n = 'aiAOV_%s' % name
    if not pm.objExists(n):
        aovs.AOVInterface().addAOV(name, aovType=aov_type)


def create_light_passes(create_hidden=False):
    """
    Creates a seperate AOV for each light for use in comp.
    :param create_hidden:
    :return:
    """
    for each in get_scene_lights():
        if not create_hidden:
            # see if the light is visible
            visible = pm.getAttr('%s.visibility' % each)
            try:
                # see if the light's parent is visible
                par_vis = pm.getAttr('%s.visibility' % pm.listRelatives(each, parent=True)[0])
                if not par_vis:
                    visible = False
            except IndexError:
                pass
        else:
            visible = True
        if visible:
            light_name = each
            if ':' in light_name:
                light_name = light_name.split(':')[-1]
            pm.setAttr(each.aiAov, light_name)
            safe_aiaov_create('RGBA_%s' % light_name, 'rgb')


def submit_render_to_farm():
    dlg = RenderLayersDialog()
    dlg.show()
    return dlg.rendered


def get_render_layers():
    r_layers = []
    for l in pm.nodetypes.RenderLayer.listAllRenderLayers():
        r_layers.append(l.name())
    return r_layers


class RenderDialog(LJDialog):

    def __init__(self, parent=None, auto_set=False):
        LJDialog.__init__(self, parent)
        # TODO - need to put this into globals
        self.button = ''
        self.res_d = {'hd': '1920x1080',
                      'half_hd': '960x540'}
        resolutions = []
        for each in self.res_d:
            resolutions.append(each)
        v_layout = QtWidgets.QVBoxLayout()
        self.render_layer_label = QtWidgets.QLabel("<b>%s</b>" % 'Render Layer')
        self.sframe_label = QtWidgets.QLabel('Start Frame')
        self.eframe_label = QtWidgets.QLabel('End Frame')
        self.resolution_label = QtWidgets.QLabel('Resolution')
        self.camera_label = QtWidgets.QLabel('Camera')
        self.sframe_line_edit = QtWidgets.QLineEdit()
        self.eframe_line_edit = QtWidgets.QLineEdit()
        self.resolution_combo_box = AdvComboBox()
        self.camera_combo_box = AdvComboBox()
        self.row = QtWidgets.QHBoxLayout()
        self.button_row = QtWidgets.QHBoxLayout()
        self.set_globals_button = QtWidgets.QPushButton('Set Globals')
        self.path_label = QtWidgets.QLabel('Path')
        self.path_line_edit = QtWidgets.QLineEdit()
        self.render_layer_line_edit = QtWidgets.QLineEdit()

        # self.row.addWidget(self.render_layer_label)
        # self.row.addWidget(self.render_layer_line_edit)
        self.row.addWidget(self.sframe_label)
        self.row.addWidget(self.sframe_line_edit)
        self.row.addWidget(self.eframe_label)
        self.row.addWidget(self.eframe_line_edit)
        self.row.addWidget(self.resolution_label)
        self.row.addWidget(self.resolution_combo_box)
        self.row.addWidget(self.camera_label)
        self.row.addWidget(self.camera_combo_box)
        self.row.addWidget(self.path_label)
        self.row.addWidget(self.path_line_edit)

        self.button_row.addItem(QtWidgets.QSpacerItem(0, 0, QtWidgets.QSizePolicy.Expanding,
                                                      QtWidgets.QSizePolicy.Minimum))
        self.button_row.addWidget(self.set_globals_button)

        v_layout.addLayout(self.row)
        v_layout.addLayout(self.button_row)
        self.setLayout(v_layout)
        self.setWindowTitle("Set Globals")

        self.camera_combo_box.setEditable(False)
        self.resolution_combo_box.setEditable(False)
        self.path_line_edit.setMinimumWidth(480)
        render_path = get_render_folder()
        self.path_line_edit.setText(render_path)
        self.sframe_line_edit.setText(str(get_frame_start()))
        self.eframe_line_edit.setText(str(get_frame_end()))
        self.resolution_combo_box.addItems(resolutions)
        self.camera_combo_box.addItems(get_camera_names())

        self.set_globals_button.clicked.connect(self.set_globals_clicked)
        if auto_set:
            self.set_globals_clicked()

    def set_globals_clicked(self):
        self.button = 'Set Globals'
        sframe = self.sframe_line_edit.text()
        eframe = self.eframe_line_edit.text()
        w, h = self.res_d[self.resolution_combo_box.currentText()].split('x')
        camera = self.camera_combo_box.currentText()
        path = self.path_line_edit.text()

        pm.mel.setMayaSoftwareFrameExt(3, 0)
        pm.setAttr("defaultRenderGlobals.extensionPadding", 4)
        pm.setAttr('defaultRenderGlobals.extensionPadding', 4)
        pm.setAttr("defaultRenderGlobals.fs", float(sframe))
        pm.setAttr("defaultRenderGlobals.ef", float(eframe))
        pm.setAttr('defaultResolution.w', int(w))
        pm.setAttr('defaultResolution.h', int(h))
        pm.workspace(fileRule=['images', path])

        # Set the selected camera as the "renderable" camera
        for i in range(self.camera_combo_box.count()):
            shape_node = get_shape_name(self.camera_combo_box.itemText(i))
            if str(self.camera_combo_box.itemText(i)) == str(camera):
                pm.setAttr('%s.renderable' % shape_node, 1)
                # set renderable = True
            else:
                pm.setAttr('%s.renderable' % shape_node, 0)
        # remove all other cameras as "renderable"
        render_cams = get_camera_names(renderable=True)
        for each in render_cams:
            if each != get_shape_name(camera):
                render_cams.remove(each)
        self.accept()


class RenderLayersDialog(MagicList):

    def __init__(self, parent=None, title='Submit Render Layers', layers=get_render_layers()):
        MagicList.__init__(self, parent, list_items=layers, title=title, buttons=['Render Selected Layers'])
        self.selected = []
        self.item_selected.connect(self.on_selected)
        self.button_functions = [self.render_selected]
        self.rendered = False

    def on_selected(self, data):
        self.selected = []
        pm.select(d=True)
        for each in data:
            self.selected.append(each[0])
            pm.select(each, add=True)

    def render_selected(self):
        import cgl.plugins.maya.deadline_util as deadline
        reload(deadline)
        for d in self.selected:
            deadline.submit_to_deadline(render_layer=d)
        self.rendered = True


