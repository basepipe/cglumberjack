
import re
from cglcore.config import app_config

seq_rules = app_config()['rules']['general']['file_sequence']['regex']
regex = re.compile("\\.[0-9]+\\.")
path = r'prop_ball_mdl.0123123.mb'



def seq_from_file(basename):
    numbers = re.search(regex, basename)
    numbers = numbers.group(0).replace('.', '')
    string = '#' * int(len(numbers))
    string = '.%s.' % string
    this = re.sub(regex, string, basename)
    return this

print seq_from_file(path)
