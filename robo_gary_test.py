from cgl.core.convert import convert_to_mp4, create_prores_mov
from cgl.plugins.aws import s3
import os
from cgl.core.path import PathObject, CreateProductionData
# from robogary.src.plugins.editorial.timeline import editorial_from_template

PROC_METHOD = 'local'
# Create the Audio File
file_in = r'C:\Users\VP01\Videos\test_video.mkv'
output = convert_to_mp4(filein=file_in, audio_only=True, processing_method=PROC_METHOD)
print(output['job_id'])
print(output['file_out'])
#
# # Create the Video File
output = convert_to_mp4(filein=file_in, processing_method=PROC_METHOD, dependent_job=None)
prores_output = create_prores_mov(file_in, processing_method=PROC_METHOD, dependent_job=None)
# print(output['job_id'])
# print(output['file_out'])
# print(prores_output['job_id'])
# print(prores_output['file_out'])
#
# # Create The Transcript
t_file_name = os.path.basename(file_in).replace('.mkv', '.json')
# transcript_file = PathObject(file_in).copy(task='paperedit', filename='transcript.json').path_root
# CreateProductionData(os.path.dirname(transcript_file))
template_info = s3.upload_and_transcribe_audio(output['file_out'], t_file_name, processing_method=PROC_METHOD,
                                               dependent_job=output['job_id'])
# # print(template_info['job_id']
# # print(template_info['file_out']
# #
# # Create the Editorial File
# template_file = PathObject(file_in).copy(task='template', filename='template.xml').path_root
# CreateProductionData(os.path.dirname(template_file))
# editorial_from_template(clip=output['file_out'], title='Boy Band II', secondary_title="Quest for the Best",
#                         template='gen', file_out=template_file,
#                         processing_method=PROC_METHOD,
#                         dependent_job=template_info['job_id'])


