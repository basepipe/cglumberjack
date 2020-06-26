import logging
import os
import re
import click
from cgl.core.config import app_config
from cgl.core.utils.general import cgl_execute, write_to_cgl_data

CONFIG = app_config()
PATHS = CONFIG['paths']
PADDING = CONFIG['default']['padding']
settings = CONFIG['default']
thumb_res = settings['resolution']['thumb']
frame_rate = settings['frame_rate']
ext_map = CONFIG['ext_map']
PROJ_MANAGEMENT = CONFIG['account_info']['project_management']

OPTIONS = {'320p': ['180k', '360k', '-1:320'],
           '360p': ['300k', '600k', '-1:360'],
           '480p': ['500k', '1000k', '-1:480'],
           '576p': ['850k', '1700k', '-1:576'],
           '720p': ['1000k', '2000k', '-1:720'],
           '1080p': ['1000k', '2000k', '-1:1080']}


def create_proxy_sequence(input_sequence, output_sequence, width='1920', height='1080', do_height=False,
                          processing_method='local', dependent_job=None, copy_input_padding=True,
                          command_name='create_proxy_sequence()', new_window=False, ext=None):
    """
    Create a proxy jpeg sequence in sRGB color space from the given input sequence.
    :param input_sequence: input sequence string, formatted with (#, %04d, *)
    :param output_sequence: output sequence string, formatted with (####, %04d, *)
    :param width: width in pixels
    :param height: height in pixels
    :param do_height: this is when you want to specifically use both parts of the width/height.
    y default we only use width and scale from there.
    :param processing_method: how will this be processed? (local, smedge, deadline)
    :param dependent_job: job_id of any dependencies
    :param copy_input_padding: if True use the same padding as the input file,  if False, use studio wide padding setting
    :param command_name: this is the command name that will be sent to the render farm
    :param new_window: Puts the processing of the job into a new shell
    :param ext: if none i'll use what's in the output.
    :return:
    """
    from cgl.core.path import Sequence, PathObject
    if ' ' in input_sequence:
        input_sequence, frange = input_sequence.split(' ')
    input_sequence.replace('/', '\\')
    input_ = Sequence(input_sequence)
    if not input_.is_valid_sequence():
        logging.error('%s is not a valid sequence' % input_sequence)
    filein = input_.star_sequence
    if copy_input_padding:
        padding = input_.padding
    else:
        padding = PADDING
    output_sequence = output_sequence.replace('/', '\\')
    output_ = Sequence(output_sequence, padding=padding)

    if not output_.is_valid_sequence():
        logging.error('%s is not a valid sequence' % output_sequence)
    fileout = output_.num_sequence
    out_dir = os.path.dirname(fileout)
    out_obj = PathObject(out_dir)
    if out_obj.context == 'source':
        out_obj.set_attr(context='render')
    else:
        out_obj.set_attr(context='source')
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)
    if not os.path.exists(out_obj.path_root):
        os.makedirs(out_obj.path_root)
    process_info = None

    if do_height:
        res = 'x%s' % height
    else:
        res = width
    start_frame = input_.start_frame

    if processing_method == 'smedge':
        pyfile = '%s.py' % os.path.splitext(__file__)[0]
        command = r'python %s -i %s -o %s -w %s -h %s -ft sequence -t proxy' % (pyfile, filein, fileout,
                                                                                        width, height)
        # probably good to write a custom imagemagick command for smedge for this.
        process_info = cgl_execute(command, command_name=command_name, methodology='smedge', WaitForJobID=dependent_job)
    elif processing_method == 'local':
        dirname, filename = os.path.split(filein)
        match = filename.split('*')[0]
        for each in os.listdir(os.path.dirname(filein)):
            if match in each:
                file_ = os.path.join(os.path.dirname(filein), each)
                SEQ_SPLIT = "\d{3,}\.\w{2,4}$"
                frange = re.search(SEQ_SPLIT, each)
                if frange:
                    num = os.path.splitext(frange.group(0))[0]
                    filename, ext_ = fileout.split('%')
                    if not ext:
                        ext = os.path.splitext(ext_)[-1].replace('.', '')
                    file_out = '%s%s.%s' % (filename, num, ext)
                    command = '%s %s -resize %s %s' % (PATHS['magick'], file_, res, file_out)
                    process_info = cgl_execute(command, methodology='local', command_name=command_name, verbose=True,
                                               new_window=new_window)

    if process_info:
        process_info['file_out'] = fileout
        print(fileout)
        print('-----------')
        print(process_info)
        try:
            write_to_cgl_data(process_info)
        except ValueError:
            print('Skipping write to cgl_data: %s' % process_info)
        return process_info
    else:
        print('----------------------------')
        print('process_info not defined')


def create_prores_mov(input_file, output_file=None, processing_method='local', dependent_job=None, quality=0,
                      new_window=False, command_name="create_prores_mov()"):
    """
    create a prores mov from specified input sequence, and save it to output.
    :param input_file: input sequence string, formatted with (#, %04d, *)
    :param output: output string
    :return:
    """
    if quality == 0:
        description = 'proxy'
    elif quality == 1:
        description = 'low'
    elif quality == 2:
        description = 'standard'
    elif quality == 3:
        description = 'high'
    if not command_name:
        command_name = "create_prores_mov(%s)" % description
    file_, ext = os.path.splitext(input_file)
    file_type = ext_map[ext]
    if not output_file:
        output_file = '%s_prores_%s.mov' % (file_, description)
    if file_type == 'movie':
        if processing_method == 'local':
            command = '%s -i %s -c:v prores_ks -qscale:v 1 -profile:v %s -c:a copy %s' % (PATHS['ffmpeg'], input_file, quality, output_file)
            cgl_execute(command, command_name='Create Prores', methodology=processing_method, WaitForJobID=dependent_job,
                        new_window=new_window)
            return output_file
        elif processing_method == 'smedge':
            filename = "%s.py" % os.path.splitext(__file__)[0]
            command = r'python %s -i %s -o %s -t prores -ft movie -q %s' % (filename, input_file, output_file, quality)
            process_info = cgl_execute(command, command_name=command_name, methodology='smedge',
                                       WaitForJobID=dependent_job)
            process_info['file_out'] = output_file
            return process_info
    else:
        print('File type: %s not supported with create_prores_mov()' % file_type)


def create_title(file_path='sample_image.png', title_text="Sample Title Text", size='1920x1080',
                 bg='transparent',
                 font_color='ffffff',
                 font='Arial',
                 font_size='120',
                 processing_method='local',
                 dependent_job=None):
    command = '%s convert -background %s -fill #%s -size %s -gravity center ' \
              '-font %s -pointsize %s label:"%s" %s' % (PATHS['magick'], bg, font_color,
                                                        size, font, font_size,
                                                        title_text, file_path)
    cgl_execute(command, command_name='Create Title', methodology=processing_method, WaitForJobID=dependent_job,
                new_window=False)


def create_quicktime_mov():
    """
    Creates quicktime movie with shotgun's prefferred settings.
    :return:
    """


def create_web_mov(input_sequence, output, framerate=settings['frame_rate'], output_frame_rate=None,
                   res=settings['resolution']['video_review'], processing_method='local', dependent_job=None,
                   command_name='create_web_mov()', new_window=False):
    """
    create a web optimized h264 mp4 from an specified input_sequence to a specified output.mp4
    This assumes an sRGB jpg sequence as input
    :param input_sequence: input sequence string, formatted with (#, %04d, *)
    :param output: output mp4 string
    :param framerate: frame rate for input sequence
    :param output_frame_rate: if None frame rate for input movie is used, if defined this frame rate is used for output movie
    :param res: resolution 1920x1080
    :param processing_method: local, smedge, deadline
    :param dependent_job: job_id of dependencies
    :param command_name: this is the command name that will be sent to the render farm
    :return:
    """
    from cgl.core.path import Sequence
    if not output:
        logging.error('No Output Defined')
        return
    input_ = Sequence(input_sequence)
    start_frame = None
    if input_.ext != '.jpg':
        logging.error('%s is not a valid ext for input sequences' % input_.ext)
    if not input_.is_valid_sequence():
        logging.error('%s is not a valid sequence for web quicktimes' % input_sequence)
        return
    else:
        start_frame = input_.start_frame
    file_type = 'sequence'
    filein = input_.num_sequence
    fileout = output
    prep_for_output(fileout)
    process_info = None

    if processing_method == 'smedge':
        filename = "%s.py" % os.path.splitext(__file__)[0]
        command = r'python %s -i %s -o %s -t web_preview -ft sequence' % (filename, filein, fileout)
        process_info = cgl_execute(command, command_name=command_name, methodology='smedge', WaitForJobID=dependent_job)
        process_info['file_out'] = fileout
        try:
            write_to_cgl_data(process_info)
        except ValueError:
            print('Skipping creation of cgl_data for %s:' % process_info)
        return process_info

    ffmpeg_cmd = ''
    if not output_frame_rate:
        output_frame_rate = framerate
    encoder = "libx264"
    profile = 'high'
    constant_rate_factor = "24"  # i need to test this with stuff that's not created at 24fps -
    pixel_format = 'yuv420p'
    gamma = 1
    width, height = res.split('x')
    vcodec = "-vcodec libx264 -pix_fmt yuv420p -vf 'scale=trunc((a*oh)/2)*2:720' -g 30 -b:v 2000k -vprofile high -bf 0"
    acodec = "-strict experimental -acodec aac -ab 160k -ac 2"

    filter_arg = r' -filter:v "scale=iw*min($width/iw\,$height/ih):ih*min($width/iw\,$height/ih),' \
                 r' pad=$width:$height:($width-iw*min($width/iw\,$height/ih))/2:' \
                 r'($height-ih*min($width/iw\,$height/ih))/2" '.replace('$width', width).replace('$height',
                                                                                                 height)

    if file_type == 'sequence':
        ffmpeg_cmd = r'%s -start_number %s -framerate %s -gamma %s -i %s -s:v %s -b:v 50M -c:v %s -profile:v %s' \
                     r' -crf %s -pix_fmt %s -r %s %s %s' % (PATHS['ffmpeg'],
                                                            start_frame, framerate, gamma, filein, res, encoder,
                                                            profile, constant_rate_factor, pixel_format,
                                                            output_frame_rate, filter_arg, fileout)
    elif file_type == 'movie':
        ffmpeg_cmd = r'%s -gamma %s -i %s -s:v %s -b:v 50M -c:v %s -profile:v %s' \
                     r' -crf %s -pix_fmt %s -r %s %s %s' % (PATHS['ffmpeg'], gamma, filein, res,
                                                            encoder, profile, constant_rate_factor, pixel_format,
                                                            output_frame_rate, filter_arg, fileout)
    if ffmpeg_cmd:
        process_info = cgl_execute(ffmpeg_cmd, verbose=True,
                                   command_name=command_name, WaitForJobID=dependent_job, new_window=new_window)

        process_info['file_out'] = fileout
        try:
            write_to_cgl_data(process_info)
        except ValueError:
            print('Skipping creation of cgl_data for %s' % fileout)
        return process_info


def prep_for_output(fileout, cleanup=True):
    if cleanup:
        if os.path.exists(fileout):
            os.remove(fileout)
    dir_ = os.path.dirname(fileout)
    if not os.path.exists(dir_):
        os.makedirs(dir_)
    return dir_


def create_movie_thumb(input_file, output_file, processing_method='local', command_name='create_movie_thumb()',
                       dependent_job=None, new_window=False):
    """
    creates thumbnail for a movie file.
    :param input_file: input sequence string, formatted with (#, %04d, *)
    :param output_file: output sequence string, formatted with (####, %04d, *)
    :param processing_method: how will this be processed? (local, smedge, deadline)
    :param dependent_job: job_id of any dependencies
    :param command_name: this is the command name that will be sent to the render farm
    :return:
    """
    if not output_file:
        print('No output_file specified, cancelling thumbnail generation')
        return
    res = settings['resolution']['thumb_cine'].replace('x', ':')
    prep_for_output(output_file)

    if processing_method == 'smedge':
        pyfile = '%s.py' % os.path.splitext(__file__)[0]
        command = r'python %s -i %s -o %s -t thumb -ft movie' % (pyfile, input_file, output_file)
        process_info = cgl_execute(command, command_name=command_name, methodology='smedge', WaitForJobID=dependent_job)
        process_info['file_out'] = output_file
        try:
            write_to_cgl_data(process_info)
        except ValueError:
            print('Error writing to cgl_data for: %s' % output_file)
        return process_info

    if processing_method == 'local':
        command = '%s -i %s -vf "thumbnail,scale=%s" ' \
                  '-frames:v 1 %s' % (PATHS['ffmpeg'], input_file, res, output_file)
        process_info = cgl_execute(command, verbose=True, methodology='local',
                                   command_name=command_name, new_window=True,
                                   WaitForJobID=dependent_job)
        process_info['file_out'] = output_file
        try:
            write_to_cgl_data(process_info)
        except ValueError:
            print('Error writing to cgl_data for: %s' % output_file)
        return process_info


def change_extension(filein, new_ext):
    new_ext = new_ext.replace('.', '')
    file_ = os.path.splitext(filein)[0]
    return '%s.%s' % (file_, new_ext)


def convert_to_webm(filein, fileout=None, processing_method='local', dependent_job=None):
    """
    creates a .mp4 file specifically to be used in amazon's transcription services.
    :param filein:
    :param fileout:
    :param processing_method:
    :param dependent_job:
    :return:
    """
    if not fileout:
        fileout = change_extension(filein, 'mp4')
    vcodec = ' -pix_fmt yuv420p -vcodec libvpx -vf "scale=trunc((a*oh)/2)*2:720" -g 30 -b:v 2000k -vpre 720p -quality realtime -cpu-used 0 -qmin 10 -qmax 42'
    acodec = "-acodec libvorbis -aq 60 -ac 2"
    command = "%s -i %s %s %s -f webm %s" % (PATHS['ffmpeg'], filein, acodec, vcodec, fileout)
    cgl_execute(command, command_name='convert to webm', methodology=processing_method, WaitForJobID=dependent_job,
                new_window=True)
    return fileout


def convert_to_mp4(filein, fileout=None, processing_method='local', dependent_job=None, audio_only=False,
                   new_window=False, command_name='convert_to_mp4()', delete_existing=True):
    """
    creates a .mp4 file specifically to be used in amazon's transcription services.
    :param filein:
    :param fileout:
    :param processing_method:
    :param dependent_job:
    :return:
    """
    if not fileout:
        fileout = change_extension(filein, 'mp4')
        print(fileout)
        if os.path.exists(fileout):
            print('deleting fileout: %s' % fileout)
            if delete_existing:
                print('deleting existing file: %s' % fileout)
                os.remove(fileout)
        # 'scale=trunc((a*oh)/2)*2:720'
    vcodec = '-vcodec libx264 -pix_fmt yuv420p -vf "scale=trunc((a*oh)/2)*2:720" -g 30 -b:v 2000k -vprofile high -bf 0'
    acodec = "-strict experimental -acodec aac -ab 160k -ac 2"
    process_info = {'file_out': fileout, 'job_id': 0}

    if audio_only:
        if not fileout.endswith('_audio.mp4'):
            fileout = fileout.replace('.mp4', '_audio.mp4')
            print(fileout)
            if os.path.exists(fileout):
                print('deleting fileout: %s' % fileout)
                if delete_existing:
                    print('deleting existing file: %s' % fileout)
                    os.remove(fileout)
        if processing_method == 'local':
            command = "%s -i %s -vn %s %s" % (PATHS['ffmpeg'], filein, acodec, fileout)
            cgl_execute(command, command_name=command_name, methodology='local',
                        WaitForJobID=dependent_job)
            process_info['file_out'] = fileout
            return process_info
        elif processing_method == 'smedge':
            filename = "%s.py" % os.path.splitext(__file__)[0]
            command = r'python %s -i %s -o %s -t audio -ft movie' % (filename, filein, fileout)
            process_info = cgl_execute(command, command_name=command_name, methodology='smedge',
                                       WaitForJobID=dependent_job)
            process_info['file_out'] = fileout
            return process_info
    else:
        if processing_method == 'local':
            command = "%s -i %s %s %s -f mp4 %s" % (PATHS['ffmpeg'], filein, acodec, vcodec, fileout)
            cgl_execute(command, command_name='Convert to mp4', methodology=processing_method, WaitForJobID=dependent_job,
                        new_window=new_window)
            process_info['file_out'] = fileout
        elif processing_method == 'smedge':
            filename = "%s.py" % os.path.splitext(__file__)[0]
            command = r'python %s -i %s -o %s -t mp4 -ft movie' % (filename, filein, fileout)
            process_info = cgl_execute(command, command_name=command_name, methodology='smedge',
                                       WaitForJobID=dependent_job)
            process_info['file_out'] = fileout
            return process_info
    return process_info


def extract_wav_from_movie(filein, fileout=None, processing_method='local', dependent_job=None):
    """
    extracts audio from a video file.
    :param filein: location of video file to extract from.
    :param fileout: location of .wav file to be created
    :param processing_method: local, smedge, or deadline processing.
    :param dependent_job:
    :return:
    """
    # check if the input is an approved video format.
    file_, ext = os.path.splitext(filein)
    if ext in ext_map.keys():
        if ext_map[ext] == 'movie':
            if not fileout:
                fileout = '%s.wav' % file_
            if not fileout.endswith('.wav'):
                print("%s is not a .wav file, aborting wav extraction")
                return
            command = '%s -i %s -acodec pcm_s16le -ac 2 %s' % (PATHS['ffmpeg'], filein, fileout)
            cgl_execute(command, command_name='Audio Extraction', methodology=processing_method, WaitForJobID=dependent_job,
                        new_window=True)
            return fileout
    else:
        print('Extension %s not cataloged in globals, please add it to the ext_map dictionary' % ext)


@click.command()
@click.option('--input_file', '-i', prompt='File Sequence Path (file.####.ext)',
              help='Path to the Input File.  Can be Image, Image Sequence, Movie')
@click.option('--output_file', '-o', default=None,
              help='Path to the output file/folder/sequence')
@click.option('--width', '-w', default=1920, help='width in pixels')
@click.option('--height', '-h', default=1080, help='height in pixels')
@click.option('--file_type', '-ft', default='movie', help='options: sequence, image, movie')
@click.option('--conversion_type', '-t', default='web_preview',
              help='Type of Conversions: proxy, mp4, web_preview, prores, thumb, gif, audio')
@click.option('--quality', '-q', default=0, help='0:proxy, 1:low, 2:standard, 3:high')
def main(input_file, output_file, height, width, file_type, conversion_type, quality=0):
    run_dict = {}
    if file_type == 'sequence':
        if conversion_type == 'proxy':
            create_proxy_sequence(input_file, output_sequence=output_file, width=width, height=height)
        elif conversion_type == 'web_preview':
            create_web_mov(input_file, output=output_file)
    if file_type == 'movie':
        if conversion_type == 'prores':
            create_prores_mov(input_file, output_file, quality=quality)
        elif conversion_type == 'audio':
            convert_to_mp4(input_file, output_file, audio_only=True)
        elif conversion_type == 'thumb':
            create_movie_thumb(input_file, output_file)
        elif conversion_type == 'mp4':
            convert_to_mp4(input_file, output_file)
        else:
            print('Conversion Type: %s process not defined' % conversion_type)
    if run_dict.keys():
        for key in run_dict:
            click.echo('%s: %s' % (key, run_dict[key]))


if __name__ == '__main__':
    main()


