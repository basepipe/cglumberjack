from cgl.core.convert import convert_to_mp4, create_prores_mov
from cgl.core.utils.general import cgl_execute
from cgl.plugins.aws import s3
import os
from cgl.core.path import PathObject, CreateProductionData
# from robogary.src.plugins.editorial.timeline import editorial_from_template


path_ = r'Y:/CGLUMBERJACK/COMPANIES/forge/source/vr_scout/shots/010/0021/cam/tmikota/000.000/high/' \
        r'2020_10_21_10_55_36.mkv'

# create web preview
if path_.endswith('mkv'):
        mp4_file = path_.replace('mkv', 'mp4')
        mp4_file = PathObject(mp4_file).copy(context='render').path_root
        file_in = mp4_file
        check_mkv = r"ffmpeg -i {} -codec copy {}".format(path_, mp4_file)
        output = cgl_execute(check_mkv)
else:
        mp4_output = convert_to_mp4(filein=file_in, audio_only=True, processing_method='smedge')
        mp4_file = mp4_output['file_out']
        file_in = mp4_output['file_out']


# create audio preview
audio_output = convert_to_mp4(filein=mp4_file, audio_only=True, processing_method='smedge')
print(audio_output['job_id'])
print(audio_output['file_out'])
#
# create prores file
prores_output = create_prores_mov(file_in, processing_method='smedge')
#
# Create The Transcript
audio_file = audio_output['file_out']
transcript_file = audio_file.replace('.mp4', '_transcript.json')
# transcript_file = PathObject(file_in).copy(task='paperedit', filename='transcript.json').path_root
template_info = s3.upload_and_transcribe_audio(audio_file, transcript_file, processing_method='smedge',
                                               dependent_job=audio_output['job_id'])

# print(template_info['job_id']
# print(template_info['file_out']
# #
# # Create the Editorial File
# template_file = PathObject(file_in).copy(task='template', filename='template.xml').path_root
# CreateProductionData(os.path.dirname(template_file))
# editorial_from_template(clip=output['file_out'], title='Boy Band II', secondary_title="Quest for the Best",
#                         template='gen', file_out=template_file,
#                         processing_method='smedge',
#                         dependent_job=template_info['job_id'])
#
#
