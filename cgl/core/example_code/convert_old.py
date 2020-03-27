import os
import click
import logging
from cgl.core.config import app_config
from cgl.core.path import PathObject, CreateProductionData, split_sequence, number_to_hash, hash_to_number
from cgl.core.path import prep_seq_delimiter, lj_list_dir, get_start_frame
from core.utils.general import cgl_execute, write_to_cgl_data

CONFIG = app_config()['paths']
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

#####################################################################
#
#               Queries
#
#####################################################################


def get_first_frame(sequence, return_type='string'):
    sequence = prep_seq_delimiter(sequence, '*')
    first_frame = ''
    middle_frame = 0
    last_frame = ''
    try:
        # td - this will not pass some instances, we'll have to use REGEX eventually
        for each in lj_list_dir(os.path.dirname(sequence)):
            file_name = each.split()[0]
            hashes = file_name.count('#')
            if ' ' in each:
                first_frame, last_frame = each.split(' ')[-1].split('-')
                middle_frame = (int(last_frame) - int(first_frame)) / 2 + int(first_frame)
            if hashes == 9:
                middle_string = '%09d' % middle_frame
            elif hashes == 8:
                middle_string = '%08d' % middle_frame
            elif hashes == 7:
                middle_string = '%07d' % middle_frame
            elif hashes == 6:
                middle_string = '%06d' % middle_frame
            elif hashes == 5:
                middle_string = '%05d' % middle_frame
            elif hashes == 4:
                middle_string = '%04d' % middle_frame
            elif hashes == 3:
                middle_string = '%03d' % middle_frame
            elif hashes == 2:
                middle_string = '%02d' % middle_frame
        middle_frame = sequence.replace('*', middle_string)
        if return_type == 'string':
            return first_frame, middle_frame, last_frame
        else:
            return first_frame, middle_frame, last_frame
    except IndexError:
        logging.info('can not find files like {0}'.format(sequence))
        return None


def get_info(input_file):
    if get_file_type(input_file) == 'movie':
        ffprobe_cmd = "%s -v error -show_format -show_streams -of default=noprint_wrappers=1 %s"\
                      % (CONFIG['ffprobe'], input_file)
        return cgl_execute(ffprobe_cmd, verbose=True)

    elif get_file_type(input_file) == 'sequence':
        _, middle, _ = get_first_frame(input_file)
        return get_image_info(middle)


def get_image_info(input_file):
    # TODO - can we replace this with the metadata module i created?
    command = "%s --info %s" % (CONFIG['oiiotool'], input_file)
    return cgl_execute(command, verbose=True)


def print_info(d):
    # this is honestly here for developers more than anything to show us what metadata is available in case we
    # need it for different queries & functions
    for key in d:
        if key != 'None':
            logging.info('%s: %s' % (key, d[key]))


def get_resolution(input_file):
    d = get_info(input_file)
    if d:
        return '%sx%s' % (int(d['width']), int(d['height']))
    else:
        return '200x200'


def get_framerate(input_file):
    if get_file_type(input_file) == 'movie':
        return get_info(input_file)['r_frame_rate'].split('/')[0]
    else:
        return None


def get_file_type(input_file):
    _, file_ext = os.path.splitext(input_file)
    try:
        _type = ext_map[file_ext]
        if _type == 'movie':
            return 'movie'
        if _type == 'image':
            if '%0' in input_file:
                return 'sequence'
            elif '###' in input_file:
                return 'sequence'
            else:
                return 'image'
    except KeyError:
        return None

#####################################################################
#
#               CREATION
#
#####################################################################


def create_proxy(sequence, ext='jpg', verbose=True, methodology='local'):
    """
    Creates a Jpeg proxy resolution based off the resolution of the given path.
    :param sequence:
    :param ext:
    :param project_management:
    :return:
    """
    out_seq = ''
    path_object = PathObject(sequence)
    start_frame = get_start_frame(sequence)
    new_res = '%s%s' % (path_object.resolution, 'Proxy')
    path_object_output = path_object.copy(resolution=new_res, ext='jpg')
    output_dir = os.path.dirname(path_object_output.path_root)
    if not os.path.exists(output_dir):
        CreateProductionData(path_object=output_dir, project_management=False)
    if '####' in sequence:
        # replace ### with "*"
        number = hash_to_number(sequence)[-1]
        in_seq = '%s*.%s' % (split_sequence(sequence), path_object.ext)
        out_seq = '%s/%s%s.%s' % (output_dir, os.path.basename(split_sequence(sequence)), number, ext)
        command = '%s %s -scene %s %s' % (CONFIG['magick'], in_seq, start_frame, out_seq)
        run_dict = cgl_execute(command, methodology=methodology, verbose=verbose)
        run_dict['file_out'] = out_seq
        write_to_cgl_data(run_dict)
    return run_dict


def create_hd_proxy(sequence, output=None, mov=None, ext='jpg', width='1920', height='x1080', do_height=False,
                    start_frame=None, verbose=True, methodology='local', dependent_job=None):
    """
    Create HD Proxy Sequence from a givein image sequence.
    :param sequence:
    :param output:
    :param mov:
    :param ext:
    :param width:
    :param height:
    :param do_height:
    :param start_frame:
    :param verbose:
    :param methodology:
    :param dependent_job:
    :return:
    """

    if do_height:
        res = height
    else:
        res = width
    path_object = PathObject(sequence)
    path_object.set_file_type()
    hashes = ''
    fileout = ''
    out_seq = ''
    command = ''
    number = ''
    if not output:
        logging.info('No output defined for create_hd_proxy')
    else:
        path_object_output = None
        output_dir = os.path.dirname(output)
    if path_object.file_type == 'sequence':
        # replace ### with "*"
        if '##' in sequence:
            hashes, number = hash_to_number(sequence)
        elif '%0' in sequence:
            hashes, number = number_to_hash(sequence)
        in_seq = '%s*.%s' % (split_sequence(sequence), path_object.ext)
        out_seq = '%s/%s%s.%s' % (output_dir, os.path.basename(split_sequence(sequence)), number, ext)
        fileout = out_seq.replace(number, hashes)
    elif path_object.file_type == 'image':
        sequence = sequence
        try:
            path_object_output.set_attr(ext='jpg')
            fileout = path_object_output.path_root
        except AttributeError:
            this_ = os.path.splitext(output)[0]
            fileout = this_+'.jpg'
        command = '%s %s -resize %s %s' % (CONFIG['magick'], sequence, res, fileout)

    if methodology == 'smedge':
        print "I'm sending this to smedge to start after %s" % dependent_job
        command = r'python %s -i %s' % (__file__, sequence)
        # set_process_time = r'"python %s -e True -j %s -k farm_processing_end"' % (util_file, '%SMEDGE_JOB_ID%')
        # run_dict = cgl_execute(command, command_name='create_hd_proxy', methodology=methodology,
        #                        Wait=dependent_job, WorkPostExecuteSuccessfulEvt=set_process_time)
        run_dict = cgl_execute(command, command_name='%s_%s: create_hd_proxy' % (path_object.seq, path_object.shot),
                               methodology='smedge',
                               Wait=dependent_job)
        run_dict['file_out'] = fileout
        write_to_cgl_data(run_dict)
        return run_dict

    if not start_frame:
        start_frame = get_start_frame(sequence)

    if path_object.file_type == 'sequence':
        command = '%s %s -scene %s -resize %s %s' % (CONFIG['magick'], in_seq, start_frame, res, out_seq)
    if not os.path.exists(output_dir):
        CreateProductionData(path_object=output_dir, project_management='lumbermill')
    run_dict = cgl_execute(command, verbose=verbose, methodology=methodology,
                           command_name='%s_%s: create_hd_proxy' % (path_object.seq, path_object.shot),
                           Wait=dependent_job)
    run_dict['file_out'] = fileout
    write_to_cgl_data(run_dict)
    print 'file_out: %s' % fileout
    return run_dict


def create_gif_proxy(sequence, ext='gif', width='480', height='x100', do_height=False, verbose=True):
    if do_height:
        res = height
    else:
        res = width
    path_object = PathObject(sequence)
    new_res = 'gif'
    path_object_output = path_object.copy(resolution=new_res)
    output_dir = os.path.dirname(path_object_output.path_root)
    out_seq = ''
    command = ''
    if not os.path.exists(output_dir):
        CreateProductionData(path_object=output_dir, project_management=False)
    if '####' in sequence:
        in_seq = '%s*.%s' % (split_sequence(sequence), path_object.ext)
        out_seq = '%s/%s%s' % (output_dir, os.path.basename(split_sequence(sequence)), ext)
        command = '%s %s -resize %s %s' % (CONFIG['magick'], in_seq, res, out_seq)

    if command:
        cgl_execute(command, verbose=verbose)
        return out_seq


def create_gif_thumb(sequence, ext='gif', width='100', height='x100', do_height=True, verbose=True):
    if do_height:
        res = height
    else:
        res = width
    path_object = PathObject(sequence)
    new_res = 'gif'
    path_object_output = path_object.copy(resolution=new_res)
    output_dir = os.path.dirname(path_object_output.path_root)
    out_seq = ''
    command = ''
    if not os.path.exists(output_dir):
        CreateProductionData(path_object=output_dir, project_management=False)
    if '####' in sequence:
        in_seq = '%s*.%s' % (split_sequence(sequence), path_object.ext)
        out_seq = '%s/%sthumb.%s' % (output_dir, os.path.basename(split_sequence(sequence)), ext)
        command = '%s %s -resize %s %s' % (CONFIG['magick'], in_seq, res, out_seq)

    if command:
        cgl_execute(command, verbose=verbose)
        return out_seq


def create_mov(sequence, output=None, framerate=settings['frame_rate'], output_frame_rate=None,
               res=settings['resolution']['video_review'], methodology='local', dependent_job=None):

    path_object = PathObject(sequence)
    output_file = ''
    input_file = ''
    if output:
        if path_object.file_type == 'sequence':
            input_file = prep_seq_delimiter(sequence, replace_with='%')
            output_file = output
            if not os.path.exists(os.path.dirname(output_file)):
                os.makedirs(os.path.dirname(output_file))
        else:
            print('Nothing defined for %s' % path_object.file_type)
    else:
        print 2
        output_file = path_object.preview_path
        if path_object.file_type == 'sequence':
            if not output:
                output_file = output_file.split('#')[0]
                if output_file.endswith('.'):
                    output_file = '%smp4' % output_file
                else:
                    output_file = '%s.mp4' % output_file
                filename = os.path.basename(output_file)

    if methodology == 'smedge':
        command = r'python %s -i %s -t %s' % (__file__, sequence, 'mov')
        run_dict = cgl_execute(command, command_name='%s_%s: create_mov' % (path_object.seq, path_object.shot),
                               methodology='smedge', Wait=dependent_job)
        run_dict['file_out'] = output_file
        write_to_cgl_data(run_dict)
        return run_dict
    print output_file, 'output file'
    if path_object.file_type == 'sequence':
        input_file = prep_seq_delimiter(sequence, replace_with='%')
    if os.path.exists(output_file):
        os.remove(output_file)
    if os.path.splitext(input_file)[-1] == '.exr' or os.path.splitext(input_file)[-1] == '.dpx':
        logging.info('applying gamma 2.2 to linear sequence')
        gamma = 2.2
    else:
        gamma = 1

    if not output_frame_rate:
        output_frame_rate = framerate
    encoder = "libx264"
    profile = 'high'
    constant_rate_factor = "24"  # i need to test this with stuff that's not created at 24fps -
    pixel_format = 'yuv420p'

    res_list = res.split('x')
    width = res_list[0]
    height = res_list[1]
    if methodology == 'smedge':
        filter_arg = r' -filter:v \"scale=iw*min($width/iw\,$height/ih):ih*min($width/iw\,$height/ih),' \
                     r' pad=$width:$height:($width-iw*min($width/iw\,$height/ih))/2:' \
                     r'($height-ih*min($width/iw\,$height/ih))/2\" '.replace('$width', width).replace('$height',
                                                                                                      height)
    else:
        filter_arg = r' -filter:v "scale=iw*min($width/iw\,$height/ih):ih*min($width/iw\,$height/ih),' \
                     r' pad=$width:$height:($width-iw*min($width/iw\,$height/ih))/2:' \
                     r'($height-ih*min($width/iw\,$height/ih))/2" '.replace('$width', width).replace('$height',
                                                                                                     height)
    ffmpeg_cmd = ''
    if path_object.file_type == 'sequence':
        start_frame = get_first_frame(sequence)[0]
        ffmpeg_cmd = r'%s -start_number %s -framerate %s -gamma %s -i %s -s:v %s -b:v 50M -c:v %s -profile:v %s' \
                     r' -crf %s -pix_fmt %s -r %s %s %s' % (CONFIG['ffmpeg'],
                                                            start_frame, framerate, gamma, input_file, res, encoder,
                                                            profile, constant_rate_factor, pixel_format,
                                                            output_frame_rate, filter_arg, output_file)
    elif path_object.file_type == 'movie':
        print 4
        ffmpeg_cmd = r'%s -gamma %s -i %s -s:v %s -b:v 50M -c:v %s -profile:v %s' \
                     r' -crf %s -pix_fmt %s -r %s %s %s' % (CONFIG['ffmpeg'], gamma, input_file, res,
                                                            encoder, profile, constant_rate_factor, pixel_format,
                                                            output_frame_rate, filter_arg, output_file)
    if ffmpeg_cmd:
        print 5
        run_dict = cgl_execute(ffmpeg_cmd, verbose=True, methodology=methodology,
                               command_name='%s_%s: create_mov' % (path_object.seq, path_object.shot),
                               Wait=dependent_job)

        run_dict['file_out'] = output_file
        write_to_cgl_data(run_dict)
        create_movie_thumb(sequence, methodology=methodology,
                           dependent_job=run_dict['job_id'])

        return run_dict


def create_movie_thumb(input_file, output_file=None, frame='middle', thumb=True, methodology='local',
                       dependent_job=None):
    """
    Create a thumbnail from a movie file.
    :param input_file: path to mov
    :param output_file: output file (jpg)
    :param frame: first, middle, or last
    :param thumb: Default value is True, this pulls the thumbnail resolution from the settings.
    :return:
    """

    path_object = PathObject(input_file)
    if not output_file:
        if '.preview' in input_file:
            output_file.replace('.preview', '.thumb')
        else:
            output_file = PathObject(path_object=input_file).copy(resolution='thumb', ext='jpg').path_root
    if not output_file.endswith('.jpg'):
        file_ = os.path.splitext(output_file)[0]
        output_file = '%s.%s' % (file_, 'jpg')
    if os.path.exists(output_file):
        os.remove(output_file)
    if not os.path.exists(os.path.dirname(output_file)):

        CreateProductionData(os.path.dirname(output_file), project_management='lumbermill')
    if get_file_type(input_file) == 'movie':
        if thumb:
            res = get_thumb_res(input_file)
            res.replace('x', ':')
            if not res:
                logging.warning('problem with thumbnail resolution algorithm')
                res = settings['resolution']['thumb_cine']
        else:
            res = settings['resolution']['image_review'].replace('x', ':')
        # This command will just use ffmpeg's default thumbnail generator
        command = '%s -i %s -vf "thumbnail,scale=%s" ' \
                  '-frames:v 1 %s' % (CONFIG['ffmpeg'], input_file, res, output_file)
        if command:
            run_dict = cgl_execute(command, verbose=True, methodology=methodology,
                                   command_name='%s_%s: create_mov_thumb' % (path_object.seq, path_object.shot),
                                   Wait=dependent_job)
            run_dict['file_out'] = output_file
            write_to_cgl_data(run_dict)
        return run_dict

    else:
        if get_file_type(input_file) == 'sequence':
            first_frame, middle_frame, end_frame = get_first_frame(input_file)
            if frame == 'middle':
                input_file = middle_frame
            elif frame == 'first':
                input_file = first_frame
            elif frame == 'last':
                input_file = end_frame
        # create the thumbnail
        # output_file = output_file.replace('####', 'seq')
        if thumb:
            res = thumb_res
        else:
            res = settings['resolution']['image_review']
        # command = r"%s %s --fit %s --ch R,G,B -o %s" % (CONFIG['oiiotool'], input_file, res, output_file)
        command = '%s %s -resize %s %s' % (CONFIG['magick'], input_file, res, output_file)
        run_dict = cgl_execute(command, verbose=True, methodology=methodology, Wait=dependent_job)
        run_dict['file_out'] = output_file
        write_to_cgl_data(run_dict)
        return run_dict


def make_full_res_jpg(input_file, preview_path=None):
    if not preview_path:
        # preview_path = PathParser.preview_path_from_frame_path(input_file, file_type='image')
        preview_path = PathObject(path_object=input_file).preview_path
        if not os.path.isdir(os.path.split(preview_path)[0]):
            os.makedirs(os.path.split(preview_path)[0])
    command = r"%s %s --ch R,G,B -o %s" % (CONFIG['magick'], input_file, preview_path)
    if command:
        cgl_execute(command, verbose=True)
    return preview_path


def make_images_from_pdf(input_file, preview_path=None):
    """
    Creates jpg images from a pdf
    :param input_file:
    :param preview_path:
    :return:
    """
    # This requires imagemagick as well as ghostscript.  this is on hold until i understand better how
    # the licensing for ghostscript works and how we'd package it.
    if not preview_path:
        preview_path = PathObject(input_file).preview_path
        if not os.path.exists(os.path.split(preview_path)[0]):
            os.makedirs(os.path.split(preview_path)[0])
    name = os.path.splitext(os.path.split(input_file)[-1])[0]
    output_file = name + '.%04d.jpg'
    command = r"%s -density 300 %s %s/%s" % (CONFIG['imagemagick'], input_file,
                                             os.path.split(input_file)[0], output_file)
    if command:
        cgl_execute(command, verbose=True)
    return True


def get_thumb_res(input_file):
    """
    :param input_file: image file
    :return:
    """
    res = get_resolution(input_file)
    width, height = res.split('x')
    if width > height:
        # landscape resolution
        tw, th = thumb_res.split('x')
        nh = (int(height) * int(tw))/int(width)
        ntr = '%sx%s' % (tw, nh)
    else:
        tw, th = thumb_res.split('x')
        nw = (int(width) * int(tw)) / int(height)
        ntr = '%sx%s' % (nw, th)

    return ntr


def create_thumbnail(input_file, output_file):
    """
    Creates an thumbnail based off resolution defined in the get_thumb_res
    :param input_file:
    :param output_file:
    :return:
    """
    res = get_thumb_res(input_file)
    width, height = res.split('x')
    create_hd_proxy(input_file, output_file, width=width, height=height)


def make_animated_gif(input_file):
    import subprocess
    input_file = input_file.replace('####', '%04d')
    h, _ = thumb_res.split('x')
    # palette = PathParser.thumbpath_from_path(input_file)
    palette = PathObject(input_file).thumb_path
    path_, _ = os.path.splitext(palette)
    ext = '.palette.png'
    palette = path_+ext
    if os.path.exists(palette):
        os.remove(palette)
    # output_file = PathParser.thumbpath_from_path(input_file.replace('%04d', 'seq'))
    output_file = PathObject(input_file.replace('%04d', 'seq')).thumb_path
    ext2 = '.gif'
    path_, _ = os.path.splitext(output_file)
    output_file = path_+ext2
    if not os.path.exists(os.path.dirname(output_file)):
        os.makedirs(os.path.dirname(output_file))
    else:
        if os.path.exists(output_file):
            os.remove(output_file)
    filters = "fps=15,scale=%s:-1:flags=lanczos" % h
    command = '%s -i %s -vf "%s,palettegen" -y %s' % (CONFIG['ffmpeg'], input_file, filters, palette)
    print 'command 1', command
    p = subprocess.Popen([CONFIG['ffmpeg'], '-i', input_file, '-vf', "%s,palettegen" % filters, '-y', palette],
                         stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=subprocess.STDOUT)
    print p.stdout.readline()  # read the first line
    for i in range(10):  # repeat several times to show that it works
        print >> p.stdin, i  # write input
        p.stdin.flush()  # not necessary in this case
        print p.stdout.readline(),  # read output
    print p.communicate("n\n")[0],
    p.wait()

    command2 = '%s -i %s -i %s -lavfi "%s [x]; [x][1:v] paletteuse" -y %s' \
               % (CONFIG['ffmpeg'], input_file, palette, filters, output_file.replace('palette.', ''))
    print 'command 2', command2
    p2 = subprocess.Popen([CONFIG['ffmpeg'], '-i', input_file, '-i', palette, '-lavfi',
                           "%s [x]; [x][1:v] paletteuse" % filters, '-y', output_file.replace('palette.', '')],
                          stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=subprocess.STDOUT)
    print p2.stdout.readline(),  # read the first line
    for i in range(10):  # repeat several times to show that it works
        print >> p2.stdin, i  # write input
        p2.stdin.flush()  # not necessary in this case
        print p2.stdout.readline(),  # read output
    print p2.communicate("n\n")[0],
    p.wait()
    return output_file


@click.command()
@click.option('--input_file', '-i', prompt='File Sequence Path (file.####.ext)',
              help='Path to the Input File.  Can be Image, Image Sequence, Movie')
@click.option('--output_file', '-o', default=None,
              help='Path to the output file/folder/sequence')
@click.option('--conversion_type', '-t', default='proxy', help='Type of Conversion - sequence, movie, image, gif')
def main(input_file, output_file, conversion_type):
    file_type = get_file_type(input_file)
    run_dict = {}
    if file_type == 'sequence':
        if conversion_type == 'proxy':
            run_dict = create_hd_proxy(input_file, output=output_file)
        elif conversion_type == 'mov':
            run_dict = create_mov(input_file)
    if run_dict.keys():
        for key in run_dict:
            click.echo('%s: %s' % (key, run_dict[key]))


if __name__ == '__main__':
    main()
