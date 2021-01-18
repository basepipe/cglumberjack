

class SmartTask(object):
    """
    This is a template for a "task" within the cookbook.  It covers common areas when dealing with digital assets
    specific to different tasks.
    """

    def __init__(self, path_object=None):
        """

        :param path_object: must be a "PathObject"
        """
        from cgl.plugins.maya.lumbermill import scene_object
        from cgl.core.path import PathObject
        if not path_object:
            self.path_object = scene_object()
        else:
            self.path_object = path_object
        if not isinstance(path_object, PathObject):
            print("{} is not instance PathObject")
            return
        print(path_object.path_root)
        # check if it's a PathObject instance

    def build(self):
        """
        the tasks code associated with this task.
        :return:
        """
        pass

    def _import(self, file_path, reference=False,**kwargs):
        """
        Imports the file into the scene - this function should be smart enough to handle various file types
        as well as
        :return:
        """
        if not file_path:
            file_path = self.path_object.path_root
        from cgl.plugins.blender.alchemy import import_file, reference_file,PathObject

        path_object = PathObject(file_path)
        if reference:
            return reference_file(filepath=file_path,namespace=path_object.asset)
        else:
            return import_file(filepath=file_path,namespace=path_object.asset)

    def import_latest(self,task=None, reference=False, **kwargs):
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
        from cgl.plugins.blender.alchemy import publish
        publish()

    def get_msd_info(self, task_name):
        """
        creates the msd dictionary for the task being called.
        :param task_name:
        :return:
        """
        pass

    def export_msd(self, task_name, selected=None):
        """

        """
        if not selected:
            print(self.path_object.msd_path)
            self.path_object.save_msd(self.get_msd_info(task_name))
            # update the project.msd
            # update the project_test.msd

    def render(self):
        """

        :return:
        """
        pass

