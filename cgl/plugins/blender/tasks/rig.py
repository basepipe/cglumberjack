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

        #model = alc.scene_object().copy(task='mdl', set_proper_filename=True).latest_version()
        print('hello we are building rig ')
        alc.import_task(task='mdl')
        assign_rig()



    def _import(self, filepath):
        pass



def get_rig(asset= None):
    import bpy
    from cgl.plugins.blender.utils import get_object
    if asset == None :
        asset = alc.scene_object().asset

    asset_name = '{}_rig'.format(asset)
    object = get_object(asset_name)
    return object


def assign_rig():
    import bpy
    from cgl.plugins.blender.tasks import mdl
    mdl_objects = mdl.get_mdl_objects(namespace='LORA')
    act = bpy.context.active_object
    rig = get_rig()

    for obj in mdl_objects:
        if obj != act:
            bpy.context.view_layer.objects.active = obj[0]

            if 'Armature' not in obj[0].modifiers:

                bpy.ops.object.modifier_add(type='ARMATURE')


            armature_modifier = obj[0].modifiers["Armature"]

            armature_modifier.object = rig
