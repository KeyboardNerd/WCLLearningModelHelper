import matplotlib.pyplot as plt
import numpy as np
import math
import sys
import json
import uuid
import random
import time
import datetime
import UnitConverter
class DataParser(object):
	def __init__(self, fileName, deliminator):
		self.fileName = fileName
		self.deliminator = deliminator
	def parse(self, dataBase):
		f = open(self.fileName,'rU')
		lines = map(lambda(string): string.replace('\n',''), f.readlines());
		name = []
		nameRead = False
		endWithDeliminator = False;
		for i in lines:
			endWithDeliminator = (i[-1] == self.deliminator);
			if (len(i) == 0):
				continue
			if not nameRead:
				if endWithDeliminator:
					name = map(lambda(string): string.strip(), i.split(self.deliminator)[:-1])
				else:
					name = map(lambda(string): string.strip(), i.split(self.deliminator)[:])
				nameRead = True
				continue
			if endWithDeliminator:
				current = map(float, map(lambda(string): string.strip(), i.split(self.deliminator)[:-1]))
			else:
				current = map(float, map(lambda(string): string.strip(), i.split(self.deliminator)[:]))
			if (len(current) != len(name)):
				raise Exception("Error Name/Data mismatch" + str(current) + str(name))
			for index in xrange(0,len(current)):
				result = dataBase.insert(clusterName = name[index], data = current[index])
				if (not result):
					raise Exception("cluster name mistach:>" + name[index] +"<")
		f.close()

class DataBaseViewer(object):
	def __init__(self, dataBase):
		self.dataBase = dataBase
	def visualize(self):
		plt.close("all")
		names = self.dataBase.clusterNames()
		names.sort()
		dictSize = self.dataBase.numofClusters()
		size = self.dataBase.minClusterSize()
		cell = int(math.ceil(math.sqrt(dictSize)))
		f, graphs = plt.subplots(cell, cell)
		index = 0
		for i in xrange(0,cell):
			for j in xrange(0,cell):
				if index >= dictSize:
					break;
				graphs[i][j].set_title(names[index])
				graphs[i][j].plot(np.linspace(0, self.dataBase.clusterSize(names[index]),self.dataBase.clusterSize(names[index]) ), np.array(self.dataBase.select(names[index])))
				index += 1
		f.subplots_adjust(hspace=0.5)
		plt.show()
class DataWriter(object):
	def __init__(self, dataBase):
		self.dataBase = dataBase
	def save(self,filename, randomWeight):
		f = open(filename, 'w+')
		A = np.zeros((self.dataBase.minClusterSize(),self.dataBase.numofClusters()))
		i = 0
		names = self.dataBase.clusterNames()
		print names
		currentline = "#"
		weight_position = names.index("weight")
		for n in names:
			currentline += (n+",")
			A[:,i] = np.array(self.dataBase.select(n))
			i+=1
		f.write(currentline[:-1]+"\n")
		x = 0
		start = int(math.floor(random.random()*(len(A)-50)))
		print "random starts from: " + str(start)
		for line in A:
			currentline = ""
			f.write(datetime.datetime.fromtimestamp(x).strftime(':%Y-%m-%d %H%M%S000-0400:'))
			the_index = 0
			for i in line:
				if the_index == weight_position and randomWeight and x>=start and x < start+50:
					print x, i
					i += (random.random()-0.5)*20000 # add about 10% random number
					print i
				currentline += (str(i) + ",")
				the_index += 1
			f.write(currentline[:-1]+"\n")
			x+=1
class DataCluster(object):
	def __init__(self, name, unit=None, type_=None, size=0, key=None):
		if name is None:
			self.name = str(uuid.uuid4().get_hex().upper()[0:6])
		else:
			self.name = name
		if unit is None:
			self.unit = ""
		else:
			self.unit = unit
		if type_ is None:
			self.type = ""
		else:
			self.type = type_
		self.size = size
		if key is None:
			self.key = str(uuid.uuid4().get_hex().upper()[0:6])
		else:
			self.key = key

class DataBase(object):
	# db = [key=Number, value=List]
	# clusters = [key=name, value=DataCluster object]
	# ignoreCase = bool
	def __init__(self, configuration, ignoreCase):
		self.db = {}
		self.clusters = {} # store metadata of a cluster
		if ignoreCase is None:
			self.ignoreCase = False
		else:
			self.ignoreCase = ignoreCase
		self.nextVaild = 0
		self.loadConfiguration(configuration)

	def addData(self, parser):
		parser.parse(self)

	def loadConfiguration(self, configuration, unitConverter=None):
		columns = json.load(open(configuration, 'r'))["columns"]
		for item in columns:
			result = []
			for i in self.clusters.keys():
				if (self.clusters[i].key == item['key']):
					result.append(self.clusters[i])
			if len(result) > 1:
				raise Exception("Multiple key error (only one is allowed)")
			elif len(result) == 0:
				if item['name'] in self.clusters.keys():
					raise Exception("Name Collision: only one name per key")
				else:
					if self.ignoreCase:
						item['name'] = item['name'].lower()
						item['unit'] = item['unit'].lower()
						item['type'] = item['type'].lower()
					self.clusters[item['name']] = DataCluster(item['name'], item['unit'], item['type'], 0, item['key'])
					self.db[item['key']] = []
			else:
				currentCluster = result[0]
				if self.ignoreCase:
					item['name'] = item['name'].lower()
					item['unit'] = item['unit'].lower()
					item['type'] = item['type'].lower()
				new = DataCluster(item['name'], item['unit'], item['type'], currentCluster.size, currentCluster.key)
				if currentCluster.type != new.type:
					raise Exception("Type mismatch")
				del self.clusters[currentCluster.name]
				self.clusters[item['name']] = new
				self.db[new.key] = map(lambda(x): unitConverter.convert(currentCluster.type, currentCluster.unit, new.unit, x), self.db[new.key])
		return True

	def contains(self,clusterName):
		if self.ignoreCase:
			clusterName = clusterName.lower()
		return clusterName in self.clusters.keys()

	def select(self, clusterName, start=None, end=None):
		if self.ignoreCase:
			clusterName = clusterName.lower()
		if self.contains(clusterName):
			if start in range(0, self.clusters[clusterName].size) and end in range(0,self.clusters[clusterName].size):
				return self.db[self.clusters[clusterName].key][start: end]
			elif not start is None and end is None and start in range(0, self.clusters[clusterName].size):
				return self.db[self.clusters[clusterName].key][start : end]
			elif start is None and not end is None and end in range(0, self.clusters[clusterName].size):
				return self.db[self.clusters[clusterName].key][start : end]
			elif start is None and end is None:
				return self.db[self.clusters[clusterName].key][:]
		raise Warning("NO DATA SELECTED: containing check: " + str(self.contains(clusterName)) + "request: ["+str(start)+","+str(end)+"]" + ",cluster length: " + str(self.clusterSize(clusterName))+", expected cluster name: " + clusterName + ",list of clusters: " + str(self.clusterNames()))
		return []
	def drop(self, clusterName):
		# drop a cluster
		if self.ignoreCase:
			clusterName = clusterName.lower()
		if self.contains(clusterName):
			del self.db[self.clusters[clusterName].key]
			del self.clusters[clusterName]

	def update(self, clusterName, offset, newValue):
		# update a value in some cluster
		if self.ignoreCase:
			clusterName = clusterName.lower()
		if self.contains(clusterName):
			if offset in range(0, self.clusters[clusterName].size):
				self.db[self.clusters[clusterName].key][offset] = newValue
				return True
		return False

	def delete(self, clusterName, offset):
		if self.ignoreCase:
			clusterName = clusterName.lower()
		if self.contains(clusterName):
			if offset in range(0, self.clusters[clusterName].size):
				key = self.clusters[clusterName].key
				return self.db[key].remove(self.db[key][offset])
		return False

	def insert(self, clusterName, data):
		if self.ignoreCase:
			clusterName = clusterName.lower()
		if self.contains(clusterName):
			self.clusters[clusterName].size += 1
			self.db[self.clusters[clusterName].key].append(data)
		else:
			return False
		return True

	def clusterSize(self, clusterName):
		if self.ignoreCase:
			clusterName = clusterName.lower()
		if self.contains(clusterName):
			return self.clusters[clusterName].size
		return 0

	def clusterNames(self):
		return map(lambda(x): self.clusters[x].name, self.clusters)

	def numofClusters(self):
		return len(self.clusters)

	def getClusterProperty(self, clusterName):
		if self.ignoreCase:
			clusterName = clusterName.lower()
		return self.clusters[clusterName]
	def getAllClustersSize(self):
		return map(lambda(x): self.clusters[x].size, self.clusters)
	def minClusterSize(self):
		return min(map(lambda(x): self.clusters[x].size, self.clusters))
if __name__ == '__main__':
	x = time.time()
	db = DataBase('ATR72init.json', True)
	viewer = DataBaseViewer(db)
	db.addData(DataParser('data/thetest.csv', ','))
	db.loadConfiguration('ATR72done.json', UnitConverter.UnitConverter('unit.json'))
	DataWriter(db).save('data/thetest.pltdata', False)
	#viewer.visualize()
