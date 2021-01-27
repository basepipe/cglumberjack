import os
from oauth2client.service_account import ServiceAccountCredentials
import requests
from cgl.core.utils.read_write import load_json

"""
TODO:
1. Check if device id already exists in google doc, dont add it again
2. If file id already exists, dont add it to xml
"""


def authorize_sheets():
    """
    Authorizes api calls to the google sheet
    :param filepath: Path to the sheets json authentication file
    :param sheet_name: Title of the sheet being accessed
    :return: A google sheet object
    """
    from cgl.core.config.config import ProjectConfig, get_sync_config_file
    import gspread
    scope = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/spreadsheets',
             'https://www.googleapis.com/auth/drive']

    globals_ = load_json(get_sync_config_file())
    sheet_name = globals_['sync']['syncthing']['sheets_name']
    client_file = globals_['sync']['syncthing']['sheets_config_path']
    if os.path.exists(client_file):
        print('client file:{}'.format(client_file))
        creds = ServiceAccountCredentials.from_json_keyfile_name(client_file, scope)
        client = gspread.authorize(creds)
        sheet = client.open(sheet_name).sheet1
        return sheet
    else:
        print('No Client file found at: {}'.format(client_file))
        return None


def id_exists(id, sheet):
    """
    Checks to see if ID is already entered into the google sheet
    :param id: ID to look for in sheet
    :param sheet: Title of google sheet to search in
    :return: True if the value is already entered in the sheet, false if the value has no entry yet
    """
    data = sheet.col_values(1)
    for i in data:
        if i == id:
            return True
    return False


def name_exists(name, sheet):
    """
    Checks to see if name is already entered into the google sheet
    :param name: Name to look for in sheet
    :param sheet: Title of google sheet to search in
    :return: True if the value is already entered in the sheet, false if the value has no entry yet
    """
    data = sheet.col_values(2)
    for n in data:
        if n == name:
            return True
    return False


def find_empty_row_in_sheet(sheet):
    """
    Finds the first empty row in the google sheet
    :return: Integer representation of the first empty row
    """
    count = 1
    data = sheet.col_values(1)
    for i in data:
        if i == '':
            return count
        count += 1
    return count


def get_sheets_authentication():
    """
    Gets the json authentication file from amazon s3 and saves it on the local machine at the filepath
    :param client: The name of the client for the sheet
    :param filepath: The filepath where the authentication json will be saved
    :return: Returns the filepath to the local copy of the authentication file
    """
    # TODO - change this to read the ENV Variable once that's more stable/consistant.
    from cgl.core.config.config import get_sync_config_file

    sync_info = load_json(get_sync_config_file())
    filepath = sync_info['sync']['syncthing']['sheets_config_path']
    if filepath.endswith('.json'):
        url = sync_info['sync']['syncthing']['sync_thing_url']
        print('url...', url)
        try:
            import urllib.request
            urllib.request.urlretrieve(url, filepath)
            return filepath
        except ImportError:
            # Python 2 Version
            r = requests.get(url, allow_redirects=True)
            with open(filepath, 'w+') as f:
                f.write(r.content)
            return filepath
    else:
        print('ERROR in sheets_config_path globals, %s does not match client.json format' % filepath)



