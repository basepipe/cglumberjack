import httplib
import urllib2
import requests


def url_exists(url):
    """
    Checks to see if the given url exists
    :param url: url address
    :return:
    """
    try:
        u = urllib2.urlopen(url)
    except urllib2.HTTPError:
        return False
    if u.code == 200:
        return True
    else:
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