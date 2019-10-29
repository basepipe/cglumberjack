from cglcore.config import app_config
import ftrack_api

server_url = app_config()['project_management']['ftrack']['api']['server_url']
api_key = app_config()['project_management']['ftrack']['api']['api_key']
api_user = app_config()['project_management']['ftrack']['api']['api_user']

ftrack = ftrack_api.Session(server_url=server_url, api_key=api_key, api_user=api_user)


def get_all_projects():
    """
    Function to get a list of all projects for a company in ftrack

    :return: Returns a list of Project Objects
    """
    proj = ftrack.query("Project")
    # for p in proj:
    #     print p['name']
    return proj


def get_all_tasks(proj_name):
    """
    Function to get a list of all tasks for a project in ftrack

    :param proj_name: Name of Project to get info from
    :type proj_name: String
    :return: List of Task Objects
    """
    t = ftrack.query("Task where project.name is '%s'" % proj_name)
    # for task in t:
    #     print task['name']
    return t


project = get_all_projects()
tasks = get_all_tasks("cgl_testProjectA")

