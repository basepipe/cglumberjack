from cgl.core.path import PathObject


class SmartTask(object):
    """
    This is a template for a "task" within the cookbook.  It covers common areas when dealing with digital assets
    specific to different tasks.
    """
    path_object = None

    def __init__(self, path_object=None):
        """

        :param path_object: must be a "PathObject"
        """
        from cgl.plugins.maya.alchemy import scene_object
        if not path_object:
            self.path_object = scene_object()
        else:
            self.path_object = path_object
        if not isinstance(path_object, PathObject):
            print("{} is not instance LumberObject")
            return
        # check if it's a PathObject instance

    def build(self):
        """
        the tasks code associated with this task.
        :return:
        """
        from cgl.ui.widgets.dialog import InputDialog
        message = 'No build() Function Defined for Task() {}\n' \
                  'Edit or add it in the Production Cookbook:\n\n' \
                  'Software: maya\n' \
                  'Menu Type: Smart Tasks\n' \
                  'Task: {} or\n' \
                  'Create new SmartTask: {}'.format(self.path_object.task,
                                                    self.path_object.task, self.path_object.task)
        dialog = InputDialog(title='build() function Not Found', message=message)
        dialog.exec_()

    def _import(self, file_path, reference=False):
        """
        Imports the file into the scene - this function should be smart enough to handle various file types
        as well as
        :return:
        """
        if not file_path:
            file_path = self.path_object.path_root
        from cgl.plugins.maya.alchemy import import_file, reference_file
        if reference:
            return reference_file(filepath=file_path)
        else:
            return import_file(filepath=file_path)

    def import_latest(self, task=None, reference=False, **kwargs):
        if not task:
            task = self.path_object.task
        new_obj = self.path_object.copy(task=task, context='render', user='publish',
                                        latest=True,
                                        set_proper_filename=True)
        import_obj = self._import(new_obj.path_root, reference=reference)
        return import_obj

    def publish(self):
        """
        publishes specific to the task at hand. by default we just do what's in the magic_browser plugin,
        this allows us to customize at a more granular level if needed.
        :return:
        """
        from cgl.plugins.maya.alchemy import publish
        publish()

