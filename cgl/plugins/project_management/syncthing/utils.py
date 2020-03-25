import click
import xml.etree.ElementTree as ET
import gspread
import requests
import os
import getpass
import subprocess
from oauth2client.service_account import ServiceAccountCredentials

scope = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']

filepath = 'C:\\Users\\Molta\\Desktop\\client.json'
creds = ServiceAccountCredentials.from_json_keyfile_name(filepath, scope)

client = gspread.authorize(creds)

sheet = client.open('LONE_COCONUT_SYNC_THING').sheet1


def does_id_exist(value):
    """

    :param value:
    :return:
    """
    data = sheet.col_values(1)
    for i in data:
        if i == value:
            return True
    return False


def find_empty_row_in_sheet():
    """

    :return:
    """
    count = 1
    data = sheet.col_values(1)
    for i in data:
        if i == '':
            return count
        count += 1
    return count


def get_sheets_authentication(filepath, client='lone-coconut'):
    """

    :param client:
    :param filepath:
    :return:
    """
    url = 'https://%s.s3.amazonaws.com/sync_thing/lone-coconut-syncthing-0853eb66e60e.json' % client
    r = requests.get(url, allow_redirects=True)
    with open(filepath, 'w+') as f:
        f.write(r.content)
    return filepath

def get_config_path():
    """

    :return:
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

    :return:
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

def add_device_info_to_sheet(cred_path):
    """

    :return:
    """
    new_row = find_empty_row_in_sheet()
    device_dictionary = get_my_device_info()
    sheet.update_cell(new_row, 1, device_dictionary['id'])
    sheet.update_cell(new_row, 2, device_dictionary['name'])
    sheet.update_cell(new_row, 3, getpass.getuser().lower())

def get_all_device_id():
    """

    :return:
    """
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

    :return:
    """
    device_list = get_all_device_id()
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





if __name__ =="__main__":
    # get_sheets_authentication(filepath)
    # add_device_info_to_sheet(filepath)
    add_all_device_id_to_config()