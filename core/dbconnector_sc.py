from pymongo import MongoClient
import json
import sys
from core import iotDevice as sd


class serviceCatalog(object):
    '''
    Class Connector with mongodb for servicecatalog microservice 

    '''

    def __init__(self):
        self.dbclient = MongoClient()
        self.db = self.dbclient.catalog

    def get_device(self, dev_type, dev_id):
        '''
        Lookup for device by id and type
        Returns device object
        '''
        query = self.db.devices.find_one({'$and':
                                          [{'dev_id': dev_id},
                                           {'dev_type': dev_type}]},
                                         {'_id': 0})
        if query:
            try:
                tempSensor = sd.iotDevice()
                tempSensor.fromJson(query)
                return self._responsJson(tempSensor.toDict(), True)
            except Exception as e:
                return self._responsJson('Wrong Device Json', False)
        else:
            return self._responsJson('Device Not Registered', False)

    def get_devices(self, dev_type):
        '''
        Lookup for devices by type
        Returns device object
        '''
        query = self.db.devices.find({'dev_type': dev_type},
                                     {'_id': 0})
        if query.count() >= 1:
            try:
                tempDevicesList = []
                for device in query:
                    tempDevice = sd.iotDevice()
                    tempDevice.fromJson(device)
                    tempDevicesList.append(tempDevice.toDict())
                return self._responsJson(tempDevicesList, True)
            except Exception as e:
                return self._responsJson('Wrong Device Json', False)
        else:
            return self._responsJson('Device Not Registered', False)

    def get_setting(self, s_type):
        '''
        Return iot system settings 
        '''
        query = self.db.settings.find_one({'type': s_type},
                                          {"_id": 0, "type": 0})
        if query:
            return self._responsJson(query, True)
        else:
            return self._responsJson('cannot get topic', False)

    def get_services(self):
        '''
        Return iot system list of available services
        '''
        query = self.db.settings.find({}, {'_id': 0})
        if query.count() >= 1:
            return self._responsJson(list(query), True)
        else:
            return self._responsJson('Cannot get settings', False)

    def add_device(self, dev_type, tempDev, act):
        '''
        Insert/update device
        act: True => Insert Device
        act: False => Update Device
        '''
        query = self.db.devices.update({'$and':
                                        [{'dev_id': tempDev.dev_id},
                                         {'dev_type': dev_type}]},
                                       tempDev.toDict(), upsert=act)
        if query:
            return self._responsJson('sensor added', True)
        else:
            return self._responsJson('Counld not save DB', False)

    def _responsJson(self, result, success):
        ''' function to handle the format of response messages '''
        tempJson = {'result': result, 'success': success}
        return json.dumps(tempJson)
