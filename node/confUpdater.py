import json
import sys
from core import iotDevice as sd

class confUpdater(object):
    '''
    class to manage the the json configuration file of a device
    '''
    def __init__(self,type=None,fileName="conf.json"):

        self.content=None
        self.rc_address=None
        self.device=None
        self.fileName = fileName

        if (type=="sensor"):
            self.device=sd.iotDevice(dev_type="sensor")
        elif (type=="actuator"):
            self.device=sd.iotDevice(dev_type="actuator")
        else:
            pass
        with open(self.fileName,"r") as jsonfile:
            self.content=json.load(jsonfile)
        self.rc_address=self.content["rc_address"]
        if (type==None):
            self.device=self.content["dev_id"]
        else:
            self.device.fromJson(self.content["device"])

    def update_rc_address(self,rc_address):
        self.rc_address=rc_address
        self._save()

    def update_topic(self,topic):
        for e in self.device.endpoints:
            if e["type"]=="mqtt":
                e["address"]=topic
        self._save()

    def _save(self):

        if (type==None):
            json_file = {
                "rc_address": self.rc_address,
                "dev_id":self.device
            }
        else:
            json_file = {
                "rc_address":self.rc_address,
                "device": self.device.toDict()
            }

        self.content=json_file
        try:
            with open(self.fileName, 'w') as file:
                file.write(json.dumps(self.content))
            return True
        except Exception as e:
            return False


