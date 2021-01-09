from .smart_task import SmartTask
from cgl.plugins.SOFTWARE.alchemy import scene_object, import_file, import_task

TASK_NAME = os.path.basename(__file__).split('.py')[0]

"""
Instructions for Setting up a task.
1) get _import() to work for your specific software.
2) make any adjustments to "import_latest()" that you need to. 
(for example sometimes we use a glob rather than a specific file)
3) get the "build()" function to work
4) add any task specific code here for convenience.
5) Remove these instructions.
"""


class Task(SmartTask):

    def __init__(self, path_object=None):
        if not path_object:
            from cgl.plugins.maya.alchemy import scene_object
            self.path_object = scene_object()

    def build(self):
        """
        "Build Script" for this task.  This gathers all published data pertinent to this task and assembles it
        into the current scene. Ideally you'll just use the import_task() function from "alchemy".  These
        two lines for example would run the "import_latest()" functions from the 'lay' and 'cam' tasks.

        import_task(task='lay')
        import_task(task='cam')

        :return:
        """
        pass

    @staticmethod
    def _import(filepath):
        """
        imports "filepath" into the current scene. by default this pulls from the import_file method in the
        alchemy plugin file for this software.  You can change this however you need to on a per task basis though.
        :param filepath:
        :return:
        """
        import_file(filepath)

    def import_latest(self):
        """
        Imports the latest version of the current task.
        :return:
        """
        self._import(get_latest())


# TODO put a default ext here.
def get_latest(ext=''):
    """
    Convenience Function: returns the latest published version of the current task.
    :param ext: default extension for this task for imports.
    :return:
    """
    latest_obj = scene_object().copy(task=TASK_NAME, context='render',
                                     user='publish', latest=True, set_proper_filename=True, ext=ext)
    return latest_obj.path_root

