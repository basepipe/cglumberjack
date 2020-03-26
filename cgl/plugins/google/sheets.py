import gspread
import requests
from oauth2client.service_account import ServiceAccountCredentials


def authorize_sheets(sheet_name, filepath):
    """
    Authorizes api calls to the google sheet
    :param filepath: Path to the sheets json authentication file
    :param sheet_name: Title of the sheet being accessed
    :return: A google sheet object
    """
    scope = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/spreadsheets',
             'https://www.googleapis.com/auth/drive']

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
    data = sheet.col_values(1)
    for i in data:
        if i == id:
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