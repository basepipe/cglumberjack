import os
import time
import glob
from cgl.core.path import PathObject, get_folder_size
from cgl.core.utils.general import save_json, load_json


def get_cgl_info_size(folder_path, source=True, render=True, return_type='best'):
    """
    gets the cgl_info for the specified folder, if it doesn't exist it creates it.
    :param folder_path:
    :return:
    """
    source_size = 0
    render_size = 0
    if 'cgl_info.json' not in folder_path:
        cgl_info_file = os.path.join(folder_path, 'cgl_info.json').replace('\\', '/')
        if os.path.exists(cgl_info_file):
            if '/source/' in cgl_info_file:
                source_file = cgl_info_file
                render_file = cgl_info_file.replace('/source/', '/render/')
            else:
                render_file = cgl_info_file
                source_file = cgl_info_file.replace('/render/', '/source/')
            if source:
                try:
                    source_size = load_json(source_file)[os.path.dirname(source_file)]['total_bytes']
                    source_size = float(source_size)
                except KeyError:
                    pass
            if render:
                try:
                    cgl_info = load_json(render_file)
                    if cgl_info:
                        render_size = cgl_info[os.path.dirname(render_file)]['total_bytes']
                        render_size = float(render_size)
                    else:
                        render_size = 0
                except KeyError:
                    pass

            size = source_size+render_size
            mb = "{:.2f}".format(float(size/1048576))
            gb = "{:.2f}".format(float(size/1073741824))
            if return_type == 'best':
                if len(mb.split('.')[0]) > len(gb.split('.')[0]):
                    return '%s Gb' % gb
                else:
                    return '%s Mb' % mb
            elif return_type == 'mb':
                return mb
            elif return_type == 'gb':
                return gb
            elif return_type == 'bytes':
                return size
        else:
            return None

    else:
        return None


def create_cgl_info(file_path, last_attr, dirs, files, force=False):
    create = False
    ignore = ['cgl_info.json']
    file_path = file_path.replace('\\', '/')
    json_file = os.path.join(file_path, 'cgl_info.json').replace('\\', '/')
    if not os.path.exists(json_file):
        create = True
    if force:
        create = True
    if create:
        print('Calculating: ', json_file)
        parent, this = os.path.split(file_path)
        parent = os.path.join(parent, 'cgl_info.json').replace('\\', '/')
        folder_info = {}
        for each in ignore:
            if each in files:
                files.remove(each)
        size = get_folder_size(file_path)
        mb = "{:.2f}".format(float(size/1048576))
        gb = "{:.2f}".format(float(size/1073741824))
        folder_info[file_path] = {'total_bytes': size,
                                  'total_mb': mb,
                                  'total_gb': gb,
                                  'sync_status': '',
                                  'last_calculated': time.time(),
                                  'parent': parent,
                                  'files': files,
                                  'folder_type': last_attr,
                                  'children': {}
                                  }
        for d in dirs:
            folder_info[file_path]['children'][d] = {'syncing': ''}

        save_json(json_file, folder_info)


def add_size_to_parents():
    pass


def get_cgl_info_files(path_object, scope='assets', seq='*', shot='*', task='*', user='*', version='*', resolution='*'):
    # Z: / Projects / VFX / source / magLabFriday / assets / Prop / Bucket / mdl / tmikota / 000.001 / high / Prop_Bucket_mdl.mb
    path_object.set_attr(scope='assets')
    path_object.set_attr(seq=seq)
    path_object.set_attr(shot=shot)
    path_object.set_attr(task=task)
    path_object.set_attr(user=user)
    path_object.set_attr(version=version)
    path_object.set_attr(resolution=resolution)
    path_object.set_attr(filename='cgl_info.json')
    cgl_info_files = glob.glob(path_object.path_root)
    for each in cgl_info_files:
        print(each)


def build_folder_info(root_folder, force=False):
    # Goes through and builds cgl_info files for everything in the root folder
    for root, dirs, files in os.walk(root_folder):
        try:
            temp_object = PathObject(root)
            last_attr = temp_object.get_last_attr()
            create_cgl_info(root, last_attr, dirs, files, force=force)
        except ValueError:
            # TODO - need to add anything that falls into this to some kind of "not in cookbook"
            #  list of stuff to be deleted.
            last_attr = ''
            create_cgl_info(root, last_attr, dirs, files, force=force)


def create_all_cgl_info_files(company, project, source=True, render=True, force=False):
    start_time = time.time()
    if source:
        d = {"company": company, "project": project, 'context': 'source'}
        path_object = PathObject(d)
        build_folder_info(path_object.path_root, force=force)
    if render:
        d2 = {"company": company, "project": project, 'context': 'render'}
        path_object2 = PathObject(d2)
        build_folder_info(path_object2.path_root, force=force)
    end_time = time.time()-start_time
    print('print(finished processing in %s minutes' % "{:.2f}".format(end_time/60))


def create_full_project_cgl_info(company, project, branch=None):
    start_time = time.time()
    # source
    d = {"company": company, "project": project, "context": 'source', 'branch': branch}
    path_object = PathObject(d)
    source_folder = path_object.path_root
    if branch:
        if branch not in source_folder:
            source_folder = '{}/{}'.format(source_folder, branch)
    render_folder = source_folder.replace('/source/', '/render/')
    build_folder_info(source_folder, force=True)
    build_folder_info(render_folder, force=True)
    end_time = time.time()-start_time
    print('print(finished processing in %s minutes' % "{:.2f}".format(end_time/60))


if __name__ == "__main__":
    create_all_cgl_info_files('loneCoconut', 'ILUCIA', force=True)
    # create_all_cgl_info_files('VFX', '16BTH_2020_Arena', source=False)
    # print(get_cgl_info_size(r'Z:/Projects/VFX/source/16BTH_2020_Arena/assets/Vehicle', source=True, render=False))


