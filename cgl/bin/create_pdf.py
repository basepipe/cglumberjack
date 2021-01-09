import os
from reportlab.lib.units import inch
from reportlab.pdfgen.canvas import Canvas
from reportlab.platypus import PageBreak
from cgl.core.utils.general import load_json
from cgl.core.config.config import ProjectConfig
import click


class Subtitle(object):
    def __init__(self, canvas, title_origin, word_spacing=0.7, title="Title", text="text", font_size=8, ):
        s1 = canvas.beginText()
        title_x = title_origin[0]
        title_y = title_origin[1]
        s1.setTextOrigin(title_x * inch, title_y * inch)
        s1.setFont("Courier-Bold", font_size)
        s1.textLine(title)
        (x, y) = s1.getCursor()
        canvas.drawText(s1)

        s1_text = canvas.beginText()
        s1_text.setTextOrigin(x + (word_spacing * inch), title_y * inch)
        s1_text.setFont("Courier", font_size)
        s1_text.textLine(text)
        canvas.drawText(s1_text)


class Shot(object):
    ShotPath = None

    def __init__(self, filmback, focal, camera_move, fstop, start, end, scene, template_path, file_out):
        canvas = Canvas(file_out, pagesize=(4 * inch, 5 * inch))

        # Title text and settings
        canvas.setFont("Courier-Bold", 14)
        title = "Scene: "
        scene_text = scene
        canvas.drawCentredString(2 * inch, 4.8 * inch, (title + scene_text))

        # Create subtitles and their text
        Subtitle(canvas, title_origin=[0.5, 4.5], word_spacing=0.7, title="Film Back:", text=filmback, font_size=8)
        Subtitle(canvas, title_origin=[2.5, 4.5], word_spacing=0.87, title="Focal Length:", text=focal, font_size=8)
        Subtitle(canvas, title_origin=[0.5, 4.35], word_spacing=0.83, title="Camera Move:", text=camera_move, font_size=8)
        Subtitle(canvas, title_origin=[3.03, 4.35], word_spacing=0.48, title="F-stop:", text=fstop, font_size=8)
        Subtitle(canvas, title_origin=[0.5, 1.55], word_spacing=0.48, title="Start:", text=start, font_size=8)
        Subtitle(canvas, title_origin=[0.5, 1.35], word_spacing=0.38, title="End:", text=end, font_size=8)

        # Creates the thumbnail
        path = template_path
        print("attempting to create {}".format(path))
        canvas.drawImage(path, 0.5 * inch, 1.7 * inch, width=3.2 * inch, height=2.5 * inch)

        # Notes section and vector lines
        canvas.setFont("Courier-Bold", 8)
        text = "Notes:"
        canvas.drawString(0.5 * inch, 1.15 * inch, text)
        canvas.line(1 * inch, 1.15 * inch, 3.7 * inch, 1.15 * inch)
        canvas.line(0.5 * inch, 0.95 * inch, 3.7 * inch, 0.95 * inch)
        canvas.line(0.5 * inch, 0.75 * inch, 3.7 * inch, 0.75 * inch)
        canvas.line(0.5 * inch, 0.55 * inch, 3.7 * inch, 0.55 * inch)
        canvas.line(0.5 * inch, 0.35 * inch, 3.7 * inch, 0.35 * inch)

        # Updates the pdf file
        self.ShotPath = file_out
        # print(self.ShotPath, r'-----')
        self.save_file(canvas, path)

    def save_file(self, canvas, path):
        canvas.save()
        return path


class StoryBoard(object):

    # Make this accept a path array
    def __init__(self, path_list, director, project_title, output):
        storyboard = Canvas(output, pagesize=(14 * inch, 12 * inch))

        sc = 1
        pc = 1
        for scene in path_list:
            if sc == 1:
                storyboard.drawImage(scene, 0.5 * inch, 5.5 * inch, width=4 * inch, height=5 * inch)
            elif sc == 2:
                storyboard.drawImage(scene, 5 * inch, 5.5 * inch, width=4 * inch, height=5 * inch)
            elif sc == 3:
                storyboard.drawImage(scene, 9.5 * inch, 5.5 * inch, width=4 * inch, height=5 * inch)
            elif sc == 4:
                storyboard.drawImage(scene, 0.5 * inch, 0.5 * inch, width=4 * inch, height=5 * inch)
            elif sc == 5:
                storyboard.drawImage(scene, 5 * inch, 0.5 * inch, width=4 * inch, height=5 * inch)
            elif sc == 6:
                storyboard.drawImage(scene, 9.5 * inch, 0.5 * inch, width=4 * inch, height=5 * inch)
            elif sc == 7:
                storyboard.append(PageBreak())
                sc = 2
                pc = 2
            sc+=1

        # Project Title
        storyboard.setFont("Courier-Bold", 16)
        title = "Project Title:  "
        text = project_title
        storyboard.drawString(3.5 * inch, 11 * inch, (title + text))

        # Director name
        title = "Director:  "
        text = director
        storyboard.drawString(5.7 * inch, 10.65 * inch, (title + text))
        storyboard.save()
        pass


def create_shot_pdfs(json):
    """
    loads json, creates individual boards, then assembles it all as a pdf, finally deletes any unneeded files.
    :param json:
    :return:
    """
    json_dict = load_json(json)
    shotList = []
    i = 1
    for scene in json_dict['Setup']:
        file_out = r"{}/shot_{}.pdf".format(os.path.dirname(json_dict['Setup'][scene]['Thumbnail_Path']), str(i))
        Shot(filmback=json_dict['Setup'][scene]['Filmback'],
             focal=json_dict['Setup'][scene]['lens'],
             camera_move=json_dict['Setup'][scene]['Camera_Move'],
             fstop=json_dict['Setup'][scene]['fstop'],
             start=json_dict['Setup'][scene]['Script_Start'],
             end=json_dict['Setup'][scene]['Script_End'],
             scene=scene,
             template_path=json_dict['Setup'][scene]['Thumbnail_Path'],
             file_out=file_out)
        shotList.append(file_out)
        i += 1

    return shotList


def convert_shot_pdfs_to_png(path_list):
    """
    give us an array of 'pdfs and we create pngs for final pdf assembly
    :param path_list:
    :return:
    """
    convert_list = []
    for path in path_list:
        filein = path
        fileout = path.replace('pdf', 'png')
        # TODO - we should be pulling this from globals
        magick = ProjectConfig.project_config['paths']['magick']
        command = '%s -density 300 "%s" "%s"' % (magick, filein, fileout)
        print('CONVERSION -------\n\t', command)
        os.system(command)
        convert_list.append(fileout)
    return convert_list

@click.command()
@click.option('--json', '-j', default=None)
@click.option('--output', '-o', default=None)
@click.option('--director', '-d', default=None)
@click.option('--project_title', '-p', default=None)
def main(json, output, director='Not Defined', project_title='Not Defined'):
    if json:
        print('Creating Thumb Info for Each Shot...')
        PathList = create_shot_pdfs(json)
        print('Create Individual Pages...')
        ConvertList = convert_shot_pdfs_to_png(path_list=PathList)
        print('Creating Storyboard PDF...')
        StoryBoard(ConvertList, director, project_title, output)
    else:
        print('No json file defined')


if __name__ == "__main__":
    main()

