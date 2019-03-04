import exiftool
import os

#TODO I'm going to need to make a dictionary for my big list of stuff i care about and what's needed for every file type....

RAF = ['EXIF:LensModel', 'MakerNotes:RawImageHeight', 'MakerNotes:RawImageWidth', 'EXIF:CreateDate', 'EXIF:ModifyDate',
       'EXIF:SerialNumber', 'Composite:Aperture', 'EXIF:FocalLength', 'EXIF:Make', 'EXIF:Model', 'EXIF:LensMake']
MOV = ['EXIF:LensModel', 'MakerNotes:RawImageHeight', 'MakerNotes:RawImageWidth', 'EXIF:CreateDate', 'EXIF:ModifyDate',
       'EXIF:SerialNumber', 'Composite:Aperture', 'EXIF:FocalLength', 'EXIF:Make', 'EXIF:Model', 'EXIF:LensMake',
       'QuickTime:VideoFrameRate', 'QuickTime:Duration']
R3D = ['ClipName', 'EdgeTC', 'EndEdgeTC', 'TotalFrames', 'FrameHeight', 'FrameWidth', 'Aperture', 'ISO', 'Date',
       'AudioSlate', 'VideoSlate', 'Camera', 'CameraModel', 'CameraPIN', 'MediaSerialNumber', 'LensSerialNumber',
       'FPS', 'AspectRatio', 'Kelvin', 'LensName', 'LensBrand', 'FocalLength', 'Shutter(deg)', 'SensorID', 'SensorName',
       'Take']


def get_meta_data(filein):
    """
    catch all for gathering meta data, tested on:
    R3D, RAF, JPG, MOV
    :param filein:
    :return:
    """
    if filein.endswith('R3D'):
        return get_red_data(filein)
    # File types tested: RAF, JPG
    if isinstance(filein, basestring):
        files = [filein]
    elif isinstance(filein, list):
        files = filein
    with exiftool.ExifTool() as et:
        metadata = et.get_metadata_batch(files)
    return metadata[0]


def get_red_data(filein):
    """
    method for pulling metadata from r3d files.  REDLINE is a command line interface from RED that is required
    for this
    https://www.red.com/downloads/options?itemInternalId=16144
    :param filein:
    :return:
    """
    file_, ext_ = os.path.splitext(filein)
    if ext_.upper() == '.R3D':
        command = r'REDLINE --i %s --printMeta 1' % filein
        d = {}
        for line in os.popen(command).readlines():
            line = line.strip('\n')
            line = line.replace('\t', '')
            line = line.replace(' ', '')
            try:
                key_, value = line.split(':', 1)
                if key_ != 'None':
                   d[key_] = value
            except ValueError:
                pass
        return d


if __name__ == "__main__":
    image_test_file = r'/Volumes/lightroom/Photos/2018/2018-08-25/DSCF6126.RAF'
    test_file = r'/Volumes/lightroom/RED_FOOTAGE/epicw5k-lowlight-ff-24fps/G004_C010_0314CF_001.R3D'
    mov_file = r'/Volumes/lightroom/Photos/2018/2018-08-26/DSCF6364.MOV'
    data_ = get_meta_data(test_file)
    print data_
    for key in data_:
        print key, data_[key]

