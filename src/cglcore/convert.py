import os
import subprocess
import logging
from cglcore.config import app_config
from cglcore.path import PathObject, CreateProductionData, split_sequence, number_to_hash, hash_to_number
from cglcore.path import prep_seq_delimiter, lj_list_dir, get_start_frame

config = app_config()['paths']
settings = app_config()['default']
thumb_res = settings['resolution']['thumb']
frame_rate = settings['frame_rate']
ext_map = app_config()['ext_map']
PROJ_MANAGEMENT = app_config()['account_info']['project_management']

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
            if hashes == 6:
                middle_string = '%06d' % middle_frame
            if hashes == 4:
                middle_string = '%04d' % middle_frame
            if hashes == 5:
                middle_string = '%05d' % middle_frame
            if hashes == 3:
                middle_string = '%03d' % middle_frame
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
                      % (config['ffprobe'], input_file)
        p = subprocess.Popen(ffprobe_cmd,
                             stdout=subprocess.PIPE,
                             stderr=subprocess.STDOUT)
        d = {}
        for each in p.stdout:
            print each
            try:
                key, value = each.strip('\n').split('=')
                if key != 'None':
                    d[key] = value
            except ValueError:
                pass
        return d

    elif get_file_type(input_file) == 'sequence':
        _, middle, _ = get_first_frame(input_file)
        return get_image_info(middle)


def get_image_info(input_file):
    # TODO - can we replace this with the metadata module i created?
    command = "%s --info %s" % (config['oiiotool'], input_file)
    p = subprocess.Popen(command,
                         stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT)
    d = {}
    for each in p.stdout:
        res, channels, filetype = each.strip('\n').split(':')[-1].split(',')
        w, h = res.split(' x ')
        d['width'] = w.strip()
        d['height'] = h
        d['channels'] = channels.split(' ')[-2]
        d['encoding'] = filetype.split(' ')[1]
        d['filetype'] = filetype.split(' ')[-1]

    return d


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
            if '%04d' in input_file:
                return 'sequence'
            elif '####' in input_file:
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


def _execute(command):
    logging.info('Executing Command: %s' % command)
    p = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)
    while True:
        output = p.stdout.readline()
        if output == '' and p.poll() is not None:
            break
        if output:
            print output.strip()
    rc = p.poll()
    return rc


def create_proxy(sequence, ext='jpg'):
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
        command = '%s %s -scene %s %s' % (config['magick'], in_seq, start_frame, out_seq)
        _execute(command)
    print out_seq
    return out_seq


def create_hd_proxy(sequence, output=None, mov=None, ext='jpg', width='1920', height='x1080', do_height=False,
                    start_frame='1001'):
    hashes = ''
    fileout = ''
    out_seq = ''
    command = ''
    number = ''
    if do_height:
        res = height
    else:
        res = width
    path_object = PathObject(sequence)
    path_object.set_file_type()
    if not output:
        path_object_output = path_object.copy(resolution='hdProxy')
        output_dir = os.path.dirname(path_object_output.path_root)
    else:
        path_object_output = None
        output_dir = os.path.dirname(output)
    if not os.path.exists(output_dir):
        CreateProductionData(path_object=output_dir, project_management='lumbermill')
    if path_object.file_type == 'sequence':
        # replace ### with "*"
        if '##' in sequence:
            hashes, number = hash_to_number(sequence)
        elif '%0' in sequence:
            hashes, number = number_to_hash(sequence)
        in_seq = '%s*.%s' % (split_sequence(sequence), path_object.ext)
        out_seq = '%s/%s%s.%s' % (output_dir, os.path.basename(split_sequence(sequence)), number, ext)
        command = '%s %s -scene %s -resize %s %s' % (config['magick'], in_seq, start_frame, res, out_seq)
        fileout = out_seq.replace(number, hashes)
    elif path_object.file_type == 'image':
        sequence = sequence
        try:
            path_object_output.set_attr(ext='jpg')
            fileout = path_object_output.path_root
        except AttributeError:
            this_ = os.path.splitext(output)[0]
            fileout = this_+'.jpg'
        command = '%s %s -resize %s %s' % (config['magick'], sequence, res, fileout)
    print 'Command is:', command
    _execute(command)
    return fileout


def create_gif_proxy(sequence, ext='gif', width='480', height='x100', do_height=False):
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
        command = '%s %s -resize %s %s' % (config['magick'], in_seq, res, out_seq)

    if command:
        _execute(command)
        return out_seq


def create_gif_thumb(sequence, ext='gif', width='100', height='x100', do_height=True):
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
        command = '%s %s -resize %s %s' % (config['magick'], in_seq, res, out_seq)

    if command:
        _execute(command)
        return out_seq


def create_mov(sequence, output=None, framerate=settings['frame_rate'], output_frame_rate=None,
               res=settings['resolution']['video_review']):
    start_frame = 1001
    path_object = PathObject(sequence)

    if output:
        if path_object.file_type == 'sequence':
            start_frame = get_first_frame(sequence)[0]
            input_file = prep_seq_delimiter(sequence, replace_with='%')
            output_file = output
            if not os.path.exists(os.path.dirname(output_file)):
                os.makedirs(os.path.dirname(output_file))
        else:
            print('Nothing defined for %s' % path_object.file_type)
    else:
        web_path_object = PathObject(sequence).copy(resolution='webMov')
        CreateProductionData(web_path_object, project_management='lumbermill')
        output_file = web_path_object.path_root

        if path_object.file_type == 'sequence':
            start_frame = get_first_frame(sequence)[0]
            input_file = prep_seq_delimiter(sequence, replace_with='%')
            if not output:
                output_file = output_file.split('#')[0]
                if output_file.endswith('.'):
                    output_file = '%smp4' % output_file
                else:
                    output_file = '%s.mp4' % output_file
                filename = os.path.basename(output_file)
                web_path_object.set_attr(filename=filename)

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
    filter_arg = r' -filter:v "scale=iw*min($width/iw\,$height/ih):ih*min($width/iw\,$height/ih),' \
                 r' pad=$width:$height:($width-iw*min($width/iw\,$height/ih))/2:' \
                 r'($height-ih*min($width/iw\,$height/ih))/2" '.replace('$width', width).replace('$height',
                                                                                                 height)
    ffmpeg_cmd = ''
    if path_object.file_type == 'sequence':
        ffmpeg_cmd = r'%s -start_number %s -framerate %s -gamma %s -i %s -s:v %s -b:v 50M -c:v %s -profile:v %s' \
                     r' -crf %s -pix_fmt %s -r %s %s %s' % (config['ffmpeg'],
                                                            start_frame, framerate, gamma, input_file, res, encoder,
                                                            profile, constant_rate_factor, pixel_format,
                                                            output_frame_rate, filter_arg, output_file)
    elif path_object.file_type == 'movie':
        ffmpeg_cmd = r'%s -gamma %s -i %s -s:v %s -b:v 50M -c:v %s -profile:v %s' \
                     r' -crf %s -pix_fmt %s -r %s %s %s' % (config['ffmpeg'], gamma, input_file, res,
                                                            encoder, profile, constant_rate_factor, pixel_format,
                                                            output_frame_rate, filter_arg, output_file)
    if ffmpeg_cmd:
        _execute(ffmpeg_cmd)
        create_movie_thumb(sequence)

    return output_file


def create_movie_thumb(input_file, output_file=None, frame='middle', thumb=True):
    print 'creating movie thumbnail'
    if not output_file:
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
                  '-frames:v 1 %s' % (config['ffmpeg'], input_file, res, output_file)
        if command:
            _execute(command)
        return output_file

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
        # command = r"%s %s --fit %s --ch R,G,B -o %s" % (config['oiiotool'], input_file, res, output_file)
        command = '%s %s -resize %s %s' % (config['magick'], input_file, res, output_file)
        _execute(command)
        return output_file


def make_full_res_jpg(input_file, preview_path=None):
    if not preview_path:
        # preview_path = PathParser.preview_path_from_frame_path(input_file, file_type='image')
        preview_path = PathObject(path_object=input_file).preview_path_full
        if not os.path.isdir(os.path.split(preview_path)[0]):
            os.makedirs(os.path.split(preview_path)[0])
    command = r"%s %s --ch R,G,B -o %s" % (config['magick'], input_file, preview_path)
    if command:
        _execute(command)
    return preview_path


def make_images_from_pdf(input_file, preview_path=None):
    # This requires imagemagick as well as ghostscript.  this is on hold until i understand better how
    # the licensing for ghostscript works and how we'd package it.
    if not preview_path:
        preview_path = PathObject(input_file).preview_path_full
        if not os.path.exists(os.path.split(preview_path)[0]):
            os.makedirs(os.path.split(preview_path)[0])
    name = os.path.splitext(os.path.split(input_file)[-1])[0]
    output_file = name + '.%04d.jpg'
    command = r"%s -density 300 %s %s/%s" % (config['imagemagick'], input_file,
                                             os.path.split(input_file)[0], output_file)
    if command:
        _execute(command)
    return True


def get_thumb_res(input_file):
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
    res = get_thumb_res(input_file)
    width, height = res.split('x')
    create_hd_proxy(input_file, output_file, width=width, height=height)


def make_animated_gif(input_file):
    input_file = input_file.replace('####', '%04d')
    h, _ = thumb_res.split('x')
    # palette = PathParser.thumbpath_from_path(input_file)
    palette = PathObject(input_file).thumb_path_full
    path_, _ = os.path.splitext(palette)
    ext = '.palette.png'
    palette = path_+ext
    if os.path.exists(palette):
        os.remove(palette)
    # output_file = PathParser.thumbpath_from_path(input_file.replace('%04d', 'seq'))
    output_file = PathObject(input_file.replace('%04d', 'seq')).thumb_path_full
    ext2 = '.gif'
    path_, _ = os.path.splitext(output_file)
    output_file = path_+ext2
    if not os.path.exists(os.path.dirname(output_file)):
        os.makedirs(os.path.dirname(output_file))
    else:
        if os.path.exists(output_file):
            os.remove(output_file)
    filters = "fps=15,scale=%s:-1:flags=lanczos" % h
    command = '%s -i %s -vf "%s,palettegen" -y %s' % (config['ffmpeg'], input_file, filters, palette)
    print command
    p = subprocess.Popen([config['ffmpeg'], '-i', input_file, '-vf', "%s,palettegen" % filters, '-y', palette],
                         stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=subprocess.STDOUT)
    print p.stdout.readline()  # read the first line
    for i in range(10):  # repeat several times to show that it works
        print >> p.stdin, i  # write input
        p.stdin.flush()  # not necessary in this case
        print p.stdout.readline(),  # read output
    print p.communicate("n\n")[0],
    p.wait()

    command2 = '%s -i %s -i %s -lavfi "%s [x]; [x][1:v] paletteuse" -y %s' \
               % (config['ffmpeg'], input_file, palette, filters, output_file.replace('palette.', ''))
    print 'command 2', command2
    p2 = subprocess.Popen([config['ffmpeg'], '-i', input_file, '-i', palette, '-lavfi',
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

