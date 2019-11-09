from src.core.config import app_config

filepath = r'D:/VFX/companies/cgl-fsutests/source/comptestB/shots/SEA/1500/comp/tmikota/000.000/high/SEA_1500_comp.nk'


def command_line_render(filepath, frange, interactive=False):
    if interactive:
        command = '%s -F %s %s' % (app_config()['paths']['nuke'], frange, filepath)
    else:
        command = '%s -F %s -x %s' % (app_config()['paths']['nuke'], frange, filepath)
    print command


