import ftrack_api
import pprint
from cgl.core.config import app_config

# this works but will have to be made more universal in the way that CreateProjectData is.

CONFIG = app_config()


class FTrackReader:
    def __init__(self):
        self.session = ftrack_api.Session(server_url=CONFIG['project_management']['ftrack']['api']['server_url'],
                                          api_key=CONFIG['project_management']['ftrack']['api']['api_key'],
                                          api_user=CONFIG['project_management']['ftrack']['api']['api_user']
                                          )

    def list_projects(self):
        projects = self.session.query('Project where status is active')
        for proj in projects:
            print(proj['name'])

    def read_project(self, project_name):
        assets = self.session.query('AssetBuild where project.name is %s' % project_name)
        sequences = self.session.query('Sequence where project.name is %s' % project_name)

        final_dict = {
            project_name: {
                'shots': {},
                'assets': {}
            }
        }

        for sequence in sequences:
            final_dict[project_name]['shots'][sequence['name']] = {}
            shots = self.session.query(
                'Shot where parent.name is %s and project.name is %s' % (sequence['name'], project_name))
            for shot in shots:
                final_dict[project_name]['shots'][sequence['name']][shot['name']] = {}
                tasks = self.session.query('Task where parent.name is %s' % shot['name'])
                for task in tasks:
                    final_dict[project_name]['shots'][sequence['name']][shot['name']][task['name']] = task['type'][
                        'name']

        for asset in assets:
            final_dict[project_name]['assets'][asset['name']] = {}
            asset_tasks = self.session.query('Task where parent.name is %s' % asset['name'])
            for asset_task in asset_tasks:
                final_dict[project_name]['assets'][asset['name']][asset_task['name']] = asset_task['type']['name']

        pprint.pprint(final_dict)


if __name__ == "__main__":
    this = FTrackReader()
    this.read_project('cgl_unittest')
    this.list_projects()