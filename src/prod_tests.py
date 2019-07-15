import os
import json
from cglcore.path import PathObject, CreateProductionData, lj_list_dir
from cglcore.convert import _execute, create_proxy, create_hd_proxy, create_mov, create_gif_proxy, make_movie_thumb
from plugins.project_management.ftrack.main import ProjectManagementData

proj_man = 'ftrack'
# Create a Company
d = {'company': 'testco'}
path_object = PathObject(d)
print path_object.path_root
CreateProductionData(path_object, project_management=proj_man)

# Create A Project
path_object.set_attr(context='source')
path_object.set_attr(project='cgl_unittest')
print path_object.path_root
CreateProductionData(path_object, project_management=proj_man)
#####################################
# Create a Shot
#####################################

path_object.set_attr(scope='shots')
path_object.set_attr(seq='000')
path_object.set_attr(shot='0000')
print path_object.path_root
CreateProductionData(path_object, project_management=proj_man)

    # Create a Plate Task
path_object.set_attr(task='plate')
print path_object.path_root
CreateProductionData(path_object, project_management=proj_man)

path_object.set_attr(user='system')
path_object.set_attr(version='000.001')
path_object.set_attr(resolution='high')
print path_object.path_root
CreateProductionData(path_object, project_management='lumbermill')

# download some exr files that we will use for other purposes.
#command = r'wget -P %s -r -np -nH -nd -e robots=off https://media.xiph.org/tearsofsteel/linear-exr/03_2a/' % path_object.path_root
#_execute(command)

# Create a high res proxy of the plate
sequence = lj_list_dir(path_object.path_root)
proxy = create_proxy(os.path.join(path_object.path_root, sequence[0].split(' ')[0]))
hd_proxy = create_hd_proxy(os.path.join(path_object.path_root, sequence[0].split(' ')[0]))
mov = create_mov(hd_proxy)
# Create an Ftrack Review for this
review_obj = PathObject(mov)
metadata = {'frameIn': 1001,
            'frameOut': 1020,
            'frameRate': 24
            }
ProjectManagementData(path_object=review_obj).create_project_management_data(review=True, metadata=metadata)


# from cglcore.config import app_config
# import ftrack_api
# session = ftrack_api.Session(server_url=app_config()['project_management']['ftrack']['api']['server_url'],
#                                          api_key=app_config()['project_management']['ftrack']['api']['api_key'],
#                                          api_user=app_config()['project_management']['ftrack']['api']['api_user'])
#
# version = session.query('AssetVersion', 'SOME-ID')
# server_location = session.query('Location where name is "ftrack.server"').one()
# component = version.create_component(
#     path=mov,
#     data={
#         'name': 'ftrackreview-mp4'
#     },
#     location=server_location
# )
# # Meta data needs to contain *frameIn*, *frameOut* and *frameRate*.
# component['metadata']['ftr_meta'] = json.dumps({
#     'frameIn': 1001,
#     'frameOut': 1020,
#     'frameRate': 24
# })
#
# component.session.commit()

