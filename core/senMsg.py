import json
from datetime import datetime
class senMsg(object):
	'''
	class to define the structure of sensor readings
	'''
	
	def __init__(self,bn='',bt = datetime(2000,1,1)):
		self.bn = bn
		self.bt = bt
		self.e = []
	def addSensor(self,name,unit,value):
		tempDict = {'n':name,
		'u':unit,
		'v':value
		}
		self.e.append(tempDict)
	def toDict(self):
		tempDict = {
		'bn':self.bn,
		'bt':self.bt,
		'e':self.e
		}
		return tempDict
	def toJson(self):
		tempJson = self.toDict()
		# Convert datetime object to UNIX timestamp
		# Json doesnt support object type datetime
		tempJson['bt'] = int(tempJson['bt'].strftime('%s'))
		response = json.dumps(tempJson)
		return response
	def fromJson(self,jsonfile):
		self.bn = jsonfile['bn']
		# Convert UNIX timestamp back to datetime object
		self.bt = datetime.fromtimestamp(jsonfile['bt'])
		self.e = jsonfile['e']
