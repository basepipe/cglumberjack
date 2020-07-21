import ftrack_api


session = ftrack_api.Session(server_url="https://lone-coconut.ftrackapp.com",
                             api_key="ZTU3ZDZkMDUtMWI3OS00ZWU1LWE2NGItZGJiYmQyOGExZTZiOjoyMTUyYmI2ZC1kNzk2LTRmZmUtYjUzZS0wMjBiMzA5MGZhMDA",
                             api_user="LoneCoconutMail@gmail.com")
project_data = session.query('Project where status is active and name is %s' % 'cgl_unittest').first()
seqs = session.query('Sequence where name is "{0}" and project.id is "{1}"'.format('060', project_data['id'])).first()
print(seqs)







