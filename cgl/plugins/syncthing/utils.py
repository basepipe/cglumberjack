import xml.etree.ElementTree as ElemTree
import getpass
import os
import subprocess
import psutil
import cgl.plugins.google.sheets as sheets
from cgl.core.utils.general import launch_lumber_watch
from cgl.core.utils.read_write import load_json


def setup_server():
    kill_syncthing()
    USER_GLOBALS = load_json(os.path.join(os.path.expanduser('~\Documents'), 'cglumberjack', 'user_globals.json'))
    GLOBALS = load_json(USER_GLOBALS['globals'])
    cgl_tools_folder = GLOBALS['paths']['cgl_tools']
    sheet_obj = get_sheet()
    add_device_info_to_sheet(sheet_obj, server='true')
    add_all_devices_to_config(sheet_obj)
    folder_id = r'[root]\_config\cgl_tools'
    add_folder_to_config(folder_id, cgl_tools_folder)
    share_files_to_devices()  # only if you're setting up main folders
    launch_syncthing()


def setup_workstation():
    """
    sets up local workstation to talk to the studio side server.
    :param company:
    :param sheet_name:
    :return:
    """
    USER_GLOBALS = load_json(os.path.join(os.path.expanduser('~\Documents'), 'cglumberjack', 'user_globals.json'))
    GLOBALS = load_json(USER_GLOBALS['globals'])
    kill_syncthing()
    device_info = get_my_device_info()
    print('Setting Up Workstation for Syncing')
    company = GLOBALS['account_info']['aws_company_name']
    sheet_name = GLOBALS['sync']['syncthing']['sheets_name']
    folder_id = r'[root]\_config\cgl_tools'
    folder_path = GLOBALS['paths']['cgl_tools']
    sheet_obj = get_sheet()
    add_device_info_to_sheet(sheet_obj)
    add_all_devices_to_config(sheet_obj)
    add_folder_to_config(folder_id, folder_path)
    launch_syncthing()
    from cgl.plugins.aws.cgl_sqs.utils import machine_added_message
    machine_added_message(device_id=device_info['id'],
                          device_name=device_info['name'],
                          message='%s added machine %s' % ('user', device_info['name']))


def fix_folder_paths():
    kill_syncthing()
    config_path = get_config_path()
    print config_path
    tree = ElemTree.parse(config_path)
    print tree
    root = tree.getroot()
    print('Fixing Folder Paths')
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
    print '------------------------------'
    print tree
    tree.write(config_path)
    launch_syncthing()


def accept_folders():
    kill_syncthing()
    # parse the xml
    config_path = get_config_path()
    tree = ElemTree.parse(config_path)
    root = tree.getroot()
    folders_dict = {}

    for child in root:
        if child.tag == 'device':
            for c in child:
                if c.tag == 'pendingFolder':
                    id_ = c.get('id')
                    folder = get_folder_from_id(id_)
                    add_folder_to_config(id_, folder)
    launch_syncthing()


def get_folder_from_id(folder_id):
    user_globals = load_json(os.path.join(os.path.expanduser(r'~\Documents'), 'cglumberjack', 'user_globals.json'))
    globals_ = load_json(user_globals['globals'])
    try:
        variable, the_rest = folder_id.split(']')
        variable = variable.replace('[', '')
        value = globals_['paths'][variable]
        local_path = '%s%s' % (value, the_rest)
        return local_path
    except ValueError:
        print('Skipping %s, it is not a lumbermill share' % folder_id)


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
    existing_folders = []

    for child in root:
        if child.tag == 'folder':
            entry = {'id': child.get('id'), 'path': child.get('path')}
            existing_folders.append(entry)

    for entry in existing_folders:
        if folder_id == entry['id'] or folder_path == entry['path']:
            return True
    return False


def get_sheet():
    """
    Gets the sheet object for a company
    :param company: Company name in the s3 database
    :param sheet_name: Name of the google sheet being accessed
    :return: Sheet object
    """
    user_globals = load_json(os.path.join(os.path.expanduser(r'~\Documents'), 'cglumberjack', 'user_globals.json'))
    globals_ = load_json(user_globals['globals'])
    client_file = globals_['sync']['syncthing']['sheets_config_path']
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
    p = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)
    if return_output or print_output:
        while True:
            output = p.stdout.readline()
            if output == '' and p.poll() is not None:
                break
            if output:
                output_values.append(output.strip())
    return output_values[1]


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
    tree = ElemTree.parse(filepath)
    root = tree.getroot()

    for child in root:
        if child.tag == 'device' and child.get('id') == device_id:
            machine_name = child.get('name')

    return {'id': device_id, 'name': machine_name}


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


def add_device_to_config(device_id, name):
    """
    Add Specific Device to the Config
    :param device_id:
    :param name:
    :return:
    """
    device_list = [{'id': device_id,
                    'name': name}]
    add_all_devices_to_config(sheet=None, device_list=device_list)


def add_all_devices_to_config(sheet, device_list=False):
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
        tree.write(filepath)
    else:
        print('Config File does not exist: %s' % filepath)


def add_folder_to_config(folder_id, filepath):
    """
    Function to add a new folder to config.xml file
    :param folder_id: The ID label for the folder being added to syncthing
    :param filepath: The path to the file being added to syncthing
    :return:
    """
    folder_id = folder_id.replace('/', '\\')
    filepath = filepath.replace('/', '\\')
    # TODO - check to see if the folder exists
    config_path = get_config_path()
    tree = ElemTree.parse(config_path)
    root = tree.getroot()
    if not folder_id_exists(folder_id, tree=tree):
        new_node = ElemTree.SubElement(root, 'folder')
        new_node.set('id', folder_id)
        new_node.set('path', filepath)
        new_node.set('type', 'sendreceive')
        new_node.set('rescanIntervalS', '3600')
        new_node.set('fsWatcherEnabled', "True")
        new_node.set('fsWatcherDelayS', "10")
        new_node.set('ignorePerms', "false")
        new_node.set('autoNormalize', "true")
    tree.write(config_path)


def get_device_dict():
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


def share_files_to_devices(all_device_id=[], dialog=True):
    """
    Makes all files shareable to all devices found in the config file
    :return:
    """
    from cgl.plugins.aws.cgl_sqs.utils import folders_shared_message
    from cgl.ui.widgets.sync_master import SharingDialog
    # TODO - need a popup to choose who to share something with.
    if dialog:
        device_dict = get_device_dict()
        this_device = get_my_device_info()['id']
        dialog_sharing = SharingDialog(this_device, device_dict)
        dialog_sharing.exec_()
        if dialog_sharing.button == 'Ok':
            print dialog_sharing.device_list
    return
    folders_shared_message(device_id=id, device_name='test')

    config_path = get_config_path()
    tree = ElemTree.parse(config_path)
    root = tree.getroot()
    if not all_device_id:
        for child in root:
            if child.tag == 'device':
                all_device_id.append(child.get('id'))

    for child in root:
        shared = []
        if child.tag == 'folder':
            for sub_element in child:
                if sub_element.tag == 'device':
                    shared.append(sub_element.get('id'))
            for id in all_device_id:
                if id not in shared:
                    new_node = ElemTree.SubElement(child, 'device')
                    new_node.set('id', id)
    tree.write(config_path)





def sync_with_server():
    """
    Shares all local files with the server machine
    :param sheet: Google sheet object for the device sheet
    :return:
    """
    # TODO - this is temp - company-aws, and sheet_name must be in globals.
    kill_syncthing()
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
        tree.write(config_path)
    else:
        print "Error finding server device in sheet"
    launch_syncthing()


def wipe_globals():
    kill_syncthing()
    config_path = get_config_path()
    os.remove(config_path)
    launch_syncthing()
    # remove_default_folder()


def launch_syncthing():
    # TODO how do i launch syncthing without the gui?
    kill_syncthing()
    command = "syncthing"
    p = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)
    return p


def kill_syncthing():
    for proc in psutil.process_iter():
        if proc.name() == 'syncthing.exe':
            proc.terminate()
            print "Process Ended"


def nuke_syncthing(clean_sheets=False):
    """
    Kill's Syncthing
    Delete's the config.xml
    Removes all machines from the google sheet related to this Company
    restarts syncthing
    starts "Lumber-watch" as a background process.
    :return:
    """
    if clean_sheets:
        pass
        # wipe_sheets()
    wipe_globals()


def server_setup_test():
    wipe_globals()
    setup_server()
    launch_lumber_watch()


def workstation_setup_test():
    wipe_globals()
    setup_workstation()
    launch_lumber_watch()


def update_machines():
    # TODO - sheet_name and client_json need to be globals.
    kill_syncthing()
    sheet = sheets.authorize_sheets()
    add_all_devices_to_config(sheet)
    share_files_to_devices()
    launch_syncthing()


if __name__ == "__main__":
    pass

