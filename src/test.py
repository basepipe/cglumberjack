import ftrack_api
from cglcore.config import app_config
import arrow
import datetime



task_asset = None
server_url = app_config()['project_management']['ftrack']['api']['server_url']
api_key = app_config()['project_management']['ftrack']['api']['api_key']
api_user = app_config()['project_management']['ftrack']['api']['api_user']

session = ftrack_api.Session(server_url=server_url, api_key=api_key, api_user=api_user)
project = 'cgl_testThree'
project_data = session.query('Project where status is active and name is %s' % project).first()
task = 'SJM_010_roto'
task_data = session.query('Task where name is "{0}" and project.id is "{1}"'.format(task, project_data['id'])).first()
# set description


print task_data
for k in task_data.keys():
    print k
print task_data['name']
print task_data['bid']
print task_data['end_date']

print '-----------------'
print arrow.get(28800.0)
d = datetime.timedelta(hours=8)
print d.seconds,


