import shutil
import os
import time
import sys


def shutil_copy_test(from_dir, to_dir):
    files = os.listdir(from_dir)
    start_time = time.time()
    for each in files:
        from_file = os.path.join(from_dir, each)
        to_file = os.path.join(to_dir, each)
        shutil.copy(from_file, to_file)
    print('Copied %s files with shutil.copy in %s' % (len(files), (time.time()-start_time)))

    # clean up the operation
    for f in files:
        to_file = os.path.join(to_dir, f)
        os.remove(to_file)


def shutil_copy2_test(from_path, to_path):
    files = os.listdir(from_path)
    start_time = time.time()
    for each in files:
        from_file = os.path.join(from_path, each)
        to_file = os.path.join(to_dir, each)
        shutil.copy2(from_file, to_file)
    print('Copied %s files with shutil.copy2 in %s' % (len(files), (time.time()-start_time)))

    for f in files:
        to_file = os.path.join(to_dir, f)
        os.remove(to_file)


def xcopy_test(from_path, to_path):
    files = os.listdir(from_path)
    from_path = r'"%s"' % from_path
    to_path = r'"%s"' % to_path
    command = 'xcopy %s %s /i /j /q' % (from_path, to_path)
    start_time = time.time()
    os.system(command)
    print('Copied %s files with xcopy in %s' % (len(files), (time.time() - start_time)))
    for f in files:
        to_file = os.path.join(to_dir, f)
        os.remove(to_file)


def robocopy_test(from_path, to_path):
    files = os.listdir(from_path)
    from_path = r'"%s"' % from_path
    to_path = r'"%s"' % to_path
    # robocopy command - all these flags are needed to avoid printouts and save time.
    command = 'robocopy "%s" "%s" /NFL /NDL /NJH /NJS /nc /ns /np /MT:8' % (from_path, to_path)
    start_time = time.time()
    os.system(command)
    print('Copied %s files with robocopy in %s' % (len(files), (time.time() - start_time)))
    # for f in files:
    #     to_file = os.path.join(to_dir, f)
    #     os.remove(to_file)


def copy(source, destination, test=False, verbose=True):
    """
    Lumbermill Copy Function.  Built to handle any kind of copy interaction.  For example:
    copy the contents of a directory to another location: copy('/path/to/source/folder', '/path/to/destination/folder')
    copy one file to another location - no change in file name ('/path/to/file.ext', '/path/to/destination/folder')
    copy a file to another location - with a change in file name ('/path/to/file.ext', '/path/to/destination/NewFileName.ext')
    :param source: directory path or file path
    :param destination: directory path or new directory path or new file path
    :param test: False by default, if True it simply prints the commands it's doing.
    :return: True if successful
    """
    command = None
    if sys.platform == 'win32':
        if os.path.isdir(source):
            files = os.listdir(source)
            # what to do if we're copying a directory to another directory
            command = 'robocopy "%s" "%s" /NFL /NDL /NJH /NJS /nc /ns /np /MT:8' % (source, destination)
        else:
            dir_, file_ = os.path.split(source)
            files = [file_]
            # We are dealing with a single file.
            if os.path.isdir(destination):
                # Destination is a Folder
                command = 'robocopy "%s" "%s" "%s" /NFL /NDL /NJH /NJS /nc /ns /np /MT:8' % (dir_, destination, file_)
            else:
                # Destination is a file with a different name
                if not os.path.exists(os.path.dirname(destination)):
                    os.makedirs(os.path.dirname(destination))
                # TODO - check to ensure the files have the same extension.
                command = 'copy "%s" "%s" /Y >nul' % (source, destination)
        if command:
            start_time = time.time()
            if test:
                print(command)
            else:
                print(command)
                os.system(command)
            if verbose:
                print('Lumbermill Copied %s file(s) in %s seconds' % (len(files), (time.time() - start_time)))
            return True
        else:
            return False
    else:
        print('%s is not a supported platform' % sys.platform)
        return False


# shutil_copy_test(from_dir, to_dir)
# xcopy_test(from_dir, to_dir)
# robocopy_test(from_dir, to_dir)

# shutil_copy2_test(from_dir, to_dir)
to_dir = r'Z:\COMPANIES\loneCoconut\source\cgl_unitTestC\IO\CLIENT\000.000\FULLRES'
from_dir = r'Z:\02_SYSTEMS\TEST PROJECTS\CDL_0450\MEDIA\Read1\v001\FULLRES'
# copy(from_dir, to_dir, test=False)
from_file = r'Z:\02_SYSTEMS\TEST PROJECTS\CDL_0450\MEDIA\Read1\v001\FULLRES\A101C013_181204_R2GR.00248441.exr'
# copy(from_file, to_dir, test=False)
to_file = r'Z:\COMPANIES\loneCoconut\source\cgl_unitTestC\IO\CLIENT\000.000\TEST\sally.exr'
# copy(from_file, to_file, test=False)
# cgl_copy(from_dir, to_dir)



