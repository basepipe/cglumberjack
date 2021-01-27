import os
from cgl.core.path import PathObject
from cgl.apps.magic_browser.tasks.smart_task import SmartTask
from cgl.core.utils.general import load_json, save_json
import time
import re


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
        task = 'tex'
        assets = get_shots(company, project, scope='assets')
        for ass in assets:
            ass = ass.replace('\\', '/')
            if 'cgl_info' not in ass:
                pub_dir = ('{}/{}/publish'.format(ass, task))
                msd = PathObject(pub_dir).copy(latest=True, resolution='high', set_proper_filename=True,
                                               ext='json')
                # if not os.path.exists(msd.msd_path):
                tex_msd_dict = {}
                pub_path = os.path.dirname(msd.msd_path)
                s_file = glob.glob('{}/*.spp'.format(pub_path.replace('render', 'source')))
                if s_file:
                    src_file = s_file[0]
                tex_msd_dict['source_file'] = src_file
                tex_msd_dict['attrs'] = self.get_shading_dict(pub_path)
                print(msd.msd_path)
                save_json(msd.msd_path, tex_msd_dict)
                time.sleep(1)
                msd.update_project_msd()
                #else:
                 #   print('Found {}'.format(msd.msd_path))

    def get_shading_dict(self, tex_root):
        """
        Expects a Folder with the following structure:
        ../{resolution}/{material_group}/texture_file_{channel_name}.ext

        Produces a shading dictionary with the following structure:
        Material Group ("material_mtl")
            Channel Name ("BaseColor")
                Extension ("exr", "tx")
                    Texture Path (Relative)
        :param tex_root:
        :return:
        """
        udim_pattern = r"[0-9]{4}"
        ignore = ['cgl_info.json']
        ignore_ext = ['json']
        mtl_groups = os.listdir(tex_root)
        dict_ = {}
        for g in mtl_groups:
            if '.' not in g:
                dict_[g] = {}
                chann_dir = os.path.join(tex_root, g)
                if os.path.isdir(chann_dir):
                    for tex in os.listdir(chann_dir):
                        channel_name = tex.split("_")[-1].split('.')[0]
                        if channel_name not in dict_[g].keys():
                            dict_[g][channel_name] = {}
                        ext = os.path.splitext(tex)[-1].replace('.', '')
                        if ext not in ignore_ext:
                            if re.search(udim_pattern, tex):
                                new_t = re.sub(udim_pattern, '<UDIM>', tex)
                                tex = os.path.join(tex_root, g, new_t).replace('\\', '/')
                            dict_[g][channel_name][ext] = tex
        return dict_



if __name__ == '__main__':
    company = 'VFX'
    project = '02BTH_2021_Kish'
    Task().create_base_msd(company, project)