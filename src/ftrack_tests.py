import logging
import json
from cglcore.config import app_config
import ftrack_api
from cglcore.path import PathObject
from plugins.project_management.ftrack.main import ProjectManagementData
import datetime

session = ftrack_api.Session(server_url="https://lone-coconut.ftrackapp.com",
                             api_key="ZTU3ZDZkMDUtMWI3OS00ZWU1LWE2NGItZGJiYmQyOGExZTZiOjoyMTUyYmI2ZC1kNzk2LTRmZmUtYjUzZS0wMjBiMzA5MGZhMDA",
                             api_user="LoneCoconutMail@gmail.com")

project_data = session.query('Project where status is active and name is %s' % 'cgl_unittest').first()
review_session = session.create('ReviewSession', {
    'name': 'Dailies %s' % datetime.date.today(),
    'description': 'Review Session For Todays Date',
    'project': project_data
})
print review_session['project']['name']

# TODO - how do i create a web link to this review session?
# TODO - how do i create a web link to specific assets?
# TODO - how do i create a web link to a project?

#
#
# asset_version = session.query('AssetVersion where id is %s' % 'a49ad915-3377-4e97-be77-9c5ae3212d5f').one()
# server_location = session.query('Location where name is "ftrack.server"').one()
# Why does this not work? asset_version = session.query('AssetVersion', 'a49ad915-3377-4e97-be77-9c5ae3212d5f')
#
# mov = r'D:/VFX/testoby/testco/source/cgl_unittest/shots/000/0000/plate/system/000.001/hdProxy/03_2a_.mp4'
# review_obj = PathObject(mov)
# metadata = {'frameIn': 1001,
#             'frameOut': 1020,
#             'frameRate': 24
#             }
# ProjectManagementData(path_object=review_obj).create_project_management_data(review=True, metadata=metadata)
