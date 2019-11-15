import time
import os
from cgl.core.path import PathObject, get_start_frame
from cgl.core.util import current_user, cgl_copy, cgl_execute
from cgl.core.convert import create_hd_proxy, create_mov
proccessing_method = 'local'

# I need a system for timing all of this.
# Json file somewhere that tracks ALL calls to the _execute command.  We need to know:
# {
#     users: {
#         username: {
#             average_monthly_wait_time: '',
#             average_daily_wait_time: '',
#             date: {
#                 total_user_wait_time: '',
#                 total_submission: '',
#                 task_id: {
#                     command: '',
#                     user_start_time: '',
#                     user_end_time: '',
#                     process_start_time: '',
#                     process_end_time: ''
#                 }
#             }
#         }
#     }
# }

start_time = time.time()
# End Time (for final operation - for example if this goes to smedge or deadline)
files_ = r'D:/VFX/FRIDAY_ROOT/testco/source/cgl_plate_test/IO/CLIENT/001.000/03_2a_#####.exr'
filename = os.path.split(files_)[-1]
path_object = PathObject(files_)
new_publish = path_object.copy(scope='shots', seq='000', shot='0900', task='plate', resolution='high',
                               user=current_user(), version='000.000')
#### Running it all Locally
run_dict = cgl_copy(files_, new_publish.path_root, dest_is_folder=True, verbose=False)
print '-->>  Copied Files in %s seconds' % run_dict['artist_time']
time.sleep(4)
proxy_dict = create_hd_proxy(run_dict['output'])
print '-->>  Created hd proxies in %s seconds' % proxy_dict['artist_time']
time.sleep(4)
mov_dict = create_mov(proxy_dict['file_out'])
print '-->>  Created mov in %s seconds' % mov_dict['artist_time']
#### Running it all on Smedge
# print new_publish.path_root
# run_dict = cgl_copy(files_, new_publish.path_root, dest_is_folder=True, verbose=False, methodology='smedge')
# print '-->>  Copied Files in %s seconds' % run_dict['artist_time']
# proxy_dict = create_hd_proxy(run_dict['output'], methodology='smedge', dependent_job=run_dict['job_id'])
# print '-->>  Created hd proxies in %s seconds' % proxy_dict['artist_time']
# mov_dict = create_mov(proxy_dict['file_out'], methodology='smedge', dependent_job=proxy_dict['job_id'])
# print '-->>  Created mov in %s seconds' % mov_dict['artist_time']

# create a quicktime movie
# upload to ftrack