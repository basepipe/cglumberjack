import os
from .smart_task import SmartTask
from .shd import import_and_attach_shaders_for_references
import cgl.plugins.maya.lumbermill as lm
from cgl.core.utils.general import cgl_copy
import pymel.core as pm
import click

LIGHT_TYPES = [u'VRayLightDomeShape', u'VRayLightIESShape', u'VRayLightMesh', u'VRayLightMeshLightLinking',
               u'VRayLightRectShape', u'VRayLightSphereShape', u'VRayPluginNodeLightShape', u'VRaySunShape',
               u'aiAreaLight', u'aiBarndoor', u'aiGobo', u'aiLightBlocker', u'aiLightDecay', u'aiPhotometricLight',
               u'aiSkyDomeLight', u'ambientLight', u'areaLight', u'directionalLight', u'pointLight', u'spotLight',
               u'volumeLight']


class Task(SmartTask):

    def __init__(self, path_object=None):
        if not path_object:
            from cgl.plugins.maya.lumbermill import scene_object
            self.path_object = scene_object()

    def build(self):
        """
        1. Reference the latest model for this asset
        2. Import latest textures for this asset (and assemble a shader network)
        :return:
        """
        self.import_latest()
        lm.import_task(task='cam')
        lm.import_task(task='anim')
        import_and_attach_shaders_for_references()

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
    seq_light_publish_render = lm.scene_object().copy(context='render', shot='0000', latest=True, user='publish', filename='light_rig.mb', ext='mb')
    if os.path.exists(seq_light_publish_render.path_root):
        return seq_light_publish_render.path_root
    else:
        project_light_publish_render = lm.scene_object().copy(context='render', seq='000', shot='0000', latest=True, user='publish')
        return project_light_publish_render.path_root


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
        seq_light_publish_source = lm.LumberObject(current_light_rig).copy(context='source', shot='0000',
                                                                           user='publish', filename='light_rig.mb')
        seq_light_publish_render = lm.LumberObject(current_light_rig).copy(context='render', shot='0000',
                                                                           user='publish')
        cgl_copy(current_light_rig, seq_light_publish_source.path_root)
        cgl_copy(current_light_rig, seq_light_publish_render.path_root)
        if global_rig:
            global_light_publish_source = lm.LumberObject(current_light_rig).copy(context='source', seq='000',
                                                                                  shot='0000', latest=True,
                                                                                  user='publish',
                                                                                  filename='light_rig.mb')
            global_light_publish_render = lm.LumberObject(current_light_rig).copy(context='render', seq='000',
                                                                                  shot='0000', latest=True,
                                                                                  user='publish')
            cgl_copy(current_light_rig, global_light_publish_source.path_root)
            cgl_copy(current_light_rig, global_light_publish_render.path_root)


@click.command()
@click.option('--filepath', '-f', default=None)
def main(filepath):
    mayapy_file = os.path.join(os.path.dirname(__file__), 'lite_mayapy.py')
    if os.path.exists(filepath):
        if filepath.endswith('mb') or filepath.endswith('ma'):
            command = 'mayapy {} {}'.format(mayapy_file, filepath)


if __name__ == "__main__":
    main()
