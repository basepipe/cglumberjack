from .smart_task import SmartTask
from cgl.plugins.blender import alchemy as alc

class Task(SmartTask):

    def __init__(self, path_object=None):
        if not path_object:
            from cgl.plugins.blender.alchemy import scene_object
            self.path_object = scene_object()
            self.path_object.render_path = scene_object().copy(context = 'render', ext = 'abc')
    def build(self):
        """
        1. Read layout for file
        2. Import Camera
        :return:
        """
        from cgl.plugins.blender.utils import create_shot_mask_info , rename_collection
        from cgl.plugins.blender.alchemy import scene_object


        camfile = alc.scene_object().copy(task = 'cam')
        alc.import_task(file_path = camfile,  task='cam')
        alc.import_task(task='lay')

        rename_collection(scene_object())
        create_shot_mask_info()
        reset_lock_cursor()

    def _import(self, filepath):
        from cgl.plugins.blender.alchemy import import_file, scene_object
        import_file(self.path_object.render_path)
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

def get_rigs_in_scene(scene=None):
    """
    takes in view layer and returns the rigs in that scene
    :param scene:
    :type scene: view_layer
    :return:
    :rtype:
    """
    import bpy
    if scene == None:
        scene = bpy.context

    scene_objects = scene.view_layer.objects

    rigs = []
    for object in scene_objects:
        if ':rig' in object.name and object.type == 'EMPTY':
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






def reset_lock_cursor():
    import bpy

    for area in bpy.context.screen.areas:
        if area.type == 'VIEW_3D':
            for space in area.spaces:
                if space.type == 'VIEW_3D':
                    space.lock_cursor = False
