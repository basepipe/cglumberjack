import os
from cgl.core.path import PathObject
from cgl.apps.magic_browser.tasks.smart_task import SmartTask
from cgl.core.utils.general import load_json, save_json
import time

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
        task = 'bndl'
        assets = get_shots(company, project, scope='assets')
        for ass in assets:
            ass = ass.replace('\\', '/')
            if 'cgl_info' not in ass:
                pub_dir = ('{}/{}/publish'.format(ass, task))
                msd = PathObject(pub_dir).copy(latest=True, resolution='high', set_proper_filename=True,
                                               ext='json')
                if not os.path.exists(msd.msd_path):
                    if os.path.exists(msd.path_root):
                        print('Found .json: {}'.format(msd.path_root))
                        json_dict = load_json(msd.path_root)
                        temp_dict = {}
                        for key in json_dict:
                            asset_name = json_dict[key]['name']
                            splitted = json_dict[key]['source_path'].split('/')
                            task = json_dict[key]['task']
                            scope = splitted[3]
                            category = splitted[4]
                            msd_path = load_json(msd.project_msd_path)[scope][category][asset_name][task]
                            temp_dict[key] = {}
                            temp_dict[key]['name'] = asset_name
                            temp_dict[key]['category'] = category
                            temp_dict[key]['msd_path'] = msd_path
                            temp_dict[key]['task'] = task
                            temp_dict[key]['transform'] = {'matrix': json_dict[key]['transform']}
                        save_json(msd.msd_path, temp_dict)
                        msd.update_project_msd()
                else:
                    print('Found {}'.format(msd.msd_path))
                    # os.remove(msd.msd_path)

                    pass
                    """

                    # print('skipping {}'.format(msd.msd_path))
                    """


if __name__ == '__main__':
    company = 'VFX'
    project = '02BTH_2021_Kish'
    Task().create_base_msd(company, project)