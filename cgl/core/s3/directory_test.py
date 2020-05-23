from __future__ import print_function
from s3_directory import get_file_url, get_url, get_zip, launch_site, send_mail
import os


os.environ['AWS_ACCESS_KEY_ID'] = "AKIAIT4HBNN4BK4SKIRA"
os.environ['AWS_SECRET_ACCESS_KEY'] = "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"

bucket = 'cgl-dev-test-storage'

#print(get_url(bucket, "dave"))
print('mri bundle')
print(get_file_url(bucket, r"render/torporHabitat/assets/Environment/torporHabitat/bndl/publish/007.000/high/mri_delivery/magic_button_torpor_asset_bundle"))
print('executable: ')
print(get_file_url(bucket, r"render/torporHabitat/assets/Environment/torporHabitat/bndl/publish/007.000/high/mri_delivery/magic_button_torpor_build.zip"))
# print(get_zip(r"render/torporHabitat/assets/Environment/torporHabitat/bndl/publish/007.000/high/mri_delivery", bucket, 'shaun'))

#send_mail("jcfriedman95@gmail.com", "dave", bucket)

#launch_site()