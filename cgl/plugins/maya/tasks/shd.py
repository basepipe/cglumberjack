import re
import os
from .smart_task import SmartTask
from cgl.ui.widgets.dialog import InputDialog
import cgl.plugins.maya.utils as utils
import cgl.plugins.maya.alchemy as lm
try:
    import pymel.core as pm
    import maya.mel as mel
except ModuleNotFoundError:
    print('Skipping pymel.core - outside of maya')


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
        model_ref = lm.import_task(task='mdl', reference=True)
        lm.import_task(task='tex', ref_node=model_ref)

    def _import(self, filepath):
        pass


def get_latest_shader(path):
    shader_object = lm.PathObject(path).copy(task='shd', context='render', name='shaders',
                                             latest=True, set_proper_filename=True, ext='mb')
    return shader_object.path_root


def get_latest_anim_shader(seq, shot):
    """
    get latest shader
    :return:
    """
    filename = '%s_%s_shd_shaders' % (seq.lower(), shot.lower())
    latest_obj = lm.scene_object().copy(seq=seq, shot=shot, task='shd', context='render', user='publish',
                                        scope='assets', filename=filename, latest=True,
                                        ext='mb')
    return latest_obj.path_root


def import_and_attach_shaders_for_references(selected=False):
    # TODO - it'd be nice to be able to give it a string as a filter for what to look for in specific cases
    """
    parses a scene and attach shaders to all asset references.
    :return:
    """
    if selected:
        refs = utils.get_selected_reference()
    else:
        refs = pm.listReferences(refNodes=True)
    # for each reference figure out the shader publish
    if refs:
        for ref in refs:
            if pm.referenceQuery(ref[-1], isLoaded=True):
                asset_obj = lm.PathObject(str(ref[-1]))
                if asset_obj.ext == 'abc':
                    try:
                        asset_obj.seq, asset_obj.shot = asset_obj.filename.replace('.abc', '').split('_')
                    except ValueError:
                        print('ERROR: {} is a non-standard name, skipping auto-shader attachment')
                asset_obj.shot = re.sub('[0-9]+', '', asset_obj.shot)
                if asset_obj.scope == 'assets' or asset_obj.ext == 'abc':
                    if '{' in str(ref[-1]):
                        ref_path = str(ref[-1]).split('{')[0]
                    else:
                        ref_path = str(ref[-1])
                    shd_ns = '%s_shd' % asset_obj.shot
                    # does this namespace exist in the scene?
                    if shd_ns not in utils.get_namespaces():
                        if asset_obj.ext == 'abc':
                            try:
                                seq = asset_obj.seq
                                shot = asset_obj.shot
                                shd_ns = '%s_shd' % shot
                                shader_pub = get_latest_anim_shader(seq, shot)
                            except ValueError:
                                print('Invalid filename %s for reference %s' % asset_obj.filename, ref_path)
                                return
                        else:
                            shader_pub = get_latest_shader(ref_path)
                        if os.path.exists(shader_pub):
                            print('importing published shader for %s: %s' % (shd_ns, shader_pub))
                            pm.importFile(shader_pub, namespace=shd_ns)
                        else:
                            print('No Published Shaders at: %s' % shader_pub)
                    sg_list = pm.ls(regex='%s.*' % shd_ns, type='shadingEngine')
                    for sg in sg_list:
                        this = pm.PyNode(sg)
                        assigned_to_geo = pm.getAttr('%s.assigned_to' % this)
                        geometry = []
                        for a in assigned_to_geo:
                            geometry.append('*%s*:%s' % (asset_obj.shot, a))
                        try:
                            pm.sets(this, edit=True, forceElement=geometry)
                        except:
                            print('Maya Node %s not found, you probably need to republish '
                                                         'the shader' % geometry)

    mel.eval('hyperShadePanelMenuCommand("hyperShadePanel1", "deleteUnusedNodes");')

