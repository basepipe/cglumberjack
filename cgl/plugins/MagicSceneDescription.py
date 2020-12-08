import os
import copy
import glob
from cgl.core.config import app_config
from cgl.core.utils.read_write import load_json, save_json

CONFIG = app_config()


class MagicSceneDescription(object):
    scene_object = None
    path = None
    scene_file = None
    output_msd = None
    path_object = None
    data = {}
    software = None
    ad_class = None
    lgt_class = None

    def __init__(self):
        """
        This is the base code for the Production Alchemy "Mystic Scene Description" file or 'msd'.
        Essentially this is a template for setting up different 3d packages in the .msd universe.
        Follow these instructions:
        1) Copy this file into the /plugins/SOFTWARE/ folder and make sure the new one  is called msd.py


        :param software:
        :param type_:
        :param scene_description_path:
        """
        self.create_msd()

    def load_description_classes(self):
        pass

    def create_msd(self):
        self.load_description_classes()
        self.set_scene_file()
        self.set_path_object_details()
        self.set_scene_data()

    def add_asset(self, asset_description):
        self.data[asset_description.asset_name] = copy.copy(asset_description.data)

    def set_scene_file(self):
        """
        sets the scene file as path_root for the msd
        :return:
        """
        # from cgl.plugins.SOFTWARE.lumbermill import get_scene_file
        # self.scene_file = get_scene_file()
        # use the above code to set this
        pass

    def set_path_object_details(self):
        self.output_msd = self.path_object.copy(context='render', set_proper_filename=True, ext='msd').path_root
        self.data['name'] = self.path_object.shot
        self.data['source_path'] = self.path_object.path
        self.data['task'] = self.path_object.task

    def set_scene_data(self):
        """
        sets self.data with all information about the scene, this is
        :return:
        """
        bundles, children = self.get_bundles(children=True)
        if bundles:
            for b in bundles:
                b_desc = self.ad_class(b, asset_type='bndl')
                self.add_asset(b_desc)
        assets = self.get_assets(ignore=[])
        if assets:
            for a in assets:
                a_desc = self.ad_class(mesh_object=a)
                self.add_asset(a_desc)

    def get_lights(self):
        """
        Gets the lights in the scene.  Should be set on a per application basis.
        :return:
        """
        pass

    @staticmethod
    def get_assets(ignore=[]):
        """
        Gets the assets in the scene
        :param ignore:
        :return:
        """
        # This must be customized for each application
        pass

    def export(self):
        print('exporting msd to: {}'.format(self.output_msd))
        save_json(self.output_msd, self.data)
        pass

    @staticmethod
    def get_bundles(children=False):
        """
        gets all the bundles in the scene
        :param children: if True it returns children as a seperate list.
        :return:
        """
        # this must be customized for each application
        pass

