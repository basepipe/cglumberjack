from .smart_task import SmartTask
import cgl.plugins.maya.alchemy as alch
import pymel.core as pm
import maya.mel
import os
import glob
from cgl.core.path import remove_root


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
        alch.import_task(task='lay')
        alch.import_task(task='cam')

    def _import(self, filepath):
        pass

    def import_latest(self):
        """
        imports everything from latest animation publish as described in the .msd file.
        :return:
        """
        this_obj = alch.scene_object().copy(task='anim', context='render', user='publish', latest=True,
                                            set_proper_filename=True, ext='msd')
        self._import(this_obj.path_root)


def test_get_msd_info():
    from cgl.plugins.maya.tasks.cam import get_latest
    anim_ignore, anim_dict = add_anim_to_msd()
    #bundle_ignore, bundle_dict = add_bundles_to_msd()
    #ignore = anim_ignore + bundle_ignore

    #mesh_dict = add_meshes_to_msd(ignore=ignore)
    #camera_dict = add_camera_to_msd()


def add_meshes_to_dict(ignore):
    meshes = get_meshes(ignore)
    return get_mesh_dict(meshes)


def add_anim_to_msd():
    anim_ignore = get_anim()
    anim_dict = get_anim_dict()
    return anim_ignore, anim_dict


def add_bundles_to_msd():
    bundles, children = get_bundles(children=True)
    return children, bundle_dict


def get_anim():
    ref_paths = []
    if pm.objExists('ANIM'):
        anim_nodes = pm.listRelatives('ANIM', children=True)
        for a in anim_nodes:
            ref_paths.append(pm.referenceQuery(a, filename=True))
        return anim_nodes, ref_paths
    else:
        return []


def get_anim_publishes():
    this_obj = alch.scene_object().copy(task='anim', context='render', user='publish', latest=True,
                                        set_proper_filename=True, ext='msd')
    folder = os.path.dirname(this_obj.path_root)
    glob_pattern = '{}/*abc'.format(folder)
    abcs = glob.glob(glob_pattern)
    return abcs


def get_anim_dict():

    anim_dict = {'anim': {}}
    for anim in get_anim_publishes():
        abc = remove_root(anim)
        asset_name = os.path.split(abc)[-1].replace('.abc', '')
        dict_ = {
                 'transforms': {'scale': None,
                                'rotate': None,
                                'transform': None,
                                'matrix': None},
                  'msd_path': alch.scene_object().relative_msd_path,
                  'asset_name': asset_name,
                  'attrs': {'abc': abc}
                 }
        anim_dict['anim'][asset_name] = dict_
    return anim_dict


def get_bundles_dict(bundles=None):
    if not bundles:
        bundles = get_bundles()
    if bundles:
        for bndl in bundles():
            print('\t', bndl)
    else:
        return None


def get_mesh_dict(models):
    from cgl.plugins.maya.tasks.mdl import Task
    dict_ = {'meshes': {}}
    for mdl in models:
        info = Task().get_msd_info(mdl)
        print(info)


def get_bundles(children=False):
    """
    gets all the bundles in the scene
    :param children: if True it returns children as a seperate list.
    :return:
    """
    bundles = []
    bundle_ref_children = []
    sel = pm.ls(type='transform')
    for obj in sel:
        if obj.hasAttr('BundlePath'):
            bundles.append(obj)
    if children:
        for b in bundles:
            children = pm.listRelatives(b, ad=True)
            for child in children:
                try:
                    ref = pm.referenceQuery(child, filename=True, wcn=True)
                    bundle_ref_children.append(ref)
                except RuntimeError:
                    print('%s is not a reference' % child)
        return bundles, bundle_ref_children
    else:
        return bundles


def get_meshes(ignore=None):
    meshes = []
    references = pm.listReferences(namespaces=True)
    for ref in references:
        if not pm.system.referenceQuery(ref[-1], isLoaded=True):
            print('removing unloaded reference {}'.format(ref))
            pm.system.FileReference(ref[-1]).remove()
        else:
            if ref[-1].path not in ignore:
                meshes.append(ref)
    return meshes


def export_abc(file_out, geo, command_line=False):
    sframe = int(pm.playbackOptions(query=True, animationStartTime=True))
    eframe = int(pm.playbackOptions(query=True, animationEndTime=True))
    if command_line:
        command = [r'C:\Program Files\Autodesk\Maya2017\bin\mayapy.exe',
                   r'C:\Users\tmikota\PycharmProjects\core_tools\src\tools\maya\bakeGEO.py',
                   str(pm.sceneName()), file_out, str(geo)]
        print('command line not yet implemented')
        # subprocess.Popen(command)
    else:
        command = 'AbcExport -j "-frameRange %s %s -step 0.5 -uvWrite -wholeFrameGeo -worldSpace -writeVisibility ' \
                  '-eulerFilter -writeUVSets -dataFormat ogawa -root %s -file %s"' % (sframe, eframe, geo, file_out)
        print(command)
        maya.mel.eval(command)


def copy_animation(from_object, to_object):
    copy_animated_attr(from_object, to_object, 'translateX')
    copy_animated_attr(from_object, to_object, 'translateY')
    copy_animated_attr(from_object, to_object, 'translateZ')
    copy_animated_attr(from_object, to_object, 'rotateX')
    copy_animated_attr(from_object, to_object, 'rotateY')
    copy_animated_attr(from_object, to_object, 'rotateZ')
    copy_animated_attr(from_object, to_object, 'scaleX')
    copy_animated_attr(from_object, to_object, 'scaleY')
    copy_animated_attr(from_object, to_object, 'scaleZ')


def copy_animated_attr(from_object, to_object, attr):
    if pm.copyKey(from_object, attribute=attr, option='curve'):
        pm.pasteKey(to_object, attribute=attr)
    else:
        aa = pm.getAttr('{}.{}'.format(from_object, attr))
        pm.setAttr('{}.{}'.format(to_object, attr), aa)
