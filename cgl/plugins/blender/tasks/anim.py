from .smart_task import SmartTask
from cgl.plugins.blender import alchemy as alc

class Task(SmartTask):

    def __init__(self, path_object=None):
        if not path_object:
            from cgl.plugins.blender.alchemy import scene_object
            self.path_object = scene_object()

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

    def _import(self, filepath):
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

    if ends :
        return (keyframes[0], keyframes[-1])
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
