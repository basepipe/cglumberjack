import asana


class AsanaJack(object):
    project_data = None
    workspace_name = 'CG Lumberjack'
    workspace_data = None
    section_data = None
    task_data = None

    def __init__(self):
        lmill_token = '0/a0bcee9eaec3882d7d15112eb13dac4b'  # personal Token for Tom's account - have to change to app
        # create the asana client
        self.client = asana.Client.access_token(lmill_token)
        # Get your user info
        self.me = self.client.users.me()  # this assumes i'm logged in as tom.
        for workspace in self.me['workspaces']:
            if workspace['name'] == self.workspace_name:
                self.workspace_data = workspace
        if not self.workspace_data:
            return

    def find_project_data(self, project_name):
        projects = self.client.projects.find_by_workspace(self.workspace_data['id'], iterator_type=None)
        for p in projects:
            if p['name'] == project_name:
                self.project_data = p
                return self.project_data
        return None

    def find_section_data(self, project_name, section_name):
        self.find_project_data(project_name)
        sections = self.client.sections.find_by_project(self.project_data['id'])
        for s in sections:
            if s['name'] == section_name:
                self.section_data = s
                return s
        return None

    def find_task_data(self, project_name, task_name):
        self.find_project_data(project_name)
        tasks = self.client.tasks.find_by_project(self.project_data['id'])
        for t in tasks:
            if t['name'] == task_name:
                self.task_data = t
                return t
        return None

    def create_project(self, project_name, create_sections=True):
        project = self.find_project_data(project_name)
        if not project:
            self.project_data = self.client.projects.create_in_workspace(self.workspace_data['id'],
                                                                         {'name': project_name,
                                                                          'default_view': 'board'})
            if create_sections:
                self.create_section(project_name, 'Backlog')
                self.create_section(project_name, 'TODO')
                self.create_section(project_name, 'In Progress')
                self.create_section(project_name, 'Review')
                self.create_section(project_name, 'Done')
                self.delete_section(project_name, '(no section)')

            return self.project_data

    def create_section(self, project_name, section_name):
        self.section_data = self.find_section_data(project_name, section_name)
        if not self.section_data:
            self.section_data = self.client.sections.create_in_project(self.project_data['id'], {'name': section_name})
            return self.section_data

    def create_task(self, project_name, section_name, task_name, assignee=None, notes=''):
        project = self.find_project_data(project_name)
        section = self.find_section_data(project_name, section_name)
        self.task_data = self.find_task_data(project_name, task_name)
        if not self.task_data:
            self.task_data = self.client.tasks.create({'name': task_name,
                                                       'html_notes': notes,
                                                       'assignee': assignee,
                                                       'memberships': [{"project": project['gid'],
                                                                        "section": section['gid']}],
                                                       'projects': [project['gid']]})
            return self.task_data

    @staticmethod
    def create_note():
        section_one = "<strong>This is a Title:</strong>  This is not"
        ordered_list_items = "<ol><li>Item One</li><li>Item two</li><li>Item three</li></ol>"
        unordered_list_items = "<ul><li>Item One</li><li>Item two</li><li>Item three</li></ul>"
        section_two = '<strong>This is a Title:</strong> This is not a title'
        italic_text = '<em>this is italic text</em>'
        underline_text = '<u>this is underline text</u>'
        strikethrough_text = '<s>this is strikethrough text</s>'
        code_text = '<code>    print "this is code text"</code>'
        link_text = 'This is a link: <a href="http://www.google.com">"Google"</a>, asana only displays whats in href'

        return "<body>%s%s\n\n%s%s\n%s\n%s\n%s\n%s\n%s</body>" % (section_one, ordered_list_items,
                                                                  section_two, unordered_list_items,
                                                                  italic_text, underline_text, strikethrough_text,
                                                                  code_text, link_text)

    # Deletion Methods

    def delete_section(self, project_name, section_name):
        section_data = self.find_section_data(project_name, section_name)
        if section_data:
            self.client.sections.delete(section_data['id'])


# AsanaJack().create_project('Test Project D')
# print AsanaJack().find_task_data(project_name='Test Project D', task_name='task 1')
# note = AsanaJack().create_note()
# AsanaJack().create_task(project_name='Test Project D', section_name='TODO', task_name='task 22', notes=note)
