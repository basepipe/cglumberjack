from .smart_task import SmartTask
from cgl.plugins.blender import alchemy as alc

class Task(SmartTask):

    def __init__(self, path_object=None):
        if not path_object:
            from cgl.plugins.blender.alchemy import scene_object
            self.path_object = scene_object()
            self.path_object.render_path = scene_object().copy(task = 'anim',
                                                               context = 'render',
                                                               ext = 'abc',
                                                               latest=True,
                                                               user = 'publish',
                                                               set_proper_filename=True).path_root
    def build(self):
        """
        1. Read layout for file
        2. Import Camera
        :return:
        """
        from cgl.plugins.blender.utils import create_shot_mask_info , rename_collection
        from cgl.plugins.blender.alchemy import scene_object

        rename_collection(scene_object())

        alc.import_task(task='lay', reference=True,latest = True)
        alc.import_task(task='cam')

        create_shot_mask_info()
        reset_lock_cursor()
        parent_rig_to_anim_group()

    def _import(self, filepath,reference):
        from cgl.plugins.blender.alchemy import import_file, scene_object
        print('animation file')
        print(self.path_object.path_root)
        rig = import_file(self.path_object.render_path)

        pass

def get_keyframes(obj, ends=False):
    import math
    '''
        returns list with first and last keyframe of the camera
    '''
    keyframes = []
    anim = obj.animation_data
    if anim is not None and anim.action is not None:
        for fcu in anim.action.fcurves:
            for keyframe in fcu.keyframe_points:
                x, y = keyframe.co
                if x not in keyframes:
                    keyframes.append((math.ceil(x)))

    if ends:
        if len(keyframes)>1:

            return (keyframes[0], keyframes[-1])
        else:

            print('no keyframes on camera')
            return(1,200)
    else:

        return keyframes

def move_keyframes(obj, offset):
    """

    :param obj: object to move animation
    :type obj: bpy.data.object
    :param offset: how many frames forwards or backwards to move
    :type offset: int
    """
    keyframes = []
    anim = obj.animation_data
    if anim is not None and anim.action is not None:
        for fcu in anim.action.fcurves:
            for keyframe in fcu.keyframe_points:
                x, y = keyframe.co
                keyframe.co = (x + offset, y)

def make_proxy(path_object,obj):
    import bpy
    rig_name = '{}_rig'.format(path_object.asset)
    objects = bpy.context.view_layer.objects
    objects.active =  obj
    bpy.ops.object.proxy_make(object=rig_name)
    return bpy.data.objects[rig_name]

def get_anim_group():
    from cgl.plugins.blender.alchemy import scene_object
    from cgl.plugins.blender.utils import create_object
    scn = scene_object()
    group = create_object('{}_{}:anim'.format(scn.seq, scn.shot))

    return group

def get_animation_mdl_groups():
    elements = get_rigs_in_scene(all=True)
    from ..utils import get_objects_in_hirarchy, get_object
    from ..msd import path_object_from_asset_name


    for obj in elements:
        # print(obj.name)
        if ':' not in obj.name:

            name = obj.name.split('_')[0]
        else:
            name = obj.name.split(':')[0]

        # print(asset.path_root)
        # print(asset.asset)
        asset = path_object_from_asset_name(name)

        mdl_group = get_objects_in_hirarchy(obj)
        for mdl in mdl_group:


            locator = get_object(mdl)
            new_name = '{}:'.format(asset.asset)
            old_name = '{}_'.format(asset.asset)

            locator.name = locator.name.replace(old_name, new_name)

        mdl_group = get_objects_in_hirarchy(obj)
    return mdl_group

def get_rigs_in_scene(scene=None, all = False):
    """
    takes in view layer and returns the rigs in that scene
    :param scene:
    :type scene: view_layer
    :return:
    :rtype:
    """
    import bpy
    from cgl.plugins.blender.utils import create_object
    if scene == None:
        scene = bpy.context

    scene_objects = scene.view_layer.objects

    rigs = []
    for object in scene_objects:
        if ':rig' in object.name and object.type == 'EMPTY':
            rigs.append(object)

    if all:
        anim_group = get_anim_group()
        for object in anim_group.children:
            rigs.append(object)
    return rigs

def export_rigs():
    """
    exports all the rigs in the scene
    :return:
    :rtype:
    """
    from cgl.plugins.blender.alchemy import export_selected, scene_object, selection

    selection(clear=True)

    for obj in get_rigs_in_scene():
        selection(object=obj)

    render_path = scene_object().copy(context = 'render', ext = 'abc')

    export_selected(render_path.path_root)
    print(render_path.path_root)
    print(get_rigs_in_scene())

def renanme_action():
    objects = bpy.context.selected_objects
    # selected_object = bpy.context.object
    for selected_object in objects:
        action = selected_object.animation_data.action
        if action:

            currentScene = lm.scene_object()

            newActionName = '_'.join([currentScene.filename_base, selected_object.name, currentScene.version])
            action.name = newActionName
            print(newActionName)

        else:
            lm.confirm_prompt(message='No action linked to object')


def parent_rig_to_anim_group():
    from cgl.plugins.blender.alchemy import scene_object
    from cgl.plugins.blender import utils

    scn = scene_object()
    rigs = get_rigs_in_scene()

    anim_group = get_anim_group()

    for rig in rigs:
        utils.parent_object(rig,anim_group)
        rig_proxy = utils.get_object('{}_proxy'.format(rig.name))
        if rig_proxy:
            utils.parent_object(rig_proxy,anim_group)
def reset_lock_cursor():
    import bpy

    for area in bpy.context.screen.areas:
        if area.type == 'VIEW_3D':
            for space in area.spaces:
                if space.type == 'VIEW_3D':
                    space.lock_cursor = False
