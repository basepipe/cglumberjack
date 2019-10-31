from cglcore.config import app_config
import ftrack_api

server_url = app_config()['project_management']['ftrack']['api']['server_url']
api_key = app_config()['project_management']['ftrack']['api']['api_key']
api_user = app_config()['project_management']['ftrack']['api']['api_user']

print server_url, api_key, api_user

ftrack = ftrack_api.Session(server_url=server_url, api_key=api_key, api_user=api_user)
task_id = '5f3c64ce-0784-4f2e-8f4f-d6c828d4197d'
# task_id = 'b55e4628-f5b4-4855-b521-b985a2bb678a'

result = ftrack.query('Task where id is "%s" ' % task_id)

for task in result:
    print task['timelogs'][0]['start']
    new_log = ftrack.create('Timelog', {"user_id": "bcdf57b0-acc6-11e1-a554-f23c91df1211", "duration": 10800.0})
    task['timelogs'].append(new_log)
    # ftrack.commit()


# print result[0].__dict__

# how can i print all the attrs in this timelog?
# how do i create a timelog object?  what attrs are needed?

