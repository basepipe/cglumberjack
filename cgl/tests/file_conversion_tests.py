from cgl.core.path import PathObject

# hdri sequence conversion
exr_sequence_hash = r'D:/VFX/FRIDAY_ROOT/cglumberjack/render/cgl_testProjectJ/shots/080/000/plate/publish/000.000/high/03_2a_#####.exr'
exr_sequence_percentage = r'D:/VFX/FRIDAY_ROOT/cglumberjack/render/cgl_testProjectJ/shots/080/000/plate/publish/000.000/high/03_2a_%05d.exr'
exr_sequence_star = r'D:/VFX/FRIDAY_ROOT/cglumberjack/render/cgl_testProjectJ/shots/080/000/plate/publish/000.000/high/03_2a_*.exr'

non_exist = r'D:/VFX/FRIDAY_ROOT/cglumberjack/render/cgl_testProjectJ/shots/080/000/plate/publish/000.000/1920x1080/03_2a_#####.exr'


# sequence = Sequence(non_exist)
# sequence.print_info()
# sequence = Sequence(exr_sequence_percentage)
# sequence.print_info()
# sequence = Sequence(exr_sequence_star)
# sequence.print_info()

# print '00000000000000000000'
# path_object = PathObject(exr_sequence_hash)
# print path_object.preview_path
# print path_object.thumb_path
# path_object.make_preview()
# path_object.upload_review()
# path_object.make_proxy()
#path_object.make_quicktime()

#path_object.make_thumbnail()
#path_object.upload_to_project_management()

# exr_sequence_hash = r'D:/VFX/FRIDAY_ROOT/cglumberjack/render/cgl_testProjectJ/shots/080/000/plate/publish/000.000/high/03_2a_#####.exr'
# path_object = PathObject(exr_sequence_hash)
# path_object.copy_path()
#process_info = path_object.make_preview()
#path_object.upload_review(job_id=process_info['job_id'])
import subprocess
import os
source = r"C:\Users\tmiko\PycharmProjects\cglumberjack\cgl\plugins\nuke\templates\default.nk"
dest = r"D:\VFX\FRIDAY_ROOT\cglumberjack\source\cgl_testProjectJ\shots\080\900\comp\tmiko\000.000\high\080_900_comp.nk"
command = 'copy %s %s /Y >nul' % (source, dest)
os.system(command)
list = ['copy', r'C:\\Users\\tmiko\\PycharmProjects\\cglumberjack\\cgl\\plugins\\nuke\\templates\\default.nk', r'D:\\VFX\\FRIDAY_ROOT\\cglumberjack\\source\\cgl_testProjectJ\\shots\\080\\0200\\comp\\tmiko\\000.000\\high\\080_0200_comp.nk', '/Y >nul']
command = list
p = subprocess.Popen(command)
