import os


def fix_repo(root_directory):
    """
    gives you a print out of commands you can run to make a piece of code python 3 compliant.
    :param root_directory:
    :return:
    """
    for root, dirs, files in os.walk(root_directory):
        for name in files:
            if name.endswith('.py'):
                if '__init__' not in name:
                    if 'Qt' not in name:
                        command = r'python C:\Python38\Tools\scripts\2to3.py -w {}'.format(os.path.join(root, name))
                        print(command)
                        #os.system(command)


fix_repo(r'C:\Users\tmiko\PycharmProjects\pipe_builder\src')
