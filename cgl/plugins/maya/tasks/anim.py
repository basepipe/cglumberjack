from .smart_task import SmartTask
import cgl.plugins.maya.lumbermill as lm
import cgl.plugins.maya.msd as msd
reload(msd)


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
        lm.import_task(task='lay')
        lm.import_task(task='cam')

    def _import(self, filepath):
        if filepath.endswith('.msd'):
            msd.load_msd(this_obj.path_root)

    def import_latest(self):
        """
        imports everything from latest animation publish as described in the .msd file.
        :return:
        """
        this_obj = lm.scene_object().copy(task='anim', context='render', user='publish', latest=True,
                                          set_proper_filename=True, ext='msd')
        self._import(this_obj.path_root)
