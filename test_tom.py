from cgl.core.convert import convert_to_mp4, create_prores_mov
from plugins.aws import s3
import os
from cgl.core.path import PathObject, CreateProductionData
from robogary.src.plugins.editorial.timeline import editorial_from_template


def create_prores_resolution(input_file, resolution, processing_method='smedge', job_id=None):
    d_ = {'proxy': 0,
          'low': 1,
          'standard': 2,
          'high': 3
          }
    filename = os.path.basename(input_file)
    file_, ext = os.path.splitext(filename)
    path_object = PathObject(input_file).copy(resolution=resolution, filename='%s.mov' % file_, ext='mov',
                                              context='render')
    CreateProductionData(os.path.dirname(path_object.path_root))
    process_info = create_prores_mov(input_file=input_file, output_file=path_object.path_root, quality=d_[resolution],
                                     new_window=False, processing_method=processing_method, dependent_job=job_id)
    return process_info

# Create the Audio File
file_in = r'F:/FSU-CMPA/COMPANIES/VFX/render/tuesdayTest/assets/Tutorials/lumbermill_intro/video/publish/000.000/high/intro_to_lumbermill.mkv'
output = convert_to_mp4(filein=file_in, audio_only=True, processing_method='smedge')
print output['job_id']
print output['file_out']
# Create The Transcript
t_file_name = os.path.basename(file_in).replace('.mkv', '.json')
transcript_file = PathObject(file_in).copy(task='paperedit', filename='transcript.json').path_root
CreateProductionData(os.path.dirname(transcript_file))
template_info = s3.upload_and_transcribe_audio(output['file_out'], transcript_file, processing_method='smedge', dependent_job=output['job_id'])
print template_info['job_id']
print template_info['file_out']
# Create the ProRes proxy
proxy_info = create_prores_resolution(file_in, 'proxy')
# Create the ProRes proxy
standard_info = create_prores_resolution(file_in, 'standard')
# Create the Editorial File
print standard_info['file_out']
template_file = PathObject(file_in).copy(task='template', filename='template.xml').path_root
CreateProductionData(os.path.dirname(template_file))
editorial_from_template(clip=standard_info['file_out'], title='Boy Band II', secondary_title="Quest for the Best", template='gen',
                        file_out=template_file, processing_method='smedge', dependent_job=standard_info['job_id'])


