import xml.etree.ElementTree as ElemTree
import getpass
import os
import subprocess
import requests
import json
import datetime
import time
import cgl.plugins.google.sheets as sheets
from cgl.core.utils.general import cgl_execute, launch_lumber_watch
from cgl.core.utils.read_write import load_json, save_json
from cgl.core.path import PathObject

URL = 'http://localhost:8384/rest'



def setup_server(clean=False):
    """
    sets up a machine as a syncing server for a studio.  This is the machine that will add remote workstations as
    collaborators, in a studio this must be connected to main storage server, for smaller projects this must be set up
    on the machine with the main storage for the project.  all files from remote machines will come back to this on
    publish.
    :param clean: wipe the server as part of the setup process.
    :return:
    """
    from cgl.core.config.config import ProjectConfig
    wipe_globals()
    user_globals = ProjectConfig().user_config_file
    set_machine_type('server')
    # cgl_tools_folder = os.path.dirname(ProjectConfig().project_config_file)

    sheet_obj = get_sheet()
    add_device_info_to_sheet(sheet_obj, server='true')
    add_all_devices_to_config(sheet_obj)
    # folder_id = r'[root]\_config\cgl_tools'
    # folder_id = r'[root]\master\config\master'
    # add_folder_to_config(folder_id, cgl_tools_folder, type_='sendonly')
    share_folders_to_devices()  # only if you're setting up main folders
    launch_syncthing()


def set_machine_type(m_type=""):
    from cgl.core.config.config import ProjectConfig
    """
    sets the machine type for the current machine
    a value of "" is used when a machine is using magic_browser but not syncthing.  This would be typical of a networked
    machine at the studio.
    :param m_type: valid types: "", "remote workstation", "server"
    :return:
    """
    user_globals = ProjectConfig().user_config
    user_globals['sync_thing_machine_type'] = m_type
    save_json(ProjectConfig().user_config_file, user_globals)


def clear_sync_thing_user_globals():
    from cgl.core.config.config import user_config, get_user_config_file
    user_globals = user_config()
    user_globals['sync_thing_config_modified'] = ""
    user_globals['sync_thing_machine_type'] = ""
    save_json(get_user_config_file(), user_globals)


def get_syncthing_state():
    """
    Returns syncthing state.  On, Off, Paused, Syncing
    :return:
    """
    pass


def setup_workstation():
    """
    sets up local workstation to talk to the studio side server.
    :param company:
    :param sheet_name:
    :return:
    """
    wipe_globals()
    from cgl.core.config.config import ProjectConfig, get_sync_config_file
    sync_config = load_json(get_sync_config_file())
    set_machine_type("remote workstation")
    # kill_syncthing()
    print(1, get_my_device_info())
    device_info = get_my_device_info()
    print('Setting Up Workstation for Syncing')
    print(sync_config)
    company = sync_config['sync']['syncthing']['aws_company_name']
    sheet_name = sync_config['sync']['syncthing']['sheets_name']

    sheet_obj = get_sheet()
    add_device_info_to_sheet(sheet_obj)
    add_all_devices_to_config(sheet_obj)
    # add_folder_to_config(folder_id, folder_path, type_='recieveonly')
    from cgl.plugins.aws.cgl_sqs.utils import machine_added_message
    machine_added_message(device_id=device_info['id'],
                          device_name=device_info['name'],
                          message='%s added machine %s' % ('user', device_info['name']))
    launch_lumber_watch(new_window=True)



def fix_folder_paths():
    kill_syncthing()
    config_path = get_config_path()
    tree = ElemTree.parse(config_path)
    root = tree.getroot()
    for child in root:
        if child.tag == 'folder':
            id_ = child.get('id')
            cgl_folder = get_folder_from_id(id_)
            xml_folder = child.get('path')
            if xml_folder != cgl_folder:
                child.set('path', cgl_folder)
                print('Changing path to %s' % cgl_folder)
            else:
                print('Folder Passes')
    tree.write(config_path)
    launch_syncthing()


def process_pending_folders(folder_type='sendreceive'):
    # receiveonly, sendonly, sendreceive
    config_path = get_config_path()
    tree = ElemTree.parse(config_path)
    root = tree.getroot()
    write = False
    for child in root:
        if child.tag == 'device':
            device_id = child.get('id')
            for c in child:
                if c.tag == 'pendingFolder':
                    id_ = c.get('id')
                    print('found pending folder: %s' % id_)
                    local_folder = get_folder_from_id(id_)
                    print('local folder is {}'.format(local_folder))
                    if local_folder:
                        if not os.path.exists(local_folder):
                            print('Creating Local Folder for Syncing: %s' % local_folder)
                            os.makedirs(local_folder)
                        c.set('path', local_folder)
                        # need a device list here for the add folder to config part to work.
                        device_list = [device_id]
                        print(local_folder)
                        local_path_object = PathObject(local_folder)
                        print(local_path_object.path_root)
                        print(local_path_object.scope)
                        print(local_path_object.asset)
                        new_node = None
                        write = True
                        folder_node = folder_id_exists(id_, tree=tree)
                        if folder_node is not None:
                            new_node = folder_node
                        else:
                            print('id_, adding %s to config' % id_)
                            new_node = ElemTree.SubElement(root, 'folder')
                            new_node.set('id', id_)
                            new_node.set('path', local_folder)
                            new_node.set('type', folder_type)
                            new_node.set('rescanIntervalS', '3600')
                            new_node.set('fsWatcherEnabled', "True")
                            new_node.set('fsWatcherDelayS', "10")
                            new_node.set('ignorePerms', "false")
                            new_node.set('autoNormalize', "true")
                            write = True
                        if device_list:
                            for id_ in device_list:
                                print('adding device %s to folder %s' % (id_, local_folder))
                                device_node = ElemTree.SubElement(new_node, 'device')
                                device_node.set('id', id_)
                        child.remove(c)
                    else:
                        print('skipping non-cgl folders')
    if write:
        tree.write(config_path)
        process_pending_folders(folder_type='sendreceive')
    else:
        print('\tNo Pending Folders Found')
        return True


def process_pending_devices():
    # parse the xml
    config_path = get_config_path()
    tree = ElemTree.parse(config_path)
    root = tree.getroot()
    write = False
    folders_dict = {}
    devices = False
    for child in root:
        if child.tag == 'pendingDevice':
            if child.get('id') != get_my_device_info()['id']:
                print("Found Pending Device: Checking to see if it's on the approved list.")
                add_device_to_config(child.get('id'), child.get('name'), remove=True)
                devices = True
    if devices:
        print('\tNo Pending Devices Found')



def process_folder_naming(kill=False, folder_type='sendreceive'):
    """
    remaps folders to local root.
    :return:
    """
    config_path = get_config_path()
    tree = ElemTree.parse(config_path)
    root = tree.getroot()
    write = False
    folders_dict = {}
    for child in root:
        if child.tag == 'folder':
            if ' ' in child.get('path'):
                local_folder = get_folder_from_id(child.get('id'))
                p_obj = PathObject(local_folder)
                label = ''
                if p_obj.scope == 'assets':
                    label = '%s-%s-%s (%s)' % (p_obj.asset, p_obj.task, p_obj.version, p_obj.context)
                elif p_obj.scope == 'shots':
                    label = '%s_%s-%s-%s (%s)' % (p_obj.seq, p_obj.shot, p_obj.task, p_obj.version, p_obj.context)
                print('changing %s to magic_browser pathing: %s' % (child.get('id'), local_folder))
                if not os.path.exists(local_folder):
                    print('Creating Local Folder for Syncing: %s' % local_folder)
                    os.makedirs(local_folder)
                # might need to create the folders if they don't exist, just to be sure.
                child.set('path', local_folder)
                child.set('type', folder_type)
                if label:
                    child.set('label', label)
                write = True
            if child.get('ID') == 'default':
                print('Removing "default" folder from syncthing registry')
                root.remove(child)
                write = True
    if write:
        tree.write(config_path)
    else:
        print('\tNo Folder Naming Issues Found')


def process_st_config(folder_type='sendreceive'):
    kill_syncthing()
    print('Processing syncthing config')
    process_pending_devices()
    process_pending_folders(folder_type=folder_type)
    process_folder_naming()
    launch_syncthing()


def get_folder_from_id(folder_id):
    from cgl.core.config.config import ProjectConfig
    user_globals = ProjectConfig().user_config
    try:
        variable, the_rest = folder_id.split(']')
        variable = variable.replace('[', '')

        value = user_globals['paths'][variable]
        local_path = '%s%s' % (value, the_rest)
        return local_path
    except ValueError:
        print('Skipping %s, it is not a magic_browser share' % folder_id)
        return None


def get_syncthing_folders():
    """
    creates a dictionary of {folder_id: path} for all the folders in syncthing.
    :return: Dictionary of folder ID's mapped to folder paths
    """
    config_path = get_config_path()
    tree = ElemTree.parse(config_path)
    root = tree.getroot()
    folders_dict = {}

    for child in root:
        if child.tag == 'folder':
            folders_dict[child.get('id')] = child.get('path')

    return folders_dict


def edit_syncthing_folder(folder_id, new_local_path):
    """
    Changes the path variable of the specified folder into the new path
    :param folder_id: ID of the folder to be changed
    :param new_local_path: New path value for folder
    :return:
    """
    config_path = get_config_path()
    tree = ElemTree.parse(config_path)
    root = tree.getroot()

    for child in root:
        if child.tag == 'folder' and child.get('id') == folder_id:
            child.set('path', new_local_path)

    tree.write(config_path)


def folder_id_exists(folder_id, folder_path='', tree=None):
    if not tree:
        config_path = get_config_path()
        tree = ElemTree.parse(config_path)
    root = tree.getroot()
    child = None

    for child in root:
        if child.tag == 'folder':
            if folder_id == child.get('id') or folder_path == child.get('path'):
                return child
    return None


def get_sheet():
    """
    Gets the sheet object for a company
    :param company: Company name in the s3 database
    :param sheet_name: Name of the google sheet being accessed
    :return: Sheet object
    """
    from cgl.core.config.config import get_sync_config_file
    globals_ = load_json(get_sync_config_file())
    client_file = globals_['sync']['syncthing']['sheets_config_path']
    name_ = globals_['sync']['syncthing']['sheets_name'].split('_SYNC_THING')[0]
    print('Syncing with %s' % name_)
    sheet_obj = None
    if not os.path.exists(client_file):
        sheets.get_sheets_authentication()
    else:
        sheet_obj = sheets.authorize_sheets()
    return sheet_obj


def get_config_path():
    """
    Gets the full path to the syncthing config file
    :return: A string containing the full path to the config file
    """
    command = "syncthing -paths"
    return_output = False
    print_output = True
    output_values = []
    try:
        p = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)
        if return_output or print_output:
            while True:
                output = p.stdout.readline()
                if output == '' and p.poll() is not None:
                    break
                if output:
                    output_values.append(output.strip())
        return output_values[1]
    except:
        print('Syncthing Not installed on system')


def get_my_device_info():
    """
    Retreives current device's information from the syncthing config file
    :return: A dictionary with the device ID and device name
    """
    machine_name = ''
    return_output = False
    print_output = True
    output_values = []
    p = subprocess.Popen('syncthing -device-id', stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)
    if return_output or print_output:
        while True:
            output = p.stdout.readline()
            if output == '' and p.poll() is not None:
                break
            if output:
                output_values.append(output.strip())

    device_id = output_values[0]
    filepath = get_config_path()
    if os.path.exists(filepath):
        tree = ElemTree.parse(filepath)
        root = tree.getroot()

        for child in root:
            if child.tag == 'device' and child.get('id') == device_id:
                machine_name = child.get('name')

        return {'id': device_id, 'name': machine_name}
    else:
        return None


def save_all_sync_events():
    api_key = get_sync_api_key()
    path = os.path.join(os.path.expanduser('~'), 'Documents', 'cglumberjack', 'sync_logs',
                        'time_%s.json' % datetime.datetime.now().strftime("%H_%M_%S"))
    r = requests.get('%s/events' % URL, headers={'X-API-Key': '%s' % api_key})
    dict = json.loads(r.content)
    with open(path, 'w+') as outfile:
        json.dump(dict, outfile, indent=4)


def syncthing_synced():
    api_key = get_sync_api_key()
    start_time = time.time()
    syncing_files = []
    synced_files = []
    synced = True
    total_bytes_done = 0
    total_bytes = 0
    total_uploads = 0
    uploading_files = False
    try:
        # TODO - this seems to only pull one value and continue to repeat it.
        r = requests.get('%s/events' % URL, headers={'X-API-Key': '%s' % api_key}, timeout=15)
        dict = json.loads(r.content)
        # print(dict)
        download = False
        for each in dict:
            if each['type'] == "FolderSummary":
                if each['data']['summary']['needBytes']:
                    synced = False
                    now = datetime.datetime.now()
                    event_time = each['time'].split('.')[0]
                    date_time_obj = datetime.datetime.strptime(str(event_time), '%Y-%m-%dT%H:%M:%S')
                    h, m, s = str(now - date_time_obj).split(':')
                    if m == '00':
                        syncing_files.append(each)
                    else:
                        synced_files.append(each)
                    # perc = (float(each['data']['summary']['needBytes'])/float(each['data']['summary']['globalBytes']))
                    # print('\t%s percent Synced' % perc)
            if each['type'] == 'DownloadProgress':
                download = True
                for folder in each['data']:
                    for file in each['data'][folder]:
                        total_bytes_done += each['data'][folder][file]['bytesDone']
                        total_bytes += each['data'][folder][file]['bytesTotal']
            if each['type'] == 'LocalIndexUpdated':
                synced = False
                uploading_files = True
                total_uploads += each['data']['items']
        if uploading_files:
            print("Pushing {} items".format(total_uploads))
        if syncing_files:
            print('Pulling: %s items' % len(syncing_files))
        if len(syncing_files)+total_uploads==0:
            return True
        if synced:
            return True
        else:
            return False
    except requests.exceptions.ReadTimeout:
        print('Sync reached 15s timeout - restarting')
        kill_syncthing()
        time.sleep(5)
        process_st_config()
        time.sleep(10)
        launch_syncthing()


def check_status(response):
    if response.status_code != 200:
        print('not yet')


def get_events_of_type(type):
    return_list = []
    api_key = get_sync_api_key()
    r = requests.get('%s/events' % URL, headers={'X-API-Key': '%s' % api_key})
    dict = json.loads(r.content)
    for each in dict:
        if each['type'] == type:
            return_list.append(each)
    return return_list


def get_download_progress(filename):
    return_list = []
    api_key = get_sync_api_key()
    r = requests.get('%s/events' % URL, headers={'X-API-Key': '%s' % api_key})
    dict = json.loads(r.content)
    for each in dict:
        if each['type'] == 'DownloadProgress':
            for folder in each['data']:
                for file in folder:
                    return_dict[file] = (file['bytesDone']/file['bytesTotal'])
    return return_dict


def add_device_info_to_sheet(sheet, server = 'false'):
    """
    Adds current device information to google sheet
    :param sheet: The sheet object to be edited
    :return:
    """
    new_row = sheets.find_empty_row_in_sheet(sheet)
    device_dictionary = get_my_device_info()
    if not sheets.id_exists(device_dictionary['id'], sheet) and not sheets.name_exists(device_dictionary['name'],sheet):
        sheet.update_cell(new_row, 1, device_dictionary['id'])
        sheet.update_cell(new_row, 2, device_dictionary['name'])
        sheet.update_cell(new_row, 3, getpass.getuser().lower())
        if server == 'true':
            sheet.update_cell(new_row, 4, 'Yes')
        else:
            sheet.update_cell(new_row, 4, 'No')


def get_all_device_info(sheet):
    """
    Gets all devices currently entered into syncthing
    :return: Array of dictionaries containing necessary device information
    """
    device_list = []
    num_of_rows = sheets.find_empty_row_in_sheet(sheet)
    for row in range(2, num_of_rows):
        if sheet.cell(row, 1).value != get_my_device_info()['id']:
            entry = {"id": sheet.cell(row, 1).value, "name": sheet.cell(row,2).value, "user": sheet.cell(row,3).value}
            device_list.append(entry)
    return device_list


def add_device_to_config(device_id, name, remove=True):
    """
    Add Specific Device to the Config
    :param device_id:
    :param name:
    :return:
    """
    device_list = [{'id': device_id,
                    'name': name}]
    sheet = get_sheet()
    # check to see if the device is on the device list.
    if sheets.id_exists(device_id, sheet):
        print('Adding approved device to Syncing %s' % device_list)
        add_all_devices_to_config(sheet=None, device_list=device_list, remove_pending=remove)
    else:
        print('Device not found in Google Sheets.')


def add_all_devices_to_config(sheet, device_list=False, remove_pending=False):
    """
    Add a new device to be synched with in syncthing
    :return:
    """
    if not device_list:
        if not sheet:
            print('Please Provide a Google Sheet to the function')
            return
        device_list = get_all_device_info(sheet)

    filepath = get_config_path()
    if os.path.exists(filepath):
        tree = ElemTree.parse(filepath)
        root = tree.getroot()
        for entry in device_list:
            print('adding device: %s' % entry)
            new_node = ElemTree.SubElement(root, 'device')
            new_node.set('id', entry['id'])
            new_node.set('name', entry['name'])
            new_node.set('compression', "metadata")
            new_node.set("introducer", "false")
            new_node.set("skipIntroductionRemovals", 'false')
            new_node.set("introducedBy", "")
            address = ElemTree.SubElement(new_node, 'address')
            address.text = 'dynamic'
            paused = ElemTree.SubElement(new_node, 'paused')
            paused.text = "false"
            autoAcceptFolders = ElemTree.SubElement(new_node, 'autoAcceptFolders')
            autoAcceptFolders.text = "true"
            maxSendKbps = ElemTree.SubElement(new_node, 'maxSendKbps')
            maxSendKbps.text = 0
            maxRecvKbps = ElemTree.SubElement(new_node, 'maxRecvKbps')
            maxRecvKbps.text = 0
            maxRequestKiB = ElemTree.SubElement(new_node, 'maxRequestKiB')
            maxRequestKiB.text = 0
        if remove_pending:
            for child in root:
                if child.tag == 'pendingDevice':
                    for key in device_list:
                        if key['id'] == child.get('id'):
                            root.remove(child)
        tree.write(filepath)
    else:
        print('Config File does not exist: %s' % filepath)


def get_all_devices_from_config():
    filepath = get_config_path()
    devices = []
    if os.path.exists(filepath):
        tree = ElemTree.parse(filepath)
        root = tree.getroot()
        for child in root:
            if child.tag == 'device':
                device_id = child.get('name')
                devices.append(device_id)
    return devices


def get_sync_folders():
    folders_dict = {}
    config_path = get_config_path()
    print(config_path)
    tree = ElemTree.parse(config_path)
    root = tree.getroot()
    device_id = ''
    for child in root:
        if child.tag == 'device':
            device_id = child.get('name')
        if child.tag == 'folder':
            sync_folder = child.get('path').replace('\\', '/')
            try:
                path_object = PathObject(sync_folder)
                #  print(path_object.path_root)
                user_path = path_object.split_after('user')
                task_path = path_object.split_after('task')
                shot_path = path_object.split_after('shot')
                seq_path = path_object.split_after('seq')
                set_sync_statuses(folders_dict, user_path, sync_folder, device_id)
                set_sync_statuses(folders_dict, task_path, user_path, device_id)
                set_sync_statuses(folders_dict, shot_path, task_path, device_id)
                set_sync_statuses(folders_dict, seq_path, shot_path, device_id)
            except TypeError:
                pass
            folders_dict[sync_folder] = {'type': child.get('type'),
                                         'devices': [device_id],
                                         'folders': []}
    return folders_dict


def set_sync_statuses(folders_dict, path_, sync_folder, device_id):
    if path_ in folders_dict.keys():
        if sync_folder not in folders_dict[path_]['folders']:
            folders_dict[path_]['folders'].append(sync_folder)
            folders_dict[path_]['type'] = '%s Synced' % len(folders_dict[path_]['folders'])
        if device_id not in folders_dict[path_]['devices']:
            folders_dict[path_]['devices'].append(device_id)
    else:
        folders_dict[path_] = {'folders': [sync_folder],
                               'type': '1 Synced',
                               'devices': [device_id]}


def add_folder_to_config(folder_id, filepath, device_list=None, type_='sendonly', sqs=True):
    """
    Function to add a new folder to config.xml file
    :param folder_id: The ID label for the folder being added to syncthing
    :param filepath: The path to the file being added to syncthing
    :param device_list: List of Device IDs to share with the folders.
    :return:
    """
    folder_id = folder_id.replace('/', '\\')
    filepath = filepath.replace('/', '\\')
    # p_obj = PathObject(filepath)
    # if p_obj.scope == 'assets':
    #     label = '%s-%s-%s (%s)' % (p_obj.asset, p_obj.task, p_obj.version, p_obj.context)
    # elif p_obj.scope == 'shots':
    #     label = '%s_%s-%s-%s (%s)' % (p_obj.seq, p_obj.shot, p_obj.task, p_obj.version, p_obj.context)
    # # TODO - check to see if the folder exists
    config_path = get_config_path()
    tree = ElemTree.parse(config_path)
    root = tree.getroot()
    new_node = None
    write = True
    folder_node = folder_id_exists(folder_id, tree=tree)
    if folder_node is not None:
        new_node = folder_node
    else:
        print(folder_id, 'does not exist in config, creating')
        new_node = ElemTree.SubElement(root, 'folder')
        new_node.set('id', folder_id)
        new_node.set('path', filepath)
        # new_node.set('label', label)
        new_node.set('type', type_)
        new_node.set('rescanIntervalS', '3600')
        new_node.set('fsWatcherEnabled', "True")
        new_node.set('fsWatcherDelayS', "10")
        new_node.set('ignorePerms', "false")
        new_node.set('autoNormalize', "true")
        write = True
    if device_list:
        for id_ in device_list:
            print('adding device %s to folder %s' % (id_, filepath))
            device_node = ElemTree.SubElement(new_node, 'device')
            device_node.set('id', id_)
            write = True
    if write:
        # assumes syncthing is dead already
        print('writing file to %s' % get_config_path())
        tree.write(get_config_path())
        # assumes other code will launch syncthing.


def get_device_dict():
    """
    Queries Google Sheets for all devices.  This could be made much faster if it simply querried the current config file
    for sync thing.
    :return:
    """
    sheet = get_sheet()
    row_count = sheets.find_empty_row_in_sheet(sheet)
    device_id_col = 0
    device_name_col = 1
    user_col = 2
    server_col = 3
    device_dict = {}
    for i in range(2, row_count):
        data = sheet.row_values(i)
        device_dict[data[device_id_col]] = {'username': data[user_col],
                                            'device_name': data[device_name_col],
                                            'proj_man_user': '',
                                            'full_name': '',
                                            'is_server': data[server_col]}
    return device_dict


def share_files(path_object):
    from cgl.ui.widgets.sync_master import SyncMaster
    current_m_type = None
    from cgl.core.config.config import ProjectConfig
    user_globals = ProjectConfig().user_config
    if 'sync_thing_machine_type' in user_globals.keys():
        current_m_type = user_globals['sync_thing_machine_type']
    if not current_m_type:
        set_machine_type("")
        print('This machine is not set up for syncing, sync files not accessible')
        return
    print(path_object.company)
    print(path_object.project)
    print(path_object.scope)
    sm_dialog = SyncMaster(company=path_object.company,
                           project=path_object.project,
                           scope=path_object.scope,
                           device_list=[])
    sm_dialog.exec_()


def share_project(path_object):
    from cgl.ui.widgets.sync_master import SharingDialog
    dialog_ = SharingDialog(path_object=path_object, type_='sendreceive')
    dialog_.exec_()
    if dialog_.button == 'Ok':
        launch_syncthing(verbose=True)


def share_folders_to_devices(device_ids=[], folder_list=[r'[root]\_config\cgl_tools'], dialog=False):
    """
    Makes all files shareable to all devices found in the config file
    :return:
    """

    config_path = get_config_path()
    tree = ElemTree.parse(config_path)
    root = tree.getroot()
    write = False
    if not device_ids:
        print('No device IDs identified, skipping file share')
        return

    for child in root:
        shared = []
        if child.tag == 'folder':
            id_ = child.get('id')
            if id_ in folder_list:
                for sub_element in child:
                    if sub_element.tag == 'device':
                        shared.append(sub_element.get('id'))
                for d_id in device_ids:
                    if d_id not in shared:
                        new_node = ElemTree.SubElement(child, 'device')
                        new_node.set('id', d_id)
                        write = True
    if write:
        write_globals(tree)


def sync_with_server():
    """
    Shares all local files with the server machine
    :param sheet: Google sheet object for the device sheet
    :return:
    """
    write = False
    company = 'lone-coconut'
    sheet_name = 'LONE_COCONUT_SYNC_THING'
    sheet = get_sheet()
    device_id = ''
    num_rows = sheets.find_empty_row_in_sheet(sheet)

    for entry in range(2, num_rows):
        if sheet.cell(entry, 4).value == 'Yes':
            device_id = sheet.cell(entry, 1).value

    config_path = get_config_path()
    tree = ElemTree.parse(config_path)
    root = tree.getroot()

    if device_id != '':
        for child in root:
            if child.tag == 'folder' and '[' in child.get('id'):
                new_node = ElemTree.SubElement(child, 'device')
                new_node.set('id', device_id)
                write = True
    else:
        print("Error finding server device in sheet")
    if write:
        write_globals(tree)


def write_globals(tree, kill=True):
    """
    Allows me to write globals for a elemtree, acts as a wrapper around what syncthing needs to do before/after.
    :param tree:
    :return:
    """
    if kill:
        kill_syncthing()
    tree.write(get_config_path())
    launch_syncthing()


def wipe_globals(verbose=False):
    # TODO - Clean up SHEETS - remove the device from the list.
    # TODO - is there a way to remove the device from syncthing?
    # TODO -
    kill_syncthing()
    clear_sync_thing_user_globals()
    config_path = get_config_path()
    if os.path.exists(config_path):
        os.remove(config_path)
    launch_syncthing(verbose=verbose)


def launch_syncthing(verbose=False):
    # kill_syncthing()
    # print('launching syncthing in background')
    print('Launching Syncthing')
    if verbose:
        command = "syncthing"
    else:
        command = "syncthing -no-browser -no-console"
    cgl_execute(command, new_window=True)


def kill_syncthing():
    import psutil
    killed = False
    for proc in psutil.process_iter():
        if proc.name() == 'syncthing.exe':
            proc.terminate()
            killed = True
    if killed:
        print('Killed Syncthing background processes')


def show_browser():
    from cgl.core.utils.general import cgl_execute
    print('Launching Syncthing Browser')
    # TODO - i want it to only be the browser-only, but for now it seems like there are times when we have to blast it
    # command = 'syncthing -browser-only'
    command = 'syncthing'
    cgl_execute(command, new_window=True)


def syncthing_running():
    import psutil
    for proc in psutil.process_iter():
        if proc.name() == 'syncthing.exe':
            return True
    else:
        print('Syncthing: Not Running, Launching Syncthing')
        launch_syncthing()
        return False


def test(name):
    r = os.popen('tasklist /v').read().strip().split('\n')
    print(('# of tasks is %s' % (len(r))))
    for i in range(len(r)):
        s = r[i]
        if name in r[i]:
            print(('%s in r[i]' % (name)))
            return r[i]
    return []


def get_sync_api_key():
    config_path = get_config_path()
    tree = ElemTree.parse(config_path)
    root = tree.getroot()
    # print(root['gui']['api_key'])
    for child in root:
        if child.tag == 'gui':
            for c in child:
                if c.tag == 'apikey':
                    return c.text
    return None


def update_machines():
    print('update_machines')
    # TODO - sheet_name and client_json need to be globals.
    kill_syncthing()
    sheet = sheets.authorize_sheets()
    add_all_devices_to_config(sheet)
    share_folders_to_devices()
    launch_syncthing()


if __name__ == "__main__":
    #wipe_globals()
    #setup_workstation()
    #kill_syncthing()
    # process_pending_devices()
    # print(get_all_devices_from_config())
    # print(get_my_device_info()['name'])
    #from cgl.core.utils.general import launch_lumber_watch
    # launch_lumber_watch()
    #launch_syncthing(True)
    pass