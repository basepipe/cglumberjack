import os
import glob
import datetime
import pandas as pd
import time
from plugins.preflight.preflight_check import PreflightCheck
from cgl.core.path import PathObject, CreateProductionData, split_sequence, split_sequence_frange
from cgl.core.util import cgl_copy
from cgl.core.config import UserConfig


METHODOLOGY = UserConfig().d['methodology']
FILEPATH = 0
FILENAME = 1
FILETYPE = 2
FRANGE = 3
TAGS = 4
KEEP_CLIENT_NAMING = 5
SCOPE = 6
SEQ = 7
SHOT = 8
TASK = 9
PUBLISH_FILEPATH = 10
PUBLISH_DATE = 11
STATUS = 12


class PublishPlate(PreflightCheck):
    """
    This Class is designed specifically to work with the lumbermill ingest tool.  It expects a lumbermill data frame in order to function.
    This is designed to work with only one selected row at the moment.

    """

    def __init__(self):
        self.pandas_path = self.shared_data['pandas_path']
        self.data_frame = self.shared_data['data_frame'].copy(deep=True)
        if self.shared_data['current_selection']:
            self.current_selection = self.shared_data['current_selection']
        else:
            self.current_selection = None
        self.test = False

    def getName(self):
        pass

    def make_source_file(self, to_path, row):
        source_path = PathObject(to_path)
        source_path.set_attr(context='source')
        source_path.set_attr(filename='system_report.csv')
        dir = os.path.dirname(source_path.path_root)
        # CreateProductionData(dir)
        data = []
        data.append((row["Filepath"], row["Filename"], row["Filetype"], row["Frame_Range"], row["Tags"],
                     row["Keep_Client_Naming"], row["Scope"], row["Seq"], row["Shot"], row["Task"],
                     row["Publish_Filepath"], row["Publish_Date"], row["Status"], row['Parent']))
        df = pd.DataFrame(data, columns=self.shared_data['ingest_browser_header'])
        if not self.test:
            df.to_csv(source_path.path_root, index=False)

    def save_data_frame(self):
        self.data_frame.to_csv(self.pandas_path, index=False)

    def run(self):
        d = datetime.datetime.today()
        current_date = d.strftime('%d-%m-%Y %H:%M:%S')
        for index, row in self.data_frame.iterrows():
            if row['Filename'] == self.current_selection[0][0] and row['Parent'] == self.current_selection[0][-1]:
                if row['Status'] == 'Tagged':
                    from_file = row['Filepath']
                    to_file = row['Publish_Filepath']

                    if row['Filetype'] == 'folder':
                        print 'Copying %s to %s' % (from_file, to_file)
                        # Send this to the Preflights - No matter what basically
                        if not self.test:
                            cgl_copy(from_file, to_file, methodology=METHODOLOGY)
                            CreateProductionData(to_file, json=True)
                        # self.data_frame.at[index, 'Status'] = 'Published'
                        # self.data_frame.at[index, 'Publish_Date'] = current_date
                        # row['Publish_Date'] = current_date
                        # row['Status'] = 'Published'
                        self.make_source_file(to_file, row)

                    elif row['Filetype'] == 'sequence':
                        to_dir = os.path.dirname(to_file)
                        if not self.test:
                            CreateProductionData(to_dir)
                        file_sequence, self.shared_data['frange'] = split_sequence_frange(from_file)
                        print file_sequence
                        from_query = split_sequence(from_file)
                        from_filename = os.path.split(file_sequence)[-1]
                        self.shared_data['published_seq'] = os.path.join(to_dir, from_filename)
                        self.shared_data['publish_file'] = os.path.join(to_dir, from_filename)
                        print 'Copying sequence %s to %s' % (file_sequence, to_dir)
                        cgl_copy(file_sequence, to_dir, methodology=METHODOLOGY)
                        # self.data_frame.at[index, 'Status'] = 'Published'
                        # self.data_frame.at[index, 'Publish_Date'] = current_date
                        # row['Publish_Date'] = current_date
                        # row['Status'] = 'Published'
                        self.make_source_file(to_dir, row)
                    else:
                        print 'FILETYPE =', row['Filetype']
                        if not self.test:
                            print 'Copying %s to %s' % (from_file, to_file)
                            CreateProductionData(os.path.dirname(to_file))
                            cgl_copy(from_file, to_file, methodology=METHODOLOGY)
                            self.shared_data['publish_file'] = to_file
                        # self.data_frame.at[index, 'Status'] = 'Published'
                        # self.data_frame.at[index, 'Publish_Date'] = current_date
                        # row['Publish_Date'] = current_date
                        # row['Status'] = 'Published'
                        self.make_source_file(to_file, row)
                    self.pass_check('Check Passed')
                    if not self.test:
                        self.save_data_frame()

