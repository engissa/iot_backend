import paho.mqtt.client as mqtt
import time
import json
from datetime import datetime
import requests
import sys
from core import senMsg as sm
from core import iotDevice as sd
from node import confUpdater as cu
import RPi.GPIO as GPIO


class ActuatorApp(object):
    ''' Class used to manage the actuator application '''
    def __init__(self, portPI=4):
        '''
        1- get device info and rc address from conf file
        2- attach device
        3- get broker address 
        4- start listening
        '''
        print('initializing the SanoAtmo Sensor Application')
        self.isConnected = False
        self.isRegistered = False
        self.broker_address = None
        self.action_topic = None
        self.port = 1883
        self.conf = cu.confUpdater(type="actuator",fileName="confActuator.json")
        self.rc_address = self.conf.rc_address
        self.device = self.conf.device
        self._attach()
        self._confBroker()
        self._confTopic()
        self.time_switching=10000
        self.client = mqtt.Client(self.device.dev_id)
        self.portPI=portPI
        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.portPI, GPIO.OUT)
    def _confTopic(self):
        while True:
            try:
                bi_raw = requests.get(self.rc_address + 'services/action_topic')
                res = json.loads(bi_raw.text)
                if res['success']:
                    self.action_topic = res['result']["topic"]
                break
            except Exception as e:
                print('could not get the topics')
                time.sleep(5)
                pass

    def _confBroker(self):
        '''function to retrieve the broker information and store it in the object'''
        print('Contacting Service Catalog...')
        while True:
            try:
                bi_raw = requests.get(self.rc_address + 'services/broker')
                conf = json.loads(bi_raw.text)
                tempBroker = conf['result']
                self.broker_address = tempBroker['address']
                self.port = tempBroker['port']
                break
            except Exception as e:
                print(e)
                time.sleep(5)       #TODO change time to 30
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

    def _on_message(self,client,userdata,msg):
        '''
        function to retrive the message subscribed to and control actuators according to the action received.
        Once it has been switched on, the actuator can be switched off only after 5 minutes.
        '''
        res = json.loads(msg.payload)
        self.time_threshold=res["w_time"]
        if res["action"]=="on":
            if  GPIO.input(self.portPI):  #TODO only one statement when we connect leds
                pass
            else:
                GPIO.output(self.portPI, 1)
                self.time_switching=time.time()
                print ("switched LED on")
        else:
            if (int(time.time()-self.time_switching)>int(self.time_threshold)):
                print ("turning off")
            if GPIO.input(self.portPI):    #TODO only one statement when we connect leds
                print("switched LED off")
                GPIO.output(self.portPI, 0)
            else:
                pass


    def start(self):
        '''
        function to start the application subscribing to the topic act/[actuator id]
        '''
        print('Connecting to Broker and starting transmittion')
        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect
        self.client.on_message=self._on_message
        self.client.connect(self.broker_address, port=int(self.port))
        print ("broker address: "+self.broker_address)
        self.client.subscribe(str(self.action_topic+self.device.dev_id), 0)
        self.client.loop_forever()
        while not self.isConnected:
            time.sleep(0.1)


    def disconnect(self):
        self.client.disconnect()
        self.client.loop_stop()
        print("\nConnection Closed")

    def _attach(self):
        '''
        function to add the device to the resource catalog if it isn't already registered
        '''
        print (self.isRegistered)
        while not self.isRegistered:
            try:
                print (self.device.toJson())
                # Check if device is registerd
                bi_raw = requests.get(self.rc_address +
                                      'device/actuator/' + self.device.dev_id)
                res = json.loads(bi_raw.text)
                if res['success']:
                    self.isRegistered = True
                    res_raw = requests.post(self.rc_address +
                                            'device/actuator',
                                            self.device.toJson())
                    response = json.loads(res_raw.text)
                    if response['success']:
                        self.isRegistered = True
                    else:
                        pass
                elif not res['success']:
                    res_raw = requests.put(self.rc_address +
                                           'device/actuator/',
                                           self.device.toJson())
                    response = json.loads(res_raw.text)
                    if response['success']:
                        self.isRegistered = True
                else:
                    pass

            except Exception as e:
                print(e)
                print("Could not register device trying in 30 seconds")
                time.sleep(5)
                pass

if __name__ == '__main__':
    actuatorapp = ActuatorApp()
    actuatorapp.start()
