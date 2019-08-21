from plugins.project_management.ftrack.main import find_user_assignments
from cglcore.config import app_config
import ftrack_api



server_url = app_config()['project_management']['ftrack']['api']['server_url']
api_key = app_config()['project_management']['ftrack']['api']['api_key']
api_user = app_config()['project_management']['ftrack']['api']['api_user']
session = ftrack_api.Session(server_url=server_url, api_key=api_key, api_user=api_user)
project_name = 'cgl_fritest'
user = 'lonecoconutmail@gmail.com'
project_data = session.query('Project where status is active and name is %s' % project_name).first()
user_data = session.query('User where username is "{}"'.format(user)).first()
project_tasks = session.query('select name, status.name, assignments.resource from Task where project.id is %s' % project_data['id'])
# session.populate(project_tasks, 'name,status.name,assignments.resource')
for p in project_tasks:
    for i, each in enumerate(p['assignments']):
        if p['assignments'][i]['resource'] == user_data:
            if p['parent']:
                if 'AssetBuild' in str(type(p['parent'])):
                    print p['parent'], 'is AssetBuild'

session.close()

# assignments = ProjectManagementData().find_user_assignments('lonecoconutmail@gmail.com')
# data = []
# for a in assignments:
#     shot = a['context']['parent']['name']
#     task = a['context']['name']
#     status = a['context']['status']['name']
#     print shot, task, status
#     data.append(['seq', shot, 'path goes here', 'Due Date', status, task])
