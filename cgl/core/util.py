import pprint
import click
import os
import glob
import json
import sys
import getpass
import time
import logging
import re
import xmltodict
from cgl.core.config import app_config

CONFIG = app_config()


def pretty(obj):
    """
    return a pretty printed representation of an object
    Args:
        obj: the object to pretty print

    Returns:
        str:

    """
    pp = pprint.PrettyPrinter(indent=4)
    return pp.pformat(obj)


def app_name(str_=None, human=False):
    """
    return the name of the application used in settings files
    Args:
        str_: the name to map from defaults sys.argv[0]
        human: a human readable string

    Returns:
        str: name of application

    """
    supported_apps = ['maya', 'nuke', 'houdini', 'unreal', 'unity']
    if str_ is None:
        str_ = sys.argv[0]

    title = os.path.basename(str_)
    if human:
        title = title.replace("_", " ")
    title, _ = os.path.splitext(title)

    if title not in supported_apps:
        title = 'standalone'

    return title


def folder_size(folder, size=0):
    """
    gets the memory size of a folder, can also take files
    :param folder:
    :param size:
    :return:
    """

    if os.path.isdir(folder):
        for d, subdir, files in os.walk(folder):
            for name in files:
                size = size + os.path.getsize('%s/%s' % (d, name))
            for subfolder in subdir:
                folder_size('%s/%s' % (d, subfolder), size)
        return '%s mb' % (size/1000000)
    else:
        return '%s mb' % (os.path.getsize(folder)/1000000)


def current_user():
    """
    find the currently logged in user
    Returns:
        str: username

    """
    return getpass.getuser().lower()


def test_string_against_rules(test_string, rule, effected_label=None):
    """
    Test for any string to see if it passes any regex "rule" from the global.yaml file.
    :param test_string: string to be tested against regex
    :param rule: regex pattern to test against
    :param effected_label: PySide Label Object to effect color of.
    :return:
    """
    regex = re.compile(r'%s' % CONFIG['paths']['rules'][rule])
    if re.findall(regex, test_string):
        if effected_label:
            effected_label.setStyleSheet("color: rgb(255, 255, 255);")
        return False
    else:
        if effected_label:
            effected_label.setStyleSheet("color: rgb(255, 50, 50);")
        return CONFIG['paths']['rules']['%s_example' % rule]


def cgl_copy(source, destination, methodology='local', verbose=False, dest_is_folder=False, test=False, job_name=''):
    """
    Catch all for any type of copy function.  Handles a list of files/folders as well as individual files.
    :param source: takes a list of files/folders, or a string represeting a file or folder
    :param destination: string, directory or filename
    :param test: if True no the function only prints what it would be copying
    :param verbose:
    :param dest_is_folder: If True the copy tool will assume that the destination string represents a folder
    :return:
    """
    from cgl.core.path import get_file_type

    run_dict = {'start_time': time.time(),
                'function': 'cgl_copy()'}
    if get_file_type(source) == 'sequence':
        dir_, file_ = os.path.split(source)
        run_dict['output'] = os.path.join(destination, file_)
        pattern = '%s*' % file_.split('###')[0]
        source = glob.glob(source)
        command = 'robocopy "%s" "%s" "%s" /NFL /NDL /NJH /NJS /nc /ns /np /MT:8' % (dir_, destination, pattern)
        temp_dict = cgl_execute(command=command, print_output=False, methodology=methodology, verbose=verbose,
                                command_name='%s:copy_sequence' % job_name)
        # return the sequence based off the folder
        run_dict['output'] = os.path.join(destination, file_)
        run_dict['job_id'] = temp_dict['job_id']
    if isinstance(source, list):
        temp_dict = copy_file_list(source, destination, methodology, verbose, dest_is_folder)
    else:
        temp_dict = cgl_copy_single(source, destination, test=False, verbose=False, dest_is_folder=dest_is_folder)
    run_dict['command'] = temp_dict['command']
    run_dict['artist_time'] = get_end_time(run_dict['start_time'])
    run_dict['end_time'] = time.time()
    return run_dict


def copy_file_list(file_list, destination, methodology, verbose, dest_is_folder=True):
    """
    this function takes a list of files and figures out the most efficient way to copy them in the following order:
    1) Are there any folders in this list?
    2) Are there file sequences in this list?
    3) Are there unique individual files in this list?
    :param file_list:
    :param destination:
    :param methodology:
    :param verbose:
    :param dest_is_folder:
    :return:
    """
    # For a First Draft cgl_copy_single works just fine for files and folders.
    # as a next step i'd like to process it so i can also identify sequences within the list.  This is tricky because
    # i have to be able to handle the instance of there's a sequence in the folder and i only want to copy certain
    # frame ranges.
    run_dict = {'start_time': time.time(),
                'function': 'cgl_copy_file_list()'}
    for f in file_list:
        cgl_copy_single(f, destination=destination, methodology=methodology, verbose=verbose,
                        dest_is_folder=dest_is_folder)
    run_dict['command'] = 'cgl_copy_file_list()'
    run_dict['artist_time'] = get_end_time(run_dict['start_time'])
    return run_dict


def cgl_copy_single(source, destination, test=False, methodology='local', verbose=False, dest_is_folder=False,
                    command_name='cgl_copy_single'):
    """
    Lumbermill Copy Function.  Built to handle any kind of copy interaction.  For example:
    copy the contents of a directory to another location:
        copy('/path/to/source/folder', '/path/to/destination/folder')
    copy one file to another location - no change in file name:
        copy('/path/to/file.ext', '/path/to/destination/folder')
    copy a file to another location - with a change in file name
        copy('/path/to/file.ext', '/path/to/destination/NewFileName.ext')
    :param source: directory path or file path
    :param destination: directory path or new directory path or new file path
    :param test: False by default, if True it simply prints the commands it's doing.
    :param methodology: how command will be executed
    :param verbose: (boolean) Toggle print statments
    :param dest_is_folder: if True the destination is a folder.
    :param command_name: this is what will be sent to the render manager.
    :return: True if successful
    """
    run_dict = {'function': 'cgl_copy_single()'}
    do_system = False
    if verbose:
        logging.info('copying %s to %s' % (source, destination))
    command = None
    if sys.platform == 'win32':
        source = source.replace('/', '\\')
        destination = destination.replace('/', '\\')
        # make sure the destination directories exist
        if dest_is_folder:
            if not os.path.exists(destination):
                os.makedirs(destination)
        else:
            directory = os.path.dirname(destination)
            if not os.path.exists(directory):
                os.makedirs(directory)
        if os.path.isdir(source):
            # what to do if we're copying a directory to another directory
            run_dict['command_type'] = 'directory to directory'
            command = 'robocopy "%s" "%s" /NFL /NDL /NJH /NJS /nc /ns /np /MT:8 /E' % (source, destination)
        else:
            dir_, file_ = os.path.split(source)
            # We are dealing with a single file.
            if dest_is_folder:
                # Destination is a Folder
                run_dict['command_type'] = 'single file to directory'
                command = 'robocopy "%s" "%s" "%s" /NFL /NDL /NJH /NJS /nc /ns /np /MT:8' % (dir_, destination, file_)
            else:
                # Destination is a file with a different name
                run_dict['command_type'] = 'file to renamed file'
                # TODO - check to ensure the files have the same extension.
                command = 'copy "%s" "%s" /Y >nul' % (source, destination)
                do_system = True
        if command:
            if test:
                print command
            else:
                run_dict['start_time'] = time.time()
                run_dict['command'] = command
                cgl_execute(command=command, print_output=False, methodology=methodology, verbose=verbose,
                            command_name=command_name, do_system=do_system)
                run_dict['artist_time'] = time.time()-run_dict['start_time']
                run_dict['end_time'] = time.time()
        return run_dict
    elif sys.platform == 'darwin':
        print 'OSX is not a supported platform'
        return False
    elif sys.platform == 'linux2':
        print 'Linux is not a supported platform'
        return False
    else:
        print '%s is not a supported platform' % sys.platform
        return False


def split_all(path):
    all_parts = []
    while 1:
        parts = os.path.split(path)
        if parts[0] == path:  # sentinel for absolute paths
            all_parts.insert(0, parts[0])
            break
        elif parts[1] == path:
            all_parts.insert(0, parts[1])
            break
        else:
            path = parts[0]
            all_parts.insert(0, parts[1])
    return all_parts


def save_json(filepath, data):
    with open(filepath, 'w') as outfile:
        json.dump(data, outfile, indent=4, sort_keys=True)


def load_json(filepath):
    with open(filepath) as jsonfile:
        data = json.load(jsonfile)
    return data


def save_xml(filepath, data):
    with open(filepath, 'w') as outfile:
        outfile.write(xmltodict.unparse(data))


def load_xml(filepath):
    with open(filepath) as xmlfile:
        docs = xmltodict.parse(xmlfile.read())
    return docs


def load_style_sheet(style_file='stylesheet.css'):
    file_ = os.path.join(__file__.split('cglumberjack')[0], 'cglumberjack', 'resources', style_file)
    f = open(file_, 'r')
    data = f.read()
    data.strip('\n')
    # path = APP_PATH.replace('\\', '/')
    # data = data.replace('<PATH>', path)
    return data


def cgl_execute(command, return_output=False, print_output=True, methodology='local', verbose=True,
                command_name='cgl_execute', do_system=False, new_window=False, **kwargs):
    # TODO - we need to make sure this command is used everywhere we're passing commands if at all possible.

    run_dict = {'command': command,
                'command_name': command_name,
                'start_time': time.time(),
                'methodology': methodology,
                'farm_processing_end': '',
                'farm_processing_time': '',
                'job_id': None}
    if methodology == 'local':
        output_values = []
        import subprocess
        if do_system:
            # TODO this requires testing, i think i've solved why this was needed, it'd ne nice to remove it.
            os.system(command)
        else:
            print('Executing Command:\n%s' % command)
            if new_window:
                subprocess.Popen(command, universal_newlines=True, creationflags=subprocess.CREATE_NEW_CONSOLE)
                # TODO - would like a way to ensure output prints to the new console as well as to our output.  For now
                # it seems like it's a one or the other scneario
            else:
                p = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)
                if return_output or print_output:
                    while True:
                        output = p.stdout.readline()
                        if output == '' and p.poll() is not None:
                            break
                        if output:
                            if print_output:
                                print output.strip()
                            output_values.append(output.strip())

        run_dict['artist_time'] = time.time() - run_dict['start_time']
        run_dict['end_time'] = time.time()
        run_dict['printout'] = output_values
        return run_dict
        # rc = p.poll()
        # if return_output:
        #     return output_values
        # else:
        #     return rc
    elif methodology == 'deadline':
        # TODO - add deadline integration
        print 'deadline not yet supported'
    elif methodology == 'smedge':
        range = '1'
        if '-Type Nuke' in command:
            smedge_command = r'%s Script %s' % (CONFIG['paths']['smedge'], command)
        else:
            environment_overrides = "CGL_PYTHON=C:\Python27;C:\Python27\Scripts;C:\Python27\Lib\site-packages;"
            if command.startswith('python'):
                command = '$(:CGL_PYTHON)\\%s' % command
            smedge_command = r'%s Script -Type Generic Script -Name %s -Range %s ' \
                             r'-Command "%s" -EnvironmentOverrides "%s"' % (CONFIG['paths']['smedge'],
                                                                            command_name, range, command,
                                                                            environment_overrides)
        for k in kwargs:
            value = kwargs[k]
            smedge_command = '%s -%s %s' % (smedge_command, k, value)
        # this needs to check for a smedge connection
        temp_dict = cgl_execute(smedge_command, methodology='local')
        run_dict['job_id'] = temp_dict['printout'][0].split('Job ID: ')[-1]
        run_dict['artist_time'] = time.time() - run_dict['start_time']
        run_dict['end_time'] = time.time()
        return run_dict


def check_for_latest_master(return_output=True, print_output=False):
    # TODO - probably need something in place to check if git is installed.
    code_root = CONFIG['paths']['code_root']
    command = 'git remote show origin'
    os.chdir(code_root)
    output = cgl_execute(command, return_output=return_output, print_output=print_output)

    for line in output:
        if 'pushes to master' in line:
            if 'up to date' in line:
                print 'cglumberjack code base up to date'
                return True
            else:
                print 'cglumberjack code base needs updated'
    return False


def update_master():
    code_root = CONFIG['paths']['code_root']
    command = 'git pull'
    os.chdir(code_root)
    cgl_execute(command)


def get_end_time(start_time):
    return time.time()-start_time


def get_job_id():
    return str(time.time()).replace('.', '')


def write_to_cgl_data(process_info):
    job_id = None
    if 'job_id' in process_info.keys():
        if process_info['job_id']:
            job_id = process_info['job_id']
        else:
            process_info['job_id'] = get_job_id()
    user = current_user()
    cgl_data = os.path.join(os.path.dirname(CONFIG['paths']['globals']), 'cgl_data.json')
    if os.path.exists(cgl_data):
        data = load_json(cgl_data)
    else:
        data = {}
    if user not in data.keys():
        data[user] = {}
    if job_id not in data[user].keys():
        data[user][process_info['job_id']] = process_info
    else:
        print '%s already exists in %s dict' % (process_info['job_id'], user)
        return
    save_json(cgl_data, data)


def edit_cgl_data(job_id, key, value=None, user=None):
    if not job_id:
        logging.info('No Job ID Defined')
        click.echo('No Job ID Defined')
        return
    if not key:
        logging.info('No Key Defined')
        click.echo('No Key Defined')
    if not value:
        value = time.time()
    if not user:
        user = current_user()
    cgl_data = os.path.join(os.path.dirname(CONFIG['paths']['globals']), 'cgl_data.json')
    if os.path.exists(cgl_data):
        data = load_json(cgl_data)
        print user, job_id, key, value
        data[user][job_id][key] = value
        save_json(cgl_data, data)
        print 'saved it probably'
    else:
        logging.info('No cgl_data.json found! Aborting')
        click.echo('No cgl_data.json found! Aborting')
        return


@click.command()
@click.option('--edit_cgl', '-e', default=False, prompt='edit cgl data file for a user, job_id, and key/value pair')
@click.option('--user', '-u', default=current_user(), prompt='File Sequence Path (file.####.ext)',
              help='Path to the Input File.  Can be Image, Image Sequence, Movie')
@click.option('--job_id', '-j', default=None,
              help='job_id object to edit')
@click.option('--key', '-k', help='key to edit')
@click.option('--value', '-v', help='value for the key')
def main(edit_cgl, user, job_id, key, value):
    if edit_cgl:
        edit_cgl_data(user, job_id, key, value)


if __name__ == '__main__':
    main()




