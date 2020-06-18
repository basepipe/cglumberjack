import os
import shutil


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
    if does_asset_exist(path):
        pass
    else:
        try:
            os.mkdir(path)
        except OSError:
            print "Error creating directory %s" % path
            return False
        else:
            print "Successfully created directory at %s" % path
            return path


def copy_new_asset(asset_name, filepath):
    """
    Function to copy new asset files to bridge assets folder
    :param asset_name: Name of new asset
    :param filepath: Filepath to folder with new asset files
    :return:
    """
    asset_dir = make_new_asset_dir(asset_name)
    if asset_dir:
        for file in os.listdir(filepath):
            if os.path.splitext(file)[1] == '.exr':
                shutil.copy(os.path.join(filepath, file), asset_dir)
        print "Successfully copied files to %s" % asset_dir
    else:
        print "Error: Asset '%s' already exists" % asset_name


if __name__ == "__main__":
    pass