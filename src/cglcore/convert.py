import os
import subprocess
import glob
import logging

from cglcore.config import app_config
from cglcore.path import PathObject, CreateProductionData, split_sequence, hash_to_number, get_start_frame, prep_seq_delimiter

# Important note regarding ffmpeg and .h264 encoding:  There was a lot of discussion about whether this is ok
# to be distributing software with .h264 encoding.  I called the law firm that handles licensing and they said that
# as a software provider until we reach 100,000 sales they would never go after us.  Distributing software with ffmpeg
# included in it therefore is perfectly legal.  Once you get to a certain volume of distribution however it needs to be
# paid for.

config = app_config()['paths']
settings = app_config()['default']
thumb_res = settings['resolution']['thumb']
frame_rate = settings['frame_rate']
ext_map = app_config()['ext_map']

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


def get_first_frame(input_file, return_type='string'):
    input_file = input_file.replace('%04d', '*')
    input_file = input_file.replace('####', '*')
    try:
        # td - this will not pass some instances, we'll have to use REGEX eventually
        first_frame = sorted(glob.glob(input_file))[0]
        last_frame = sorted(glob.glob(input_file))[-1]
        start_number = int(first_frame.rsplit(".", 2)[1])
        last_number = int(last_frame.rsplit(".", 2)[1])
        middle_number = (last_number - start_number)/2 + start_number
        middle_string = '%04d' % middle_number
        middle_frame = input_file.replace('*', middle_string)
        if return_type == 'string':
            return first_frame, middle_frame, last_frame
        else:
            return start_number, middle_number, last_number
    except IndexError:
        logging.info('can not find files like {0}'.format(input_file))
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
    return '%sx%s' % (int(d['width']), int(d['height']))


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
    print 'executing command: %s' % command
    p = subprocess.Popen(command,
                         stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT)
    for each in p.stdout:
        each = each.strip()
        try:
            if "ERROR" in each:
                logging.error(each)
        except TypeError:
            pass


def create_proxy(sequence, ext='jpg', start_frame='1001'):
    """
    Creates a Jpeg proxy resolution based off the resolution of the given path.
    :param sequence:
    :param ext:
    :return:
    """
    path_object = PathObject(sequence)
    new_res = '%s%s' % (path_object.resolution, 'Proxy')
    path_object_output = path_object.copy(resolution=new_res)
    output_dir = os.path.dirname(path_object_output.path_root)
    if not os.path.exists(output_dir):
        CreateProductionData(path_object=output_dir)
    if '####' in sequence:
        # replace ### with "*"
        hashes, number = hash_to_number(sequence)
        in_seq = '%s*.%s' % (split_sequence(sequence), path_object.ext)
        out_seq = '%s/%s%s.%s' % (output_dir, os.path.basename(split_sequence(sequence)), number, ext)
        command = '%s %s -scene %s %s' % (config['magick'], in_seq, start_frame, out_seq)
    else:
        sequence = ''
        fileout = ''

    _execute(command)
    return out_seq.replace(number, hashes)


def create_hd_proxy(sequence, ext='jpg', width='1920', height='x1080', do_height=False, start_frame='1001'):
    if do_height:
        res = height
    else:
        res = width
    path_object = PathObject(sequence)
    new_res = 'hdProxy'
    path_object_output = path_object.copy(resolution=new_res)
    output_dir = os.path.dirname(path_object_output.path_root)
    if not os.path.exists(output_dir):
        CreateProductionData(path_object=output_dir)
    if '####' in sequence:
        # replace ### with "*"
        hashes, number = hash_to_number(sequence)
        in_seq = '%s*.%s' % (split_sequence(sequence), path_object.ext)
        out_seq = '%s/%s%s.%s' % (output_dir, os.path.basename(split_sequence(sequence)), number, ext)
        command = '%s %s -scene %s -resize %s %s' % (config['magick'], in_seq, start_frame, res, out_seq)
    else:
        command = 'not a sequence?'
        sequence = ''
        fileout = ''

    _execute(command)
    return out_seq.replace(number, hashes)


def create_gif_proxy(sequence, ext='gif', width='480', height='x100', do_height=False):
    if do_height:
        res = height
    else:
        res = width
    path_object = PathObject(sequence)
    new_res = 'gif'
    path_object_output = path_object.copy(resolution=new_res)
    output_dir = os.path.dirname(path_object_output.path_root)
    if not os.path.exists(output_dir):
        CreateProductionData(path_object=output_dir)
    if '####' in sequence:
        in_seq = '%s*.%s' % (split_sequence(sequence), path_object.ext)
        out_seq = '%s/%s%s' % (output_dir, os.path.basename(split_sequence(sequence)), ext)
        command = '%s %s -resize %s %s' % (config['magick'], in_seq, res, out_seq)
    else:
        sequence = ''
        fileout = ''

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
    if not os.path.exists(output_dir):
        CreateProductionData(path_object=output_dir)
    if '####' in sequence:
        in_seq = '%s*.%s' % (split_sequence(sequence), path_object.ext)
        out_seq = '%s/%sthumb.%s' % (output_dir, os.path.basename(split_sequence(sequence)), ext)
        command = '%s %s -resize %s %s' % (config['magick'], in_seq, res, out_seq)
    else:
        sequence = ''
        fileout = ''

    _execute(command)
    return out_seq


def create_mov(sequence, framerate=settings['frame_rate'], output_frame_rate=None,
               res=settings['resolution']['video_review']):
    start_frame = get_start_frame(sequence)
    input_file = prep_seq_delimiter(sequence, replace_with='%')
    output_file = '%smov' % split_sequence(sequence)
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
    ffmpeg_cmd = r'%s -start_number %s -framerate %s -gamma %s -i %s -s:v %s -b:v 50M -c:v %s -profile:v %s' \
                 r' -crf %s -pix_fmt %s -r %s %s %s' % (config['ffmpeg'],
                                                        start_frame, framerate, gamma, input_file, res, encoder,
                                                        profile, constant_rate_factor, pixel_format,
                                                        output_frame_rate, filter_arg, output_file)
    print ffmpeg_cmd
    p = subprocess.Popen(ffmpeg_cmd, shell=True)
    p.wait()
    return output_file



def make_movie_thumb(input_file, output_file=None, frame='middle', thumb=True):
    # what am i doing here?  Is this just creating a thumbnail?
    if not output_file:
        output_file = PathObject(path_object=input_file).thumb_path_full
    if os.path.exists(output_file):
        os.remove(output_file)
    if get_file_type(input_file) == 'movie':
        print 'movie'
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
        p = subprocess.Popen(command,
                             stdout=subprocess.PIPE,
                             stderr=subprocess.STDOUT)
        for each in p.stdout:
            each = each.strip()
            try:
                if "ERROR" in each:
                    logging.error(each)
            except TypeError:
                pass
        return output_file

    else:
        if get_file_type(input_file) == 'sequence':
            print 'input_file', input_file
            first_frame, middle_frame, end_frame = get_first_frame(input_file)
            if frame == 'middle':
                input_file = middle_frame
            elif frame == 'first':
                input_file = first_frame
            elif frame == 'last':
                input_file = end_frame
        # create the thumbnail
        output_file = output_file.replace('####', 'seq')
        if thumb:
            res = thumb_res
        else:
            res = settings['resolution']['image_review']
        command = r"%s %s --fit %s --ch R,G,B -o %s" % (config['oiiotool'], input_file, res, output_file)
        if not os.path.exists(os.path.dirname(output_file)):
            os.makedirs(os.path.dirname(output_file))
        p = subprocess.Popen(command,
                             stdout=subprocess.PIPE,
                             stderr=subprocess.STDOUT,
                             shell=True)
        for each in p.stdout:
            each = each.strip()
            try:
                if "ERROR" in each:
                    logging.debug(each)
                    logging.error(each)
            except TypeError:
                pass
        logging.info(command)
        return output_file


def make_full_res_jpg(input_file, preview_path=None):
    if not preview_path:
        # preview_path = PathParser.preview_path_from_frame_path(input_file, file_type='image')
        preview_path = PathObject(path_object=input_file).preview_path_full
        if not os.path.isdir(os.path.split(preview_path)[0]):
            os.makedirs(os.path.split(preview_path)[0])
    command = r"%s %s --ch R,G,B -o %s" % (config['oiiotool'], input_file, preview_path)
    p = subprocess.Popen(command,
                         stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT)
    for each in p.stdout:
        each = each.strip()
        try:
            if "ERROR" in each:
                logging.debug(each)
                logging.error(each)
        except TypeError:
            pass
    logging.info(command)
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
    p = subprocess.Popen(command,
                         stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT)
    for each in p.stdout:
        each = each.strip()
        try:
            if "ERROR" in each:
                logging.debug(each)
                logging.error(each)
        except TypeError:
            pass
    logging.info(command)
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


def make_web_mov(input_file, output_file=None, framerate=frame_rate, output_frame_rate=None,
                 res=settings['resolution']['video_review']):
    print input_file
    if get_file_type(input_file) is 'sequence':
        # This section may have to be augmented or replaced to work with something that is licensed to deal with .h264
        if os.path.splitext(input_file)[-1] == '.exr':
            logging.info('applying gamma 2.2 to linear .exr sequence')
            gamma = 2.2
        else:
            gamma = 1

        if not output_file:
            # must be named correctly, in which case we'd need an error message.
            output_file = os.path.splitext(input_file.replace("####.", ''))[0]+'.mov'
            path, file_ = os.path.split(output_file)
            output_file = os.path.join(path, '.preview', file_)
        # code for converting image sequence to web movie
        encoder = "libx264"
        profile = 'high'
        constant_rate_factor = "24"  # i need to test this with stuff that's not created at 24fps -
        pixel_format = 'yuv420p'

        input_file = input_file.replace("%04d", "*")
        input_file = input_file.replace("####", "*")
        if not framerate:
            # i'll want to check the config to see what the frame rate of the show is.
            pass
        if not output_frame_rate:
            output_frame_rate = framerate
        try:
            first_frame = sorted(glob.glob(input_file))[0]
        except IndexError:
            logging.info('can not find files like {0}'.format(input_file))
            return None
        start_number = int(first_frame.rsplit(".", 2)[1])

        input_file = input_file.replace("*", "%04d")
        res_list = res.split('x')
        width = res_list[0]
        height = res_list[1]
        filter_arg = r' -filter:v "scale=iw*min($width/iw\,$height/ih):ih*min($width/iw\,$height/ih),' \
                     r' pad=$width:$height:($width-iw*min($width/iw\,$height/ih))/2:' \
                     r'($height-ih*min($width/iw\,$height/ih))/2" '.replace('$width', width).replace('$height',
                                                                                                     height)
        ffmpeg_cmd = r'%s -start_number %s -framerate %s -gamma %s -i %s -s:v %s -b:v 50M -c:v %s -profile:v %s' \
                     r' -crf %s -pix_fmt %s -r %s %s %s' % (config['ffmpeg'],
                                                            start_number, framerate, gamma, input_file, res, encoder,
                                                            profile, constant_rate_factor, pixel_format,
                                                            output_frame_rate, filter_arg, output_file)
        print ffmpeg_cmd
        return
        if not os.path.isdir(os.path.dirname(output_file)):
            os.makedirs(os.path.dirname(output_file))
        p = subprocess.Popen(ffmpeg_cmd, shell=True)
        p.wait()
        return output_file

    elif get_file_type(input_file) is 'movie':
        if not output_file:
            # output_file = PathParser.preview_path_from_frame_path(input_file)
            output_file = PathObject(input_file).preview_path_full
        # code for converting movie to web movie
        inputfile = '"%s"' % input_file
        if not os.path.isdir(os.path.dirname(output_file)):
            os.makedirs(os.path.dirname(output_file))
        if os.path.isfile(output_file):
            os.remove(output_file)
        output_file = '"%s"' % output_file
        movie_quality = "high444"  # options are: baseline:iPhone, iPhone 3G, old low-end Android devices,
        #                         other embedded players, main:iPhone 3GS, iPhone 4, iPad, low-end Android phones,
        #                         high:Desktop browsers, iPhone 4S+, iPad 2+,
        #                               Android 4.x+ tablets, Xbox 360, Playstation 3
        movie_conversion_speed = 'slow'  # options are: ultrafast, superfast, veryfast, faster, fast, medium,
        #                                slow, slower, veryslow

        bitrate = OPTIONS['1080p'][0]
        bufsize = OPTIONS['1080p'][1]
        vfscale = OPTIONS['1080p'][2]
        # TODO: apparently this is better for audio_options = "libfdk_aac -b:a 128k", but requires a new ffmpeg build
        audio_options = "aac -b:a 128k"
        command = '{0} -i {1} -codec:v libx264 -profile:v {2} -preset {3} -b:v {4} -maxrate {5} ' \
                  '-bufsize {6} -vf scale={7} -threads 0 -codec:a {8} {9}'.format(config['ffmpeg'],
                                                                                  inputfile, movie_quality,
                                                                                  movie_conversion_speed,
                                                                                  bitrate, bitrate, bufsize, vfscale,
                                                                                  audio_options, output_file)

        p = subprocess.Popen(command, shell=True)
        p.wait()
        return output_file

    else:
        pass


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
    print p.stdout.readline(),  # read the first line
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

