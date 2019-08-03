import os
import json
from cglcore.path import PathObject, CreateProductionData, lj_list_dir
from cglcore.convert import _execute, create_proxy, create_hd_proxy, create_mov, create_gif_proxy, create_movie_thumb
from plugins.project_management.ftrack.main import ProjectManagementData


# ############################################################
#   TESTS FOR ASSET SPECIFIC/ FILE SPECIFIC STUFF
# ############################################################

# EXR SEQUENCE
# TODO - how cool would it be to have a GUI that allowed for different kinds of testing!?!?

# command = r'wget -P %s -r -np -nH -nd -e robots=off https://media.xiph.org/tearsofsteel/linear-exr/03_2a/' % path_object.path_root
#_execute(command)

path_object = PathObject(r'D:/VFX/testoby/testco/source/cgl_unittest/shots/010/0100/plate/system/000.001/high')
print path_object.path_root

sequence = lj_list_dir(path_object.path_root, return_sequences=True)
path_object.set_attr(filename=sequence[0].split()[0])
proxy = create_proxy(os.path.join(path_object.path_root, sequence[0].split(' ')[0]), project_management='ftrack')
# proxy = r'D:/VFX/testoby/testco/source/cgl_unittest/shots/010/0100/plate/system/000.001/highProxy/03_2a_#####.jpg'
proxy_object = PathObject(proxy)
hd_proxy = create_hd_proxy(os.path.join(path_object.path_root, sequence[0].split(' ')[0]), project_management='ftrack')
# hd_proxy = r'D:/VFX/testoby/testco/source/cgl_unittest/shots/010/0100/plate/system/000.001/hdProxy/03_2a_#####.jpg'
mov = create_mov(hd_proxy, project_management='ftrack')