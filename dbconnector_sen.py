import paho.mqtt.client as mqtt
from pymongo import MongoClient
from datetime import datetime
import requests
import time
import json

"""Application GLOBAL CONFIGURATIONS """
MS_ID = 'DBMC'
RC_ADDRESS = 'http://127.0.0.1:8181/catalog/'
##########################

class DBConnector(object):
    '''
    Mongodb Sensor readings connector. read sensor data and store in database
    '''

    def __init__(self, client_id, rc_address):
        self.client_id = client_id
        self.dbclient = MongoClient()
        self.db = self.dbclient.iotdb
        self.rc_address = rc_address
        self.connected = False
        self.broker_address = None
        self.port = 1883
        self.topic = 'readings/#'
        # self._confTopic()
        self._confBroker()
        self.client = mqtt.Client(self.client_id)

    def _confTopic(self):
        while True:
            try:
                # Check if device is registerd
                bi_raw = requests.get(self.rc_address + '/services/reading_topic')
                res = json.loads(bi_raw.text)
                print(res)
                if res['sucess']:
                    self.topic = res['success']['topic']
                    print(self.topic)
                    break
            except Exception as e:
                print('could not get the subscribing topic: '+str(e))
                time.sleep(5)
                pass

    def _confBroker(self):
            ''' function to retrieve the broker
            information and store it in the object'''
            print('Contacting Service Catalog...')
            while True:
                try:
                    # Retrieve broker URL and Port of mqtt broker
                    bi_raw = requests.get(self.rc_address + 'services/broker')
                    print(bi_raw.text)
                    conf = json.loads(bi_raw.text)
                    # Set the broker URL and Port
                    tempBroker = conf['result']
                    self.broker_address = tempBroker['address']
                    self.port = int(tempBroker['port'])
                    break
                except Exception as e:
                    # Retry to reconnect in 30 seconds
                    print(e)
                    time.sleep(5)
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
        print(self.broker_address)
        self.client.connect(self.broker_address, port=self.port)
        self.client.subscribe(self.topic, 2)
        self.client.loop_forever()
        while not self.Connected:
            time.sleep(0.1)

    def on_message(self, client, userdata, msg):
        collection = self.db.sensor
        try:
            print(msg.payload)
            post = json.loads(msg.payload)
            for x in post['e']:
                ddc = {'bn': post['bn'],
                       'bt': datetime.fromtimestamp(post['bt']),
                       'n': x['n'],
                       'u': x['u'],
                       'v': x['v']}
                collection.insert(ddc)
        except Exception as e:
            print("incorrect packet:" + str(e))

    def disconnect(self):
        self.client.disconnect()
        self.client.loop_stop()
        print("\nConnection Closed")


if __name__ == '__main__':
    dbmc = DBConnector(MS_ID, RC_ADDRESS)
    dbmc.start()
