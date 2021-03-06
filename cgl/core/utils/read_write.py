import json
import xmltodict
import os
from zipfile import ZipFile, ZIP_DEFLATED


def unzip(zipped_file, destination, password=None):
    """

    :param zipped_file:
    :param destination:
    :param password:
    :return:
    """
    print('unzipping %s' % zipped_file)
    with ZipFile(zipped_file, 'r') as zipObj:
        zipObj.extractall(path=destination, pwd=password)
    return destination


def zip_path(source_path, zip_file):
    """
    built to handle both files and folders as "source_path"
    :param source_path:
    :param zip_file:
    :return:
    """

    if os.path.isdir(source_path):
        zipf = ZipFile(zip_file, 'w', ZIP_DEFLATED)
        zip_dir(source_path, zipf)
        zipf.close()


def zip_dir(folder_path, zip_file, password=None):
    """
    zipes a file or folder
    :param folder_path:
    :param password:
    :return:
    """
    if os.path.isdir(folder_path):
        print('directory')
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                zip_file.write(os.path.join(root, file),
                               os.path.relpath(os.path.join(root, file), os.path.join(folder_path, '..')))


def load_json(filepath):
    """
    Loads a .json file in as a dictionary
    :param filepath:
    :return:
    """
    with open(filepath) as jsonfile:
        data = json.load(jsonfile)
    return data


def save_json(filepath, data):
    """
    Saves a Dictionary as a .json file.
    :param filepath:
    :param data: dictionary
    :return:
    """
    with open(filepath, 'w') as outfile:
        json.dump(data, outfile, indent=4, sort_keys=True)


def save_xml(filepath, data):
    """
    saves a dictionary as an xml
    :param filepath:
    :param data:
    :return:
    """
    with open(filepath, 'w') as outfile:
        outfile.write(xmltodict.unparse(data))


def load_xml(filepath):
    """
    loads an xml as a dictionary
    :param filepath:
    :return:
    """
    with open(filepath) as xmlfile:
        docs = xmltodict.parse(xmlfile.read())
    return docs


def load_style_sheet(style_file='stylesheet.css'):
    """
    Loads the main style sheet for cglumberjack.
    :param style_file:
    :return:
    """
    file_ = os.path.join(__file__.split('cglumberjack')[0], 'cglumberjack', 'resources', style_file)
    f = open(file_, 'r')
    data = f.read()
    data.strip('\n')
    return data


def load_text_file(file_path):
    file_obj = open(file_path, "r")
    lines = file_obj.readlines()
    file_obj.close()
    return lines


def save_text_lines(text_array, file_path):
    """
    this expects to get typical text that would print normally.
    :param text_to_save:
    :param file_path:
    :return:
    """
    file_object = open(file_path, "w")
    file_object.writelines(text_array)
    file_object.close()

