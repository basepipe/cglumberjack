import os
import time
from cgl.core.path import PathObject
from cgl.core.utils.general import save_json, load_json


class SmartTask(object):
    """
    This is a template for a "task" within the cookbook.  It covers common areas when dealing with digital assets
    specific to different tasks.
    """

    def __init__(self, path_object=None):
        """

        :param path_object: must be a "PathObject"
        """
        if not isinstance(path_object, PathObject):
            print("{} is not instance PathObject")
            return
        self.path_object = path_object

    def build(self):
        """
        the tasks code associated with this task.
        :return:
        """
        print('we have not yet defined a system "build()" function')

    def _import(self, file_path, reference=False):
        """
        used to bring a file_path into the current folder of the current task.
        :param file_path:
        :param reference:
        :return:
        """
        pass

    def import_latest(self, task=None, reference=False, **kwargs):
        pass

    def publish(self):
        """
        publishes specific to the task at hand. by default we just do what's in the magic_browser plugin,
        this allows us to customize at a more granular level if needed.
        :return:
        """
        pass

    def create_msd(self):
        """
        By default this creates a basic .msd file based off what is in the source/render folders of the path_object.
        :return:
        """
        default_data = {}
        default_data['source_files'] = self.get_source_files()
        default_data['render_files'] = self.get_render_files()
        default_data['attrs'] = {}
        default_data['transforms'] = {}
        print("Saving MSD: {}".format(self.path_object.msd_path))
        save_json(self.path_object.msd_path, default_data)
        time.sleep(1)
        self.path_object.update_project_msd()

    def get_source_files(self):
        d = {}
        ignore = ['cgl.info']
        if self.path_object.filename:
            if self.path_object.context != 'source':
                path_object = self.path_object.copy(context='source')
                dir_ = os.path.dirname(path_object.path_root)
            else:
                dir_ = os.path.dirname(self.path_object.path_root)
            for file in os.listdir(dir_):
                if file not in ignore:
                    _, ext = os.path.splitext(file)
                    d[ext.replace('.', '')] = PathObject(os.path.join(dir_, file)).path
            return d

    def get_render_files(self):
        d = {}
        ignore = ['cgl.info']
        if self.path_object.filename:
            if self.path_object.context != 'render':
                path_object = self.path_object.copy(context='render')
                dir_ = os.path.dirname(path_object.path_root)
            else:
                dir_ = os.path.dirname(self.path_object.path_root)
            for file in os.listdir(dir_):
                if file not in ignore:
                    _, ext = os.path.splitext(file)
                    d[ext.replace('.', '')] = PathObject(os.path.join(dir_, file)).path
            return d

    def check_published_msds(self):
        """
        Checks all published msds for the task and creates one if it is missing.
        This should be defined for each task.
        :return:
        """
        pass



if __name__ == '__main__':
    import glob
    from cgl.apps.magic_browser.project_optimize import get_shots
    company = 'VFX'
    project = '02BTH_2021_Kish'
    task = 'mdl'
    assets = get_shots(company, project, scope='assets')
    msd_list = []
    for ass in assets:
        ass = ass.replace('\\', '/')
        if 'cgl_info' not in ass:
            pub_dir = ('{}/{}/publish'.format(ass, task))
            msd = PathObject(pub_dir).copy(latest=True, resolution='high', set_proper_filename=True,
                                           ext='msd')
            if not os.path.exists(msd.path_root):
                this = SmartTask(path_object=msd)
                this.create_msd()
            else:
                # os.remove(msd.msd_path)
                print('skipping {}'.format(msd.msd_path))
    # path_object = PathObject(path_)
    #print(path_object.path_root)
    #this = SmartTask(path_object=path_object)
    #this.create_msd()
