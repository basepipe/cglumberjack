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

outDir = os.getenv("HOME") + "/Ingest/imports/"

class Listener(Thread):
	def __init__(self, window):
		super(Listener, self).__init__()
		# self.diskPaths = []
		self.window = window
		self.mediaFiles = {}
		self.dates = {}
		self.fileType = {}
		self.outPaths = {}
		self.latitude = {}
		self.longitude = {}
		self.importTime = {}
		self.allDisks = []
		self.data = pandas.DataFrame()
		self.fileTypes = yaml.load(open(os.getenv("HOME") + "/cglumberjack/src/cfg/global.yaml"))['ext_map']
		self.fileTypes['.ARW'] = "image"
		self.disks = self.getDevs()
		self.prevDisks = self.disks
		self.data = pandas.DataFrame(columns=["Drive","FileName","FileType","Date","Latitude","Longitude"])



		for item in self.disks:
			# print item
			self.getFiles(item)

		# self.window.updateDevices(self.mediaFiles)

		self.runit = True

	def stop(self):
		self.runit = False

	def run(self):

		self.window.updateDevices(self.data)
		while self.runit:
			self.disks = self.getDevs()
			if len(self.disks) != len(self.prevDisks):
				self.newMedia = list(set(self.disks).difference(set(self.prevDisks)))
				if len(self.disks) > len(self.prevDisks):
					for item in self.newMedia:
						self.getFiles(item)
						self.window.message("New Media: " + item + "\nMedia Files on Device: " + str(len(self.mediaFiles[item])))

				self.window.updateDevices(self.data)

			self.prevDisks = self.disks
	
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
		# print dir
		# print os.access(dir, os.R_OK)
		if os.access(dir, os.R_OK):
			for item in os.listdir(dir):
				# print item + str(os.path.isdir(item))
				item = os.path.join(dir, item)
				if os.access(item, os.R_OK):
					if os.path.isfile(item):
						file.append(item)
					elif os.path.isdir(item):
						# print item
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
		# elif platform.system() == "Linux":
		else:
			disks = self.listDevicesNix()
		return disks

	def getFiles(self, item):
		if item not in self.allDisks:
			self.allDisks.append(item)
			self.window.message("Getting files from " + item)
			self.mediaContents = self.parseDir(item)
			self.mediaFiles[item] = []
			self.fileType[item] = []
			self.latitude[item] = []
			self.longitude[item] = []
			self.dates[item] = []
			self.importTime[item] = []
			self.outPaths[item] = []
			tempData = {}
			for file in self.mediaContents:
				# tempData = pandas.DataFrame(columns=["Drive","FileName","FileType","Date","Latitude","Longitude"])
				if os.path.splitext(file)[1].lower() in self.fileTypes.keys() or os.path.splitext(file)[1].upper() in self.fileTypes.keys():
					# print file
					# self.diskPaths.append(item)
					# self.mediaFiles[item].append(file)
					tempData["Drive"] = item
					tempData["FileName"] = file
					if os.path.splitext(file)[1].lower() in self.fileTypes.keys():
						# self.fileType[item].append(self.fileTypes[os.path.splitext(file)[1].lower()])
						tempData["FileType"] = self.fileTypes[os.path.splitext(file)[1].lower()]
					else:
						# self.fileType[item].append(self.fileTypes[os.path.splitext(file)[1].upper()])
						tempData["FileType"] = self.fileTypes[os.path.splitext(file)[1].upper()]

					# if self.fileType[item][-1] == "image":
					if tempData['FileType'] == "image":
						f = open(file, 'rb')
						exif = exifread.process_file(f, details=False)
						if 'GPS Latitude' in exif.keys():
							# self.latitude.append(exif['GPS Latitude'])
							# self.longitude.append(exif['GPS Longitude'])
							tempData["Latitude"] = exif['GPS Latitude']
							tempData["Longitude"] = exif['GPS Longitude']
						else:
							# self.latitude[item].append(None)
							# self.longitude[item].append(None)
							tempData["Latitude"] = None
							tempData["Longitude"] = None
						if 'EXIF DateTimeOriginal' in exif.keys():
							# self.dates[item].append(exif['EXIF DateTimeOriginal'])
							tempData['Date'] = exif['EXIF DateTimeOriginal']
						else:
							# self.dates[item].append(None)
							tempData['Date'] = None
						f.close()
					# elif self.fileType[item][-1] == "movie":
					elif tempData['FileType'] == "movie":
						# self.dates[item].append(self.ffprobe(file))
						# self.longitude[item].append(None)
						# self.latitude[item].append(None)
						tempData['Date'] = self.ffprobe(file)
						tempData['Longitude'] = None
						tempData['Latitude'] = None
					else:
						# self.dates[item].append(None)
						tempData['Date'] = None
					# print self.mediaFiles
					# print self.fileType
					# print self.dates
					# print self.latitude
					# print self.longitude
					# else:
					temp = pandas.DataFrame(tempData, [0])
					# self.data.append(temp, ignore_index=True)
					self.data = self.data.append(temp, sort=True, ignore_index=True)
					# print temp
					# print self.data
		else:
			self.window.message("Previously parsed drive " + item)

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

		# self.files = []
		# self.devs = []


		self.layout = QtWidgets.QVBoxLayout()
		self.mediaList = QtWidgets.QTreeView()
		self.mediaList.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
		self.model = QtGui.QStandardItemModel()
		self.mediaList.setModel(self.model)
		self.layout.addWidget(self.mediaList)

		self.scrollMessages = QtWidgets.QScrollArea()
		self.messages = QtWidgets.QLabel()
		self.scrollMessages.setWidget(self.messages)
		self.scrollMessages.setWidgetResizable(True)
		self.scrollMessages.setFixedHeight(60)
		self.layout.addWidget(self.scrollMessages)



		self.importButton = QtWidgets.QPushButton("Import")
		self.importButton.clicked.connect(self.triggerImport)
		self.layout.addWidget(self.importButton)

		self.setLayout(self.layout)
		self.lister = Listener(self)
		
		self.lister.start()

	def message(self,mess):
		self.messages.setText(self.messages.text()+'\n'+mess)
		self.messages.repaint()
		self.scrollMessages.update()
		# self.messages.setText(mess)
		# self.messages.update()
		# self.scrollMessages.update()
		# print self.messages.height()
		self.scrollMessages.verticalScrollBar().setValue(self.messages.height())
		
		
		# self.update()

	def triggerImport(self):
		disks = []
		for item in self.mediaList.selectedItems():
			disks.append(item.text())
		self.lister.importFiles(disks)
# "Drive","FileName","FileType","Date","Latitude","Longitude"
	def updateDevices(self, devs):
		self.devs = devs
		# print devs
		self.repopulate()

	def repopulate(self):
		self.model.removeRows(0, self.model.rowCount())
		# for item in self.devs:
		for item in self.devs.Drive.unique():
			# print item
			temp = QtGui.QStandardItem(item)
			temp.setEditable(False)
			self.model.appendRow(temp)
			for datet in self.devs.loc[self.devs['Drive'] == item].Date.unique():
				print datet
				temp2 = QtGui.QStandardItem(str(datet))
				temp2.setEditable(False)
				temp.appendRow(temp2)
		self.mediaList.update()
		# self.mediaList.clear()
		# for item in self.devs:
			# temp = QtWidgets.QListWidgetItem(item)
			# self.mediaList.addItem(temp)
		# self.mediaList.update()
		# self.update()

	def closeEvent(self, event):
		self.lister.stop()
		super(ImportBrowser, self).closeEvent(event)


if __name__ == "__main__":
	app = QtWidgets.QApplication(sys.argv)
	dialog = ImportBrowser()
	dialog.show()
	sys.exit(app.exec_())