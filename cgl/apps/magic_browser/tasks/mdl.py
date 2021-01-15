import os
from cgl.core.path import PathObject
from cgl.apps.magic_browser.tasks.smart_task import SmartTask


class Task(SmartTask):
    """
    This is a template for a "task" within the cookbook.  It covers common areas when dealing with digital assets
    specific to different tasks.
    """

    def create_base_msd(self, company, project):
        """
        Checks all published msds for the task and creates one if it is missing.
        This should be defined for each task.
        :return:
        """
        import glob
        from cgl.apps.magic_browser.project_optimize import get_shots
        task = 'mdl'
        assets = get_shots(company, project, scope='assets')
        for ass in assets:
            ass = ass.replace('\\', '/')
            if 'cgl_info' not in ass:
                pub_dir = ('{}/{}/publish'.format(ass, task))
                msd = PathObject(pub_dir).copy(latest=True, resolution='high', set_proper_filename=True,
                                               ext='msd')
                if not os.path.exists(msd.path_root):
                    this = Task(path_object=msd)
                    this.create_msd()
                else:
                    #@os.remove(msd.msd_path)
                    print('skipping {}'.format(msd.msd_path))


if __name__ == '__main__':
    company = 'fsu_animation'
    project = '02BTH_2021_Kish'
    Task().create_base_msd(company, project)
