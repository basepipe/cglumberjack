import logging
import json
from cglcore.config import app_config
import ftrack_api
from cglcore.path import PathObject, prep_seq_delimiter
from plugins.project_management.ftrack.main import ProjectManagementData
import datetime
from cglcore.convert import _execute, create_proxy, create_hd_proxy, create_mov, create_gif_proxy, make_movie_thumb
from cglcore.path import lj_list_dir
import os

session = ftrack_api.Session(server_url="https://lone-coconut.ftrackapp.com",
                             api_key="ZTU3ZDZkMDUtMWI3OS00ZWU1LWE2NGItZGJiYmQyOGExZTZiOjoyMTUyYmI2ZC1kNzk2LTRmZmUtYjUzZS0wMjBiMzA5MGZhMDA",
                             api_user="LoneCoconutMail@gmail.com")
project_data = session.query('Project where status is active and name is %s' % 'cgl_unittest').first()
seqs = session.query('Sequence where name is "{0}" and project.id is "{1}"'.format('060', project_data['id'])).first()
print seqs


# for each in seqs:
#     if each['name'] == self.seq:
#         logging.info('Found %s' % each['name'])
#         self.seq_data = each
#         return each







