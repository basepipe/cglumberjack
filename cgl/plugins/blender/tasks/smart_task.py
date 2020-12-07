

class SmartTask(object):
    """
    This is a template for a "task" within the pipeline.  It covers common areas when dealing with digital assets
    specific to different tasks.
    """

    def __init__(self, path_object=None):
        """

        :param path_object: must be a "PathObject"
        """
        from cgl.plugins.maya.lumbermill import LumberObject, scene_object
        if not path_object:
            self.path_object = scene_object()
        else:
            self.path_object = path_object
        if not isinstance(path_object, LumberObject):
            print("{} is not instance LumberObject")
            return
        print(path_object.path_root)
        # check if it's a PathObject instance

    def build(self):
        """
        the tasks code associated with this task.
        :return:
        """
        pass

    def _import(self, file_path, reference=False, collection_name=None):
        """
        Imports the file into the scene - this function should be smart enough to handle various file types
        as well as
        :return:
        """
        if not file_path:
            file_path = self.path_object.path_root
        from cgl.plugins.blender.lumbermill import import_file
        import_file(filepath=file_path, collection_name=collection_name)
        return  file_path

    def import_latest(self, task=None, **kwargs):
        if not task:
            print('no task arrived')
            task = self.path_object.task
        new_obj = self.path_object.copy(task=task, context='render', user='publish',
                                        latest=True,
                                        set_proper_filename=True)
        import_obj = self._import(new_obj.path_root, collection_name=self.path_object.asset)
        print(new_obj.path)
        return import_obj

        pass

    def publish(self):
        """
        publishes specific to the task at hand. by default we just do what's in the lumbermill plugin,
        this allows us to customize at a more granular level if needed.
        :return:
        """
        from cgl.plugins.maya.lumbermill import publish
        publish()

