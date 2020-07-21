import http.client
import urllib
import requests


def url_exists(url):
    """
    Checks to see if the given url exists
    :param url: url address
    :return:
    """
    try:
        request = requests.get(url)
        if request.status_code == 200:
            print('Web site exists')
            return True
        else:
            print("Website returned response code: {code}".format(code=request.status_code))
            return False
    except ConnectionError:
        print('Web site does not exist')
        return False


def download_url(url, destination_file):
    """
    Downloads the given file from url to destination file path.
    :param url: url location of a file on the web
    :param destination_file: file to be created
    :return:
    """
    r = requests.get(url, allow_redirects=True)
    with open(destination_file, 'w+') as f:
        f.write(r.content)