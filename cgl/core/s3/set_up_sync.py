import os
from syncs3 import list_bucket_objects, create_versioned_bucket, sync_bucket
from core.config import app_config

keys = app_config()['lumberjack_sync']
root_folder = app_config()['paths']['root']

os.environ['AWS_ACCESS_KEY_ID'] = keys['AWS_ACCESS_KEY_ID']
os.environ['AWS_SECRET_ACCESS_KEY'] = keys['AWS_SECRET_ACCESS_KEY']

# is there any reason not to set up a bucket for each project?
# i need to be shown how the web interface would work for a client that wants to upload something by hand

bucket = 'dev-test-storage'
# root_folder = r'Z:\VFX'
list_bucket_objects()

create_versioned_bucket(bucket_name="cgl-%s" % bucket)

# list_bucket_objects()

# eventually we'll want to set this to a root within the globals and use globals for all these variables.
if os.path.exists(root_folder):
    sync_bucket(delete=False, pull=True, folder=root_folder, bucket="s3://cgl-%s" % bucket)
    print('Sync Complete')
else:
    print('Can not find Root Folder %s' % root_folder)
# list_bucket_objects(bucket_name="cgl-your-new-bucket-name")