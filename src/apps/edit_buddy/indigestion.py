import platform
import os
import psutil
import pandas
import yaml
import datetime
from dateutil import tz
import shutil
import exifread
import copy
from Qt import QtCore, QtGui, QtWidgets
from cglui.widgets import base as CGQ
import sys
from threading import Thread
import time

from cglui import startup

outDir = os.getenv("HOME") + "/Ingest/imports/"


class Listener(Thread):
    def __init__(self, window):
        super(Listener, self).__init__()
        self.window = window
        #self.fileTypes = yaml.load(open(os.getenv("HOME") + "/PycharmProjects/cglumberjack/src/cfg/global_template.yaml"))['ext_map']
        self.fileTypes['.ARW'] = "image"
        self.disks = []
        self.prevDisks = []
        self.data = pandas.DataFrame(columns=["Drive","FileName","FileType","Date","Latitude","Longitude"])

        self.runit = True

    def stop(self):
        self.runit = False

    def run(self):

        while self.runit:
            self.disks = self.getDevs()
            if len(self.disks) != len(self.prevDisks):
                self.newMedia = list(set(self.disks).difference(set(self.prevDisks)))
                if len(self.disks) > len(self.prevDisks):
                    for item in self.newMedia:
                        self.getFiles(item)
                        self.window.message("New Media: " + item + "\nMedia Files on Device: " + str(len(self.data.loc[self.data['Drive'] == item].index)))
                if len(self.disks) < len(self.prevDisks):
                    difference = [x for x in self.prevDisks if x not in self.disks]
                    for x in difference:
                        temp = self.data.loc[self.data['Drive'] != x]
                        self.data = temp
                        self.window.message("Media " + x + " Disconnected")
                self.window.updateDevices(self.data)

            self.prevDisks = self.disks
            time.sleep(1)
    
    def ffprobe(self, file):
        output = os.popen("ffprobe -v quiet -show_entries format_tags=creation_time \"" + file + "\"").read()
        for word in output.split():
            if word != "[FORMAT]" and word != "[/FORMAT]":
                word = word.split('=')[1]
                dateholder = []
                dateholder.append("")
                dateholder.append("")
                dateholder.append("")
                i = 0
                for letter in word:
                    if letter != '-':
                        dateholder[i] += letter
                    else:
                        i += 1
                    if i == 3:
                        break
                ts = datetime.datetime.strptime(dateholder[0]+dateholder[1]+dateholder[2], '%Y%m%d')
                ts = ts.replace(tzinfo=tz.tzutc())
                return ts
        return None

    def parseDir(self, dir):
        file = []
        if os.access(dir, os.R_OK):
            for item in os.listdir(dir):
                item = os.path.join(dir, item)
                if os.access(item, os.R_OK):
                    if os.path.isfile(item):
                        file.append(item)
                    elif os.path.isdir(item):
                        file.extend(self.parseDir(item))
        return file

    def getDeviceList(self):
        return psutil.disk_partitions()

    def listDevicesNix(self):
        disks = self.getDeviceList()
        mounts = []
        for item in disks:
            if item.mountpoint != os.path.abspath(os.sep):
                mounts.append(item.mountpoint)
        return mounts

    def listDeviceWin(self):
        disks = self.getDeviceList()

        return disks

    def getDevs(self):
        disks = []
        if platform.system() == "Windows":
            disks = self.listDeviceWin()
        else:
            disks = self.listDevicesNix()
        return disks

    def getFiles(self, item):
        self.window.message("Getting files from " + item)
        self.mediaContents = self.parseDir(item)
        tempData = {}
        for file in self.mediaContents:
            if os.path.splitext(file)[1].lower() in self.fileTypes.keys() or os.path.splitext(file)[1].upper() in self.fileTypes.keys():
                tempData["Drive"] = item
                tempData["FileName"] = file
                if os.path.splitext(file)[1].lower() in self.fileTypes.keys():
                    tempData["FileType"] = self.fileTypes[os.path.splitext(file)[1].lower()]
                else:
                    tempData["FileType"] = self.fileTypes[os.path.splitext(file)[1].upper()]
                ts = self.get_creation_date(tempData['FileName'])
                tempData['Date'] = (datetime.datetime.utcfromtimestamp(ts).strftime('%Y-%m-%d'))
                temp = pandas.DataFrame(tempData, [0])
                self.data = self.data.append(temp, sort=True, ignore_index=True)

    def get_creation_date(self, path_to_file):
        if platform.system() == 'Windows':
            return os.path.getctime(path_to_file)
        elif platform.system() == 'Darwin':
            stat = os.stat(path_to_file)
            return stat.st_birthtime

    def importFiles(self, items):
        for item in items:
            self.window.message("Importing from " + item)
            if item not in self.allDisks:
                self.getFiles(item)
            
            for file in self.mediaFiles[item]:
                self.window.message("Importing File " + file)
                outPath = os.path.join(outDir, os.path.basename(file))
                shutil.copy(file, outPath)
                self.importTime[item].append(datetime.datetime.now())
                self.outPaths[item].append(outPath)
            self.window.message("Done Importing")
            data = list(zip(self.mediaFiles[item], self.fileType[item], self.dates[item], self.latitude[item], self.longitude[item], self.outPaths[item], self.importTime[item]))
            toImport = pandas.DataFrame(data=data, columns=["LocOnDisk", "Type", "Date Created", "Latitude", "Longitude", "Destination", "ImportTime"])
            toImport.to_csv(os.getenv("HOME") + "/Ingest/" + str(datetime.datetime.now()) + ".csv", index=False)
            self.window.message("Written to " + os.getenv("HOME") + "/Ingest/" + str(datetime.datetime.now()) + ".csv")
    
    def getFileList(self, item):
        return self.mediaFiles[item]

# class ImportBrowser(QtWidgets.QDialog):
class ImportBrowser(CGQ.LJDialog):
    def __init__(self, parent=None, title="Import Media"):
        super(ImportBrowser, self).__init__()

        self.layout = QtWidgets.QVBoxLayout()
        self.mediaList = QtWidgets.QTreeView()
        self.mediaList.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        self.model = QtGui.QStandardItemModel()
        self.mediaList.header().hide()
        self.mediaList.setModel(self.model)

        self.scrollMessages = QtWidgets.QScrollArea()
        self.messages = QtWidgets.QLabel()
        self.scrollMessages.setWidget(self.messages)
        self.scrollMessages.setWidgetResizable(True)
        self.scrollMessages.setFixedHeight(60)

        self.importButton = QtWidgets.QPushButton("Import")
        self.importButton.clicked.connect(self.triggerImport)

        self.layout.addWidget(self.mediaList)
        self.layout.addWidget(self.scrollMessages)
        self.layout.addWidget(self.importButton)
        self.setLayout(self.layout)
        self.lister = Listener(self)
        
        self.lister.start()

        startup.do_maya_gui_init(gui=self)

    def message(self,mess):
        self.messages.setText(self.messages.text()+'\n'+mess)
        self.scrollMessages.verticalScrollBar().setValue(self.messages.height())

    def triggerImport(self):
        disks = []
        for item in self.mediaList.selectedItems():
            disks.append(item.text())
        self.lister.importFiles(disks)

# "Drive","FileName","FileType","Date","Latitude","Longitude"
    def updateDevices(self, devs):
        self.devs = devs
        self.repopulate()

    def repopulate(self):
        self.model.removeRows(0, self.model.rowCount())
        if not self.devs.empty:
            for item in self.devs.Drive.unique():
                temp = QtGui.QStandardItem(item)
                temp.setEditable(False)
                self.model.appendRow(temp)
                byDrive = self.devs.loc[self.devs['Drive'] == item]
                for datet in byDrive.Date.unique():
                    temp2 = QtGui.QStandardItem(str(datet))
                    temp2.setEditable(False)
                    temp.appendRow(temp2)
                    byDate = byDrive.loc[byDrive['Date'] == datet]
                    for ftype in byDate.FileType.unique():
                        temp3 = QtGui.QStandardItem(str(ftype))
                        temp3.setEditable(False)
                        temp2.appendRow(temp3)
                        byType = byDate.loc[byDate['FileType'] == ftype]
                        for file in byType.FileName:
                            temp4 = QtGui.QStandardItem(str(file))
                            temp4.setEditable(False)
                            temp3.appendRow(temp4)

    def closeEvent(self, event):
        self.lister.stop()
        super(ImportBrowser, self).closeEvent(event)


if __name__ == "__main__":
    app = startup.do_gui_init()
    dialog = ImportBrowser()
    dialog.setWindowTitle('Media Ingest')
    dialog.show()
    sys.exit(app.exec_())