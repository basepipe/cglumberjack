import click
import xml.etree.ElementTree as ET
import gspread
import requests
import os
import getpass
import subprocess
from oauth2client.service_account import ServiceAccountCredentials


def authorize_sheets(sheet_name):
    """
    Authorizes api calls to the google sheet
    :param sheet_name: Title of the sheet being accessed
    :return: A google sheet object
    """
    scope = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/spreadsheets',
             'https://www.googleapis.com/auth/drive']

    filepath = 'C:\\Users\\Molta\\Desktop\\client.json'
    creds = ServiceAccountCredentials.from_json_keyfile_name(filepath, scope)

    client = gspread.authorize(creds)

    sheet = client.open(sheet_name).sheet1
    return sheet


def does_id_exist(id, sheet):
    """
    Checks to see if ID is already entered into the google sheet
    :param id: ID to look for in sheet
    :param sheet: Title of google sheet to search in
    :return: True if the value is already entered in the sheet, false if the value has no entry yet
    """
    sheet = authorize_sheets(sheet)
    data = sheet.col_values(1)
    for i in data:
        if i == id:
            return True
    return False


def find_empty_row_in_sheet():
    """
    Finds the first empty row in the google sheet
    :return: Integer representation of the first empty row
    """
    sheet = authorize_sheets('LONE_COCONUT_SYNC_THING')
    count = 1
    data = sheet.col_values(1)
    for i in data:
        if i == '':
            return count
        count += 1
    return count


def get_sheets_authentication(filepath, client='lone-coconut'):
    """
    Gets the json authentication file from amazon s3 and saves it on the local machine at the filepath
    :param client: The name of the client for the sheet
    :param filepath: The filepath where the authentication json will be saved
    :return: Returns the filepath to the local copy of the authentication file
    """
    url = 'https://%s.s3.amazonaws.com/sync_thing/lone-coconut-syncthing-0853eb66e60e.json' % client
    r = requests.get(url, allow_redirects=True)
    with open(filepath, 'w+') as f:
        f.write(r.content)
    return filepath


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
    print output_values[1]
    return output_values[1]


def get_my_device_info():
    """
    Retreives current device's information from the syncthing config file
    :return: A dictionary with the device ID and device name
    """
    filepath = get_config_path()
    tree = ET.parse(filepath)
    root = tree.getroot()
    my_id = root[0][1].get('id')

    for child in root:
        if child.tag == 'device' and child.get('id') == my_id:
            machine_name = child.get('name')
            print machine_name

    return {'id': my_id, 'name': machine_name}

def add_device_info_to_sheet(sheet_name):
    """
    Adds current device information to google sheet
    :return:
    """
    sheet = authorize_sheets(sheet_name)
    new_row = find_empty_row_in_sheet()
    device_dictionary = get_my_device_info()
    sheet.update_cell(new_row, 1, device_dictionary['id'])
    sheet.update_cell(new_row, 2, device_dictionary['name'])
    sheet.update_cell(new_row, 3, getpass.getuser().lower())

def get_all_device_info():
    """
    Gets all devices currently entered into syncthing
    :return: Array of dictionaries containing necessary device information
    """
    sheet = authorize_sheets('LONE_COCONUT_SYNC_THING')
    device_list = []
    num_of_rows = find_empty_row_in_sheet()
    print num_of_rows
    for row in range(2, num_of_rows):
        if sheet.cell(row,1).value != get_my_device_info()['id']:
            entry = {"id": sheet.cell(row, 1).value, "name": sheet.cell(row,2).value, "user": sheet.cell(row,3).value}
            device_list.append(entry)
    print device_list
    return device_list


def add_all_device_id_to_config():
    """
    Add a new device to be synched with in syncthing
    :return:
    """
    device_list = get_all_device_info()
    filepath = get_config_path()
    tree = ET.parse(filepath)
    root = tree.getroot()

    print root[1]

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
        autoAcceptFolders.text = "false"
        maxSendKbps = ET.SubElement(new_node, 'maxSendKbps')
        maxSendKbps.text = 0
        maxRecvKbps = ET.SubElement(new_node, 'maxRecvKbps')
        maxRecvKbps.text = 0
        maxRequestKiB = ET.SubElement(new_node, 'maxRequestKiB')
        maxRequestKiB.text = 0

    tree.write(filepath)


def add_folder_to_config(folder_id, filepath):
    """
    Function to add a new folder to be synched through syncthing
    :param folder_id: The ID label for the folder being added to syncthing
    :param filepath: The path to the file being added to syncthing
    :return:
    """

    config_path = get_config_path()
    tree = ET.parse(config_path)
    root = tree.getroot()

    new_node = ET.SubElement(root, 'folder')
    new_node.set('id', folder_id)
    new_node.set('path', filepath)
    tree.write(config_path)




if __name__ =="__main__":
    # get_sheets_authentication(filepath)
    # add_device_info_to_sheet(filepath)
    # add_all_device_id_to_config()
    # add_folder_to_config('kyls_new_file', 'C:\\Users\\Molta\\test')