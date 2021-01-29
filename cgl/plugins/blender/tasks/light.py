from .smart_task import SmartTask
from cgl.plugins.blender import alchemy as alc
from .anim import get_rigs_in_scene
from ..msd import path_object_from_asset_name


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
        from cgl.plugins.blender.utils import create_shot_mask_info, rename_collection,create_object
        from cgl.plugins.blender.alchemy import scene_object, import_task

        rename_collection(scene_object())

        bndl_group = create_object('{}_{}:lay'.format(scene_object().seq,scene_object().shot))
        default_list = ['FG','BG','MAIN','CAMERAS']

        for layer in default_list :
            create_object('{}_{}:{}'.format(scene_object().seq,scene_object().shot,layer), parent=bndl_group)



        import_task(task='lay', import_rigs=False, reference=False, latest=True)
        import_task(task='cam')
        import_task(task='anim')

        rigs = get_rigs_in_scene(all=True)

        for rig in rigs:
            name = rig.name.split('_')[0]
            path = path_object_from_asset_name(asset_name=name, task='shd').copy(latest=True)

            alc.import_task(task='shd', file_path=path.path_root)

        create_shot_mask_info()

    def _import(self, filepath):
        pass
