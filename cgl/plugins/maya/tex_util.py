import os
from cgl.core.utils.general import cgl_execute
from cgl.core.path import get_file_type
from cgl.core.config import app_config

CONFIG = app_config()
EXT_MAP = CONFIG['ext_map']


def tx_make(directory):
    """
    parses a directory and creates .tx files for everything in it.
    :param directory:
    :return:
    """
    directory = (os.path.dirname(directory))
    list_of_files = list()
    file_type = None
    for (dirpath, dirnames, filenames) in os.walk(directory):
        list_of_files += [os.path.join(dirpath, file) for file in filenames]
    for f in list_of_files:
        file, ext = os.path.splitext(f)
        try:
            file_type = EXT_MAP[ext]
        except KeyError:
            pass
        if file_type == 'image':
            output = '{}.tx'.format(file)
            command = '%s %s -v -u -oiio -o %s' % (CONFIG['paths']['maketx'], f, output)
            cgl_execute(command)

