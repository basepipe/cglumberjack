# import logging
# import json
# from cglcore.config import app_config
# import ftrack_api
from cglcore.path import PathObject, prep_seq_delimiter
# from plugins.project_management.ftrack.main import ProjectManagementData
# import datetime
# from cglcore.convert import _execute, create_proxy, create_hd_proxy, create_mov, create_gif_proxy, make_movie_thumb
from cglcore.path import lj_list_dir
import os


seq = r'D:\VFX\testoby\testco\source\cgl_unittest\shots\010\0100\plate\system\000.001\high'

sequence = lj_list_dir(seq, return_sequences=True)
seq2, frange = sequence[0].split()
path = os.path.join(seq, seq2)
ftrack_seq = '%s [%s]' % (prep_seq_delimiter(path, '%'), frange)

#path_object.set_attr(filename=sequence[0].split()[0])
# proxy = create_proxy(os.path.join(path_object.path_root, sequence[0].split(' ')[0]))
# hd_proxy = create_hd_proxy(os.path.join(path_object.path_root, sequence[0].split(' ')[0]))
# mov = create_mov(hd_proxy, project_management='ftrack')
# create_mov(seq, project_management='ftrack')






