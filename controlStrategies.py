#!/usr/bin/python2.7
import paho.mqtt.client as mqtt
import requests
import sys
import time
import json
from core import iotDevice as sd
from node import confUpdater as cu


class postProcessing(object):
    def __init__(self, hum, temp, iaq, threshold):
        self.hum = hum
        self.temp = temp
        self.iaq = iaq
        self.threshold = threshold

    def computeIndex(self):
        '''
        funcion to compute the index of the air quality
        the indexes are computing considering as ideal values: 25 for temperature and 45 for humidity.
        the index of air quality is computed as the average of the three values.
        '''
        temp_index = (25 - abs(self.temp - 25)) * 100 / 25
        humid_index = (45 - abs(self.hum - 45)) * 100 / 45
        index_total = (humid_index + temp_index + self.iaq) / 3
        print (self.iaq)
        return self.iaq

    def isIndexLow(self):
        '''
        fuction to return True if the index of air quality is under the threshold, False otherwise
        '''
        print("computing index...")
        if self.computeIndex() < self.threshold:
            return True
        else:
            return False


class controlStrategies(object):
    '''
    class to control the actuators-----------------???

    Functions:
    get_actuator()
    get_
    '''


    def __init__(self):
        self.client_id = None
        self.connected = False
        self.broker_address = None
        self.subscribing_topic = None
        self.action_topic = None
        self.platform_address=None
        self.port = 1883
        self.conf = cu.confUpdater(fileName="confCS.json")
        self.rc_address = self.conf.rc_address
        self.client_id = self.conf.device
        self._confBroker()
        self._confPlatform()
        self._confTopic()
        self.client = mqtt.Client(self.client_id)

    def _confTopic(self):
        while True:
            try:
                bi_raw = requests.get(self.rc_address + 'services/reading_topic')
                res = json.loads(bi_raw.text)
                if res['success']:
                    self.subscribing_topic = res['result']["topic"]
                bi_raw = requests.get(self.rc_address + 'services/action_topic')
                res = json.loads(bi_raw.text)
                if res['success']:
                    self.action_topic = res['result']["topic"]
                break
            except Exception as e:
                print('could not get the topics:'+e)
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

    def _confBroker(self):
        ''' function to retrieve the broker information and store it in the object '''
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
                time.sleep(5)
                pass

    def get_actuator(self, sen_id):
        ''' function to retrieve the actuator
        information and store it in the object'''
        print('Contacting Service Catalog for actuator...')
        list_actuators = []
        while True:
            try:
                # Retrieve broker URL and Port of mqtt broker

                bi_raw = requests.get(self.platform_address +
                                      'actuators?u=' + sen_id)
                print("get from " + self.rc_address +
                      'actuators?u=' + sen_id + ":   " + bi_raw.text)

                res = json.loads(bi_raw.text)
                if res["success"]:
                    temp_actuators = res['result']
                    for act in temp_actuators:
                        actuator=self.get_actuator_from_rc(act["act_id"])
                        list_actuators.append(actuator)
                return list_actuators

            except Exception as e:
                # Retry to reconnect in 30 seconds
                print(e)
                time.sleep(5)
                pass

    def get_actuator_from_rc(self,act_id):
        try:
            raw=requests.get(self.rc_address+"device/actuator/"+act_id)
            res=json.loads(raw.text)
            if res["success"]:
                actuator = sd.iotDevice(dev_type="actuator")
                actuator.fromJson(res["result"])
                return actuator
        except Exception as e:
            print (e)
            pass

    def _on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            print("connected to broker")
            self.Connected = True
        else:
            print("Connection Failed")
            self.Connected = False

    def start(self):
        self.client.on_connect = self._on_connect
        self.client.on_message = self.on_message
        print("broker address: " + self.broker_address)
        self.client.connect(self.broker_address, port=int(self.port))
        #print("subscribing to the topic: " + self.subscribing_topic)
        self.client.subscribe(self.subscribing_topic, 0)
        self.client.loop_forever()
        while not self.Connected:
            time.sleep(0.1)

    def on_message(self, client, userdata, msg):
        try:
            hum = 0.0
            temp = 0.0
            iaq = 0.0
            print("payload from the topic: " + msg.topic + ":  " + msg.payload)
            post = json.loads(msg.payload)
            sen_id=post['bn']
            for x in post['e']:
                if x['n'] == "humid":
                    hum = x['v']
                if x['n'] == "temp":
                    temp = x['v']
                if x['n'] == "iaq":
                    iaq = x['v']

        except Exception as e:
            print(e)
            print("incorrect packet")

        print(sen_id)
        threshold = self._get_threshold(sen_id)
        print ("thresh: "+str(threshold))
        print (sen_id)
        PP = postProcessing(hum, temp, iaq, threshold)
        actuators = self.get_actuator(sen_id)
        if len(actuators) > 0:
            if PP.isIndexLow():
                print("Switching actuators on...")
                self.switch_actuators(actuators, "on",sen_id)
            else:
                print("Switching actuators off...")
                self.switch_actuators(actuators, "off",sen_id)
        else:
            print ("no actuators configured")


    def switch_actuators(self, actuators, operation,sen_id):
        '''function to  publish the action to be done to each actuator of the system'''
        print("Switching...")
        for act in actuators:
            for e in act.endpoints:
                if e['action'] == operation:
                    w_time=self._get_wtime(sen_id,act.dev_id)
                    msg = {"action": e['action'],"w_time":w_time}
                    print (msg)
                    print("publishing on topic: " + self.action_topic + act.dev_id)
                    self.client.publish(self.action_topic+act.dev_id, json.dumps(msg),2)
                    print  (msg)

    def disconnect(self):
        self.client.disconnect()
        self.client.loop_stop()
        print("\nConnection Closed")

    def _get_threshold(self,sen_id):
        while True:
            bi_raw = requests.get(self.platform_address+"sensors/threshold?u="+sen_id)   #TODO---------CHECK-----
            res = json.loads(bi_raw.text)
            if res["success"]:
                return res["result"]["threshold"]

    def _get_wtime(self,sen_id,act_id):
        while True:
            bi_raw = requests.get(self.platform_address+"actuators/w_time?u="+act_id+"&"+"s="+sen_id)   #TODO-----CHECK---------
            res = json.loads(bi_raw.text)
            print (res)
            if res["success"]:
                return res["result"]["w_time"]

if __name__ == '__main__':
    dbmc = controlStrategies()
    dbmc.start()
