import gspread
import requests
from oauth2client.service_account import ServiceAccountCredentials

"""
TODO:
1. Check if device id already exists in google doc, dont add it again
2. If file id already exists, dont add it to xml
"""


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


def does_name_exist(name, sheet):
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


# if __name__ == '__main__':
#     # sheet = authorize_sheets('LONE_COCONUT_SYNC_THING', 'C:\\Users\\Molta\\Desktop\\client.json')
#     # k = does_id_exist('2SB5KDS-FHJ5MEH-RJKY2QR-FLJ6S3R-4KQHBCW-2YZCRJJ-LULS7LQ-NUGWDAB', sheet)
#     # print k
#     # l = does_name_exist('DESKTOP-CEDFLDG', sheet)
#     # print l