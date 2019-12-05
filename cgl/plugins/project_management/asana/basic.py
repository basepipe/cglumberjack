import asana


class AsanaJack(object):
    project_data = None
    workspace_data = None
    section_data = None
    task_data = None
    users_data = None

    def __init__(self, work_space='CG Lumberjack'):
        # TODO - change this over to the "APP" rather than individual user token, this will only work for Tom currently.
        lmill_token = '0/a0bcee9eaec3882d7d15112eb13dac4b'
        self.workspace_name = work_space
        # create the asana client
        self.client = asana.Client.access_token(lmill_token)
        # Get your user info
        self.me = self.client.users.me()  # this assumes i'm logged in as tom.
        for workspace in self.me['workspaces']:
            if workspace['name'] == self.workspace_name:
                self.workspace_data = workspace
        if not self.workspace_data:
            return

    def find_workspaces(self):
        """
        Find all workgroups available to us.
        :return:
        """
        return self.me['workspaces']

    def find_users(self):
        return self.client.users.find_by_workspace(self.workspace_data['gid'], iterator_type=None)

    def find_projects(self):
        return self.client.projects.find_by_workspace(self.workspace_data['gid'], iterator_type=None)

    def find_project_data(self, project_name):

        projects = self.client.projects.find_by_workspace(self.workspace_data['gid'], iterator_type=None)
        for p in projects:
            if p['name'] == project_name:
                self.project_data = p
                return self.project_data
        return None

    def find_section_data(self, project_name, section_name):
        self.find_project_data(project_name)
        sections = self.client.sections.find_by_project(self.project_data['gid'])
        for s in sections:
            if s['name'] == section_name:
                self.section_data = s
                return s
        return None

    def find_task_data(self, project_name, task_name):
        self.find_project_data(project_name)
        tasks = self.client.tasks.find_by_project(self.project_data['gid'])
        for t in tasks:
            if t['name'] == task_name:
                self.task_data = t
                return t
        return None

    def create_project(self, project_name, create_sections=True):
        project = self.find_project_data(project_name)
        if not project:
            self.project_data = self.client.projects.create_in_workspace(self.workspace_data['gid'],
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
            self.section_data = self.client.sections.create_in_project(self.project_data['gid'], {'name': section_name})
            return self.section_data

    def create_task(self, project_name, section_name, task_name, tag_names=None, assignee_name=None, notes=''):
        project = self.find_project_data(project_name)
        section = self.find_section_data(project_name, section_name)
        self.task_data = self.find_task_data(project_name, task_name)

        # For loop used to iterate through the array of tag names and assign each one to a tag object
        tag_array = []
        tag_list = []
        for t in tag_names:
            tags = self.client.tags.create_in_workspace(self.workspace_data['gid'], {'name': t})
            tag_array.append(tags)

        for t in tag_array:
            tag_list.append(t['gid'])

        assignee_list = self.client.users.find_by_workspace(self.workspace_data['gid'], iterator_type=None)
        for a in assignee_list:
            if a['name'] == assignee_name:
                assignee = a['gid']

        if not self.task_data:
            self.task_data = self.client.tasks.create({'name': task_name,
                                                       'html_notes': notes,
                                                       'assignee': assignee,
                                                       'memberships': [{"project": project['gid'],
                                                                        "section": section['gid']}],
                                                       'projects': [project['gid']],
                                                       'tags': tag_list
                                                       })
            return self.task_data

    def create_note(self, task_description, software=None, language=None, deliverable=None, code_location=None,
                    delivery_method=None, requirements=None, expected_results=None, resources=None):
        """
        Formats a Note according to the CGLumberjack task requirements.
        examples:
        section_one = "<strong>This is a Title:</strong>  This is not"
        ordered_list_items = "<ol><li>Item One</li><li>Item two</li><li>Item three</li></ol>"
        unordered_list_items = "<ul><li>Item One</li><li>Item two</li><li>Item three</li></ul>"
        section_two = '<strong>This is a Title:</strong> This is not a title'
        italic_text = '<em>this is italic text</em>'
        underline_text = '<u>this is underline text</u>'
        strikethrough_text = '<s>this is strikethrough text</s>'
        code_text = '<code>    print "this is code text"</code>'
        link_text = 'This is a link: <a href="http://www.google.com">"Google"</a>, asana only displays whats in href'

        :param software:
        :param language:
        :param deliverable:
        :param code_location:
        :param del_method:
        :param requirements:
        :param expected_results:
        :param resources:
        :return: rich text string for use as a note within the self.create_task script.
        """
        rtf_software = self.rtf_label('Software', software)
        rtf_language = self.rtf_label('Language', language)
        rtf_deliverable = self.rtf_label("Deliverable", deliverable)
        rtf_delivery_method = self.rtf_label("Delivery Method", delivery_method)
        info_line = "%s, %s\n\n" % (rtf_software, rtf_language)
        rtf_task_description = "<strong>Task Description:</strong>\n\t%s\n\n" % task_description
        rtf_code_location = "<strong>Code Location:</strong>\n\t<code>%s</code>\n\n" % code_location
        rtf_requirements = self.rtf_bullet_list('Requirements:', requirements)
        rtf_expected_results = self.rtf_bullet_list('Expected Results:', expected_results)
        rtf_deliverables = self.rtf_bullet_list("What You'll Deliver:", [rtf_deliverable, rtf_delivery_method])
        return "<body>%s%s%s%s%s%s</body>" % (info_line, rtf_task_description, rtf_code_location, rtf_requirements,
                                              rtf_expected_results, rtf_deliverables)

    @staticmethod
    def rtf_label(bold_text, regular_text):
        if regular_text:
            return "<strong>%s: </strong>%s" % (bold_text, regular_text)
        else:
            return "<strong>%s:</strong>%s" % (bold_text, 'Not Defined')

    @staticmethod
    def rtf_bullet_list(bold_label, bullet_list):
        if bullet_list:
            rtf_ul = "<strong>%s</strong>\n<ul>" % bold_label
            for each in bullet_list:
                rtf_ul += "<li>%s</li>" % each
            rtf_ul += "</ul>\n"
            return rtf_ul
        else:
            return "<strong>%s</strong>\n" % bold_label

    def delete_section(self, project_name, section_name):
        section_data = self.find_section_data(project_name, section_name)
        if section_data:
            self.client.sections.delete(section_data['id'])
