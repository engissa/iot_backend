import json


class iotDevice(object):

    def __init__(self, dev_type=None, device_id='NA'):
        self.dev_id = device_id
        self.updated_on = 0
        self.endpoints = []
        self.resources = []
        self.dev_type = dev_type
        # self.settings = []

    def add_endpoint(self, etype, address, desc, action=None):
        tempEnd = {'type': etype,
                   'action': action,
                   'address': address,
                   'description': desc
                   }

        self.endpoints.append(tempEnd)

    def toDict(self):
        tempDict = {'dev_id': self.dev_id,
                    'dev_type': self.dev_type,
                    'updated_on': self.updated_on,
                    'endpoints': self.endpoints,
                    'resources': self.resources,
                    # 'settings': self.settings
                    }
        return tempDict

    def fromJson(self, jsonfile):
        self.dev_id = jsonfile['dev_id']
        self.dev_type = jsonfile['dev_type']
        self.endpoints = jsonfile['endpoints']
        self.resources = jsonfile['resources']
        self.updated_on = jsonfile['updated_on']
        # self.settings = jsonfile['settings']

    def toJson(self):
        tempJson = json.dumps(self.toDict())
        return tempJson

    def __eq__(self, other):
        # Compare equality of two objects
        eq_state = (self.dev_id == other.dev_id)
        return bool(eq_state)
