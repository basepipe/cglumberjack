import os
from oauth2client.service_account import ServiceAccountCredentials
import requests
from cgl.core.utils.read_write import load_json
import cgl.plugins.google.sheets as sheets


# TODO: Change function to work with globals instead of hard code
def authorize_sheets():
    """
    Authorizes api calls to the google sheet
    :param filepath: Path to the sheets json authentication file
    :param sheet_name: Title of the sheet being accessed
    :return: A google sheet object
    """
    import gspread
    scope = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/spreadsheets',
             'https://www.googleapis.com/auth/drive']
    sheet_name = 'Dev_onboarding'
    client_file = get_sheets_authentication()
    creds = ServiceAccountCredentials.from_json_keyfile_name(client_file, scope)
    client = gspread.authorize(creds)
    sheet = client.open(sheet_name).sheet1

    return sheet


# TODO: Change function to work with globals instead of hard code
def get_sheets_authentication():
    url = 'https://cgl-developeronboarding.s3.amazonaws.com/dev_onboarding_auth.json'
    r = requests.get(url, allow_redirects=True)
    filepath = 'C:\\Users\\Molta\\Documents\\cglumberjack\\dev_onboarding_auth.json'
    with open(filepath, 'w+') as f:
        f.write(r.content)
    return filepath


def get_new_developers():
    new_devs_list = []
    sheet = authorize_sheets()
    for entry in range(2, sheets.find_empty_row_in_sheet(sheet)):
        new_dev = {}
        if sheet.cell(entry, 5).value == '':
            new_dev = {
                'Email Address': sheet.cell(entry, 2).value,
                'Full Name': sheet.cell(entry,3).value,
                'Github Username': sheet.cell(entry,4).value
            }
            new_devs_list.append(new_dev)
    return new_devs_list


def mark_dev_as_onboarded(github_username):
    sheet = authorize_sheets()
    for entry in range(2, sheets.find_empty_row_in_sheet(sheet)):
        if sheet.cell(entry, 4).value == github_username:
            if sheet.cell(entry, 5).value == "Yes":
                print "Error: User already onboarded"
                return False
            elif sheet.cell(entry, 5).value != "Yes":
                print "User Found"
                sheet.update_cell(entry, 5, 'Yes')
                return True
    print "Error: Username not found"
    return False


if __name__ == '__main__':
    pass
    # mark_dev_as_onboarded('kyul')

