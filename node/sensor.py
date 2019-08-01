""" CODE for the SENSOR """
import paho.mqtt.client as mqtt
import time
import json
from datetime import datetime
import requests
import sys
from core import senMsg as sm
from core import iotDevice as sd
import confUpdater as cu
import bme_sensor as bm

"""Application GLOBAL CONFIGURATIONS """
TOPIC = 'issasensor/'
##########################


class SASensorApp(object):
    ''' 
    Class used to manage the sensor application
    '''
    def __init__(self):
        print('Initializing the SanoAtmo Sensor Application')
        self.isConnected = False
        self.isRegistered = False
        self.topic = None
        self.broker_address = ''
        self.platform_address = ''
        self.port = 1883
        self.conf = cu.confUpdater(type="sensor", fileName="conf.json")
        self.rc_address = self.conf.rc_address
        self.device = self.conf.device
        self._attach()
        self._confBroker()
        self._confPlatform()
        temp_topic = self._get_sensor_topic()
        self.conf.update_topic(temp_topic)
        self.device = self.conf.device
        self.topic=temp_topic
        self.client = mqtt.Client(self.device.dev_id)

    def _confBroker(self):
        '''
        function to retrieve the broker
        information and store it in the object
        '''
        print('Contacting Service Catalog...')
        while True:
            try:
                # Retrieve broker URL and Port of mqtt broker
                print (self.rc_address)
                bi_raw = requests.get(self.rc_address + 'services/broker')
                conf = json.loads(bi_raw.text)
                # Set the broker URL and Port
                tempBroker = conf['result']
                self.broker_address = tempBroker['address']
                self.port = tempBroker['port']
                break
            except Exception as e:
                # Retry to reconnect in 30 seconds
                print(e)
                time.sleep(5)
                pass

    def _confPlatform(self):
        '''
        function to retrieve the broker
        information and store it in the object
        '''
        print('Contacting Service Catalog...')
        while True:
            try:
                # Retrieve broker URL and Port of mqtt broker
                bi_raw = requests.get(self.rc_address + 'services/platform_api')
                conf = json.loads(bi_raw.text)
                # Set the broker URL and Port
                tempPlatform = conf['result']
                self.platform_address = tempPlatform['address']
                break
            except Exception as e:
                # Retry to reconnect in 30 seconds
                print(e)
                time.sleep(5)
                pass

    def _on_disconnect(self, client, userdata, rc):
        if rc != 0:
            self.isConnected = False
            print("Unexpected disconnection.")

    def _on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            print("connected to broker")
            self.isConnected = True
        else:
            print("Connection Failed")

    def start(self):
        print('Connecting to Broker and starting transmittion')
        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect
        self.client.connect(self.broker_address, port=int(self.port))
        self.client.loop_start()
        while not self.isConnected:
            time.sleep(0.1)
        self._start_sensor_reading()

    def _start_sensor_reading(self):
        '''
        fuction to read the values from the bme680 sensor
        '''
        sensor_bme = bm.bme_sensor()
        while True:
            time.sleep(10)                              # TODO change to 60--------------------------------
            reading = sensor_bme.get_readings()
            msg = sensorapp.defmessage(temp=float("{0:.1f}".format(reading["temp"])), humid=reading["humid"].__int__(),
                                       iaq=(reading["iaq"]).__int__(),
                                       time=datetime.utcnow())
            self.send(msg)


    def _get_sensor_topic(self):
        '''
        function to get the topic where the sensor has to publish from the Service Catatalog database
        '''
        print("getting the topic...")
        while True:
            try:
                raw=requests.get(self.platform_address+"sensors/topic/?u="+self.device.dev_id)
                res=json.loads(raw.text)
                if res["success"]:
                    return res["result"]["topic"]
                else:
                    pass
            except Exception as e:
                print (e)
                pass


    def defmessage(self, temp, humid, iaq, time):
        '''
        function to create the message to be published from the sensor
        '''
        tempMsg = sm.senMsg(bn=self.device.dev_id, bt=time)
        tempMsg.addSensor(name='temp', unit='C', value=temp)
        tempMsg.addSensor(name='humid', unit='%', value=humid)
        tempMsg.addSensor(name='iaq', unit='%', value=iaq)
        jsonMsg = tempMsg.toJson()
        return jsonMsg

    def send(self, msg):
        '''
        function to publish the json file through mqtt
        '''
        print ("publishing to : "+self.topic)
        self.client.publish(self.topic, msg)

    def disconnect(self):
        self.client.disconnect()
        self.client.loop_stop()
        print("\nConnection Closed")

    def _attach(self):
        '''
        function to attach the sensor in the resource catalog
        '''
        while not self.isRegistered:
            try:
                bi_raw = requests.get(self.rc_address +
                                      'device/sensor/' + self.device.dev_id)
                res = json.loads(bi_raw.text)
                if res['success']:
                    res_raw = requests.post(self.rc_address +
                                            'device/sensor',
                                            self.device.toJson())
                    response = json.loads(res_raw.text)
                    if response['success']:
                        self.isRegistered = True
                    else:
                        pass
                elif not res['success']:
                    # Device is not registered
                    # FIre a put request to add the device
                    res_raw = requests.put(self.rc_address +
                                           'device/sensor',
                                           self.device.toJson())
                    response = json.loads(res_raw.text)
                    if response['success']:
                        self.isRegistered = True
                else:
                    pass

                time.sleep(5)
            except Exception as e:
                # Retry to reconnect in 30 seconds
                print(e)
                print("Could not register device trying in 30 seconds")
                time.sleep(5)
                pass


if __name__ == '__main__':

    # Create sensor application
    sensorapp = SASensorApp()
    sensorapp.start()
