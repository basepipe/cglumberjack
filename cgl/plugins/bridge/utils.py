import os
import shutil
import random
import json
from cgl.core.config import app_config

CONFIG = app_config()
ROOT = CONFIG['paths']['code_root']


def does_asset_exist(asset_name):
    """
    Checks if asset with asset_name exists in bridge files
    :param asset_name: Name of asset to check
    :return: True if asset exists, False if asset does not exist
    """
    path = os.path.join(get_bridge_assets_path(), asset_name)
    if os.path.isdir(path):
        return True
    else:
        return False


def get_bridge_assets_path():
    """
    Gets the path to the top directory for new assets
    :return:
    """
    return os.path.join(os.path.expanduser('~'), 'Documents', 'Megascans Library', 'Custom', '3d')


def make_new_asset_dir(asset_name):
    """
    Creates new folder for asset in Quixel Bridge files
    :param asset_name: Name of new asset
    :return:
    """
    path = os.path.join(get_bridge_assets_path(), asset_name)
    try:
        os.mkdir(path)
    except OSError:
        print "Error creating directory %s" % path
        return False
    else:
        print "Successfully created directory at %s" % path
        return path


def copy_new_asset(asset_dir, filepath):
    """
    Function to copy new asset files to bridge assets folder
    :param asset_name: Name of new asset
    :param filepath: Filepath of folder with new asset files
    :return:
    """
    for file in os.listdir(filepath):
        if os.path.splitext(file)[1] == '.exr':
            shutil.copy(os.path.join(filepath, file), asset_dir)
    print "Successfully copied files to %s" % asset_dir


def copy_json_template(filepath):
    """
    Copies and renames assetData template to filepath location
    :param filepath: Location to be copied to
    :return:
    """
    filepath = os.path.join(filepath, 'assetData.json')
    json_path = os.path.join(ROOT, 'cgl', 'plugins', 'bridge', 'assetData_template.json')
    shutil.copy(json_path, filepath)


def generate_new_id():
    """
    Function to generate custom id for new asset
    :return: String containing new asset's id
    """
    int_1 = random.randint(10000000, 99999999)
    int_2 = random.randint(1000, 9999)
    int_3 = random.randint(1000, 9999)
    int_4 = random.randint(1000, 9999)
    int_5 = random.randint(100000000000, 999999999999)
    id = "%d-%d-%d-%d-%d" % (int_1, int_2, int_3, int_4, int_5)
    return id


def edit_json(asset_name, json_path):
    """
    Edits the assetData.json file for the new asset
    :param asset_name: Name of the new asset
    :param json_path: Path to assetData.json file
    :return:
    """
    with open(json_path) as json_file:
        asset_dict = json.load(json_file)
        new_id = generate_new_id()
        asset_dict['asset'] = new_id
        asset_dict['id'] = new_id
        asset_dict['name'] = asset_name
        search_str = "%s %s 3d" % (asset_name, new_id)
        asset_dict['searchStr'] = search_str
        asset_dict['path'] = os.path.join(get_bridge_assets_path(), asset_name)
        asset_dict['models'][0]['name'] = "%s_LOD0" % asset_name
        asset_dict['models'][0]['uri'] = "%s_LOD0.obj" % asset_name
        for entry in asset_dict['maps']:
             entry['uri'] = "%s_2K_%s.exr" % (asset_name, entry['name'].lower())
        asset_dict['lodList'][0]['name'] = "%s_LOD0" % asset_name
        asset_dict['lodList'][0]['uri'] = "%s_LOD0.obj" % asset_name

    with open(json_path, 'w') as outfile:
        json.dump(asset_dict, outfile, indent=4, sort_keys=True)


# def ingest_new_asset(asset_name, src_path):
#     """
#     Function to create new asset in Quixel Bridge
#     :param asset_name: Name of the new asset
#     :param src_path: Filepath to folder containing new asset's files
#     :return:
#     """
#     if does_asset_exist(asset_name):
#         print "Error: %s already exists" % asset_name
#     else:
#         new_dir = make_new_asset_dir(asset_name)
#         if new_dir:
#             copy_new_asset(new_dir, src_path)
#             copy_json_template(new_dir)
#             json_file = os.path.join(new_dir, 'assetData.json')
#             edit_json(asset_name, json_file)
#         else:
#             print "Exiting"
#             pass


if __name__ == "__main__":
    pass