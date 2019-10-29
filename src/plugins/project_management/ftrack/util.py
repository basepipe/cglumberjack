from cglcore.config import app_config
import ftrack_api

server_url = app_config()['project_management']['ftrack']['api']['server_url']
api_key = app_config()['project_management']['ftrack']['api']['api_key']
api_user = app_config()['project_management']['ftrack']['api']['api_user']


def get_all_projects(server_url):
    """
    Function to get a list of all projects found in Ftrack at a given server

    :param server_url: A URL for a company in FTrack
    :type server_url: String
    :return: Returns a list of Project Objects
    """
    ftrack = ftrack_api.Session(server_url=server_url, api_key=api_key, api_user=api_user)
    proj = ftrack.query("Project")
    return proj


p = get_all_projects(server_url)
for proj in p:
    print proj['name']
