import xml.etree.ElementTree as ET
import getpass
import os
import subprocess
import cgl.plugins.google.sheets as sheets
import psutil


def setup(company, sheet_name, folder_dict=[], setup_studio=False):
    """
    setups up everything needed for syncthing to run in the production environment, adds folders to the config.
    :param folder_dict: dictionary of pairs of {folder_id: full_path}
    :return:
    """
    kill_syncthing()
    if folder_dict:
        config_path = get_config_path()
        if not os.path.exists(config_path):
            print 'launching syncthing'
        sheet_obj = get_sheet(company, sheet_name)
        add_device_info_to_sheet(sheet_obj)
        add_all_devices_to_config(sheet_obj)
        for folder_id in folder_dict:
            if not folder_id_exists(folder_id):
                add_folder_to_config(folder_id, folder_dict[folder_id])
        if setup_studio:
            share_files_to_devices() # only if you're setting up main folders
        else:
            print 'pulling from studio'
            pull_from_studio()
            # notify_of_machine_add()
    else:
        print('Please provide a list of folders before attempting to set up syncthing')
    launch_syncthing()


def pull_from_studio():
    """
    map shared folders to the correct location on local drive
    :return:
    """
    from cgl.core.config import app_config
    folders_dict = get_syncthing_folders()
    for folder_id in folders_dict:
        print folder_id
        try:
            variable, the_rest = folder_id.split(']')
            variable = variable.replace('[', '')
            value = app_config()['paths'][variable]
            local_path = '%s%s' % (value, the_rest)
            edit_syncthing_folder(folder_id, local_path)
            print local_path
        except ValueError:
            print('Skipping %s, only handling lumbermill created folders for now' % folder_id)


def get_syncthing_folders():
    """
    creates a dictionary of {folder_id: path} for all the folders in syncthing.
    :return: Dictionary of folder ID's mapped to folder paths
    """
    config_path = get_config_path()
    tree = ET.parse(config_path)
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
    tree = ET.parse(config_path)
    root = tree.getroot()

    for child in root:
        if child.tag == 'folder' and child.get('id') == folder_id:
            child.set('path', new_local_path)

    tree.write(config_path)


def folder_id_exists(folder_id, folder_path=''):
    config_path = get_config_path()
    tree = ET.parse(config_path)
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


def get_sheet(company, sheet_name):
    """
    Gets the sheet object for a company
    :param company: Company name in the s3 database
    :param sheet_name: Name of the google sheet being accessed
    :return: Sheet object
    """
    from cgl.core.config import app_config
    client_file = os.path.join(app_config()['paths']['root'], '_config', 'client.json')
    sheets.get_sheets_authentication(client_file, company)
    sheet_obj = sheets.authorize_sheets(sheet_name, client_file)
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
    tree = ET.parse(filepath)
    root = tree.getroot()

    for child in root:
        if child.tag == 'device' and child.get('id') == device_id:
            machine_name = child.get('name')

    return {'id': device_id, 'name': machine_name}


def add_device_info_to_sheet(sheet):
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


def get_all_device_info(sheet):
    """
    Gets all devices currently entered into syncthing
    :return: Array of dictionaries containing necessary device information
    """
    device_list = []
    num_of_rows = sheets.find_empty_row_in_sheet(sheet)
    for row in range(2, num_of_rows):
        if sheet.cell(row,1).value != get_my_device_info()['id']:
            entry = {"id": sheet.cell(row, 1).value, "name": sheet.cell(row,2).value, "user": sheet.cell(row,3).value}
            device_list.append(entry)
    return device_list


def add_all_devices_to_config(sheet):
    """
    Add a new device to be synched with in syncthing
    :return:
    """
    device_list = get_all_device_info(sheet)
    filepath = get_config_path()
    tree = ET.parse(filepath)
    root = tree.getroot()

    for entry in device_list:
        new_node = ET.SubElement(root, 'device')
        new_node.set('id', entry['id'])
        new_node.set('name', entry['name'])
        new_node.set('compression', "metadata")
        new_node.set("introducer", "false")
        new_node.set("skipIntroductionRemovals", 'false')
        new_node.set("introducedBy", "")
        address = ET.SubElement(new_node, 'address')
        address.text = 'dynamic'
        paused = ET.SubElement(new_node, 'paused')
        paused.text = "false"
        autoAcceptFolders = ET.SubElement(new_node, 'autoAcceptFolders')
        autoAcceptFolders.text = "true"
        maxSendKbps = ET.SubElement(new_node, 'maxSendKbps')
        maxSendKbps.text = 0
        maxRecvKbps = ET.SubElement(new_node, 'maxRecvKbps')
        maxRecvKbps.text = 0
        maxRequestKiB = ET.SubElement(new_node, 'maxRequestKiB')
        maxRequestKiB.text = 0
    tree.write(filepath)


def add_folder_to_config(folder_id, filepath):
    """
    Function to add a new folder to config.xml file
    :param folder_id: The ID label for the folder being added to syncthing
    :param filepath: The path to the file being added to syncthing
    :return:
    """
    # TODO - check to see if the folder exists
    config_path = get_config_path()
    tree = ET.parse(config_path)
    root = tree.getroot()

    new_node = ET.SubElement(root, 'folder')
    new_node.set('id', folder_id)
    new_node.set('path', filepath)
    new_node.set('type', 'sendreceive')
    new_node.set('rescanIntervalS', '3600')
    new_node.set('fsWatcherEnabled', "True")
    new_node.set('fsWatcherDelayS', "10")
    new_node.set('ignorePerms', "false")
    new_node.set('autoNormalize', "true")
    tree.write(config_path)


def share_files_to_devices():
    """
    Makes all files shareable to all devices found in the config file
    :return:
    """
    config_path = get_config_path()
    tree = ET.parse(config_path)
    root = tree.getroot()

    all_device_id = []

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
                    new_node = ET.SubElement(child, 'device')
                    new_node.set('id', id)
    tree.write(config_path)


def share_with_server(sheet, files = ['']):
    """
    Shares all local files with the server machine
    :param sheet: Google sheet object for the device sheet
    :return:
    """
    device_id = ''
    num_rows = sheets.find_empty_row_in_sheet(sheet)

    for entry in range(2, num_rows):
        if sheet.cell(entry, 4).value == 'Yes':
            device_id = sheet.cell(entry, 1).value

    config_path = get_config_path()
    tree = ET.parse(config_path)
    root = tree.getroot()

    if device_id != '':
        for child in root:
            if child.tag == 'folder' and child.get('id') in files:
                new_node = ET.SubElement(child, 'device')
                new_node.set('id', device_id)
        tree.write(config_path)
    else:
        print "Error finding server device in sheet"


def launch_syncthing():
    kill_syncthing()
    command = "syncthing"
    p = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)
    return p


def kill_syncthing():
    for proc in psutil.process_iter():
        if proc.name() == 'syncthing.exe':
            proc.terminate()
            print "Process Ended"


def update_machines(sheet_name='LONE_COCONUT_SYNC_THING', client_json='Z:\cocodrive\COMPANIES\_config\client.json'):
    kill_syncthing()
    sheet = sheets.authorize_sheets('LONE_COCONUT_SYNC_THING', 'Z:\cocodrive\COMPANIES\_config\client.json')
    add_all_devices_to_config(sheet)
    share_files_to_devices()
    launch_syncthing()


if __name__ == "__main__":
    print "syncthing"