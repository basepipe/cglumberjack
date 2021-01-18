



def find_matching_files(file_path, dictionary):
    """
    creates a list of match
    :param file_path:
    :param dictionary:
    :return:
    """
    from cgl.core.path import remove_root
    ignore = ['.json', '.msd']
    if not self.single_asset_name:
        no_ext_path, ext = os.path.splitext(file_path)
        glob_pattern = '{}'.format(no_ext_path)
    else:
        directory = os.path.dirname(self.scene_object.copy(context='render').path_root)
        glob_pattern = '{}/{}.*'.format(directory, self.single_asset_name)
    print('\tlooking for {}'.format(glob_pattern))
    files = glob.glob(glob_pattern)
    for f in files:
        f = f.replace('\\', '/')
        _, ext = os.path.splitext(f)
        ext = ext.replace('.', '')
        dictionary[str(ext)] = remove_root(f)
    for key in dictionary:
        print('\t\t{}: {}'.format(key, dictionary[key]))
    return dictionary