from cglcore.path import create_previews
import ftrack_api
from cglcore.config import app_config

server_url = app_config()['project_management']['ftrack']['api']['server_url']
api_key = app_config()['project_management']['ftrack']['api']['api_key']
api_user = app_config()['project_management']['ftrack']['api']['api_user']

session = ftrack_api.Session(server_url=server_url, api_key=api_key, api_user=api_user, auto_connect_event_hub=True)
server_location = session.query('Location where name is "ftrack.server"').first()
path = r'D:\VFX\FRIDAY_ROOT\testco\render\cgl_unittest\shots\020\0100\plate\tmiko\000.001\high\Capture.PNG'
preview_path = r'D:\VFX\FRIDAY_ROOT\testco\render\cgl_unittest\shots\020\0200\plate\tmiko\000.001\high\.preview\Capture.jpg'
thumb_path = r'D:\VFX\FRIDAY_ROOT\testco\render\cgl_unittest\shots\020\0200\plate\tmiko\000.001\high\.thumb\Capture.jpg'

task = session.get('Task', 'dfa65df9-d955-4d4e-9658-e2bf8c11a10c')
asset_parent = task['parent']
asset = session.query('Asset where name is "{0}" and parent.id is "{1}"'.format(task['name'], asset_parent['id'])).one()
asset_type = session.query('AssetType where name is "Geometry"').one()
if not asset:
    asset = session.create('Asset', {
        'name': task['name'],
        'type': asset_type,
        'parent': asset_parent
    })
    session.commit()

asset_version = session.query('AssetVersion where asset_id is %s' % asset['id']).first()

asset_version = session.create('AssetVersion', {
    'asset': asset,
    'task': task,
    'version': float(12.5)
})
print asset_version['id'], 'asset_version_id'

session.commit()

asset_version.create_component(path=preview_path,
                               data={
                                    'name': 'ftrackreview-image',
                               },
                               location=server_location
                               )
asset_version.create_component(path=thumb_path,
                               data={
                                    'name': 'thumbnail'
                               },
                               location=server_location
                               )

session.commit()
