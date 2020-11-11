def create_tt(duration, tt_object):
    """

    :param length: duration of the turntable
    :param tt_object: object to create the turntable around
    :return:
    """
    pass


def clean_tt():
    pass


def confirm_prompt(title='title', message='message', button='Ok'):
    """
    standard confirm prompt, this is an easy wrapper that allows us to do
    confirm prompts in the native language of the application while keeping conventions
    :param title:
    :param message:
    :param button: single button is created with a string, multiple buttons created with array
    :return:
    """
    pm.confirmDialog(title=title, message=message, button=button)


def get_hdri_json_path():
    hdri_json = CONFIG['paths']['resources']
    return os.path.join(hdri_json, 'hdri', 'settings.json')


def hdri_widget():
    """"
    Launches an hdri widget that allows us to choose which hdri we want in our scene.
    """
    d = load_json(get_hdri_json_path())
    # window = pm.window()
    # pm.columnLayout()
    # pm.optionMenu(label='Colors', changeCommand=create_env_light)
    # for each in d.keys():
    #     pm.menuItem(label=each)
    # pm.showWindow(window)


def create_env_light(tex_name):
    """
    creates an env light with texture: tex_name
    :param tex_name:
    :return:
    """
    pass
