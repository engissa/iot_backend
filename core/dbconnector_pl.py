''' Disco Library '''
from pymongo import MongoClient
from bson.objectid import ObjectId
import json
import sys
sys.path.insert(0, '../')
# import iotSensor as ss
# import iotActuator as sa
import iotDevice as sd


class platformDbConnector(object):
    '''
    Class connector with mongodb for platform microservice
    '''

    def __init__(self):
        self.dbclient = MongoClient()
        self.db = self.dbclient.iotsys
        self.json_db = None
        self.sysname = ''

    def add_user(self, user_name, pwd):
        ''' 
        Add new  user 
        '''
        query = self.db.users.find_one({'$and': [
                                        {'user_name': user_name},
                                        {'pwd': pwd}]})
        if query:
            return self._responsJson('User Already in DB', False)
        else:
            query = self.db.users.insert_one({'user_name': user_name,
                                              'pwd': pwd})
            if query:
                return self._responsJson('user added', True)
            else:
                return self._responsJson('Cannot add user', False)

    def user_sign_in(self, user_name, pwd):
        '''
        sign in user , returns user_id 
        '''
        query = self.db.users.find_one({'$and': [
                                        {'user_name': user_name},
                                        {'pwd': pwd}]})
        if query:
            user_id = ObjectId(str(query['_id']))
            tempDict = {'user_id': str(user_id)}
            return self._responsJson(tempDict, True)
        else:
            return self._responsJson('Wrong Credentials', False)

    def get_houses(self, user_id):
        '''
        Return list of houses for a user
        '''
        query = self.db.houses.find({'users.user_id': user_id})
        if query.count() >= 1:
            tempList = []
            for house in query:
                h_id = str(ObjectId(str(house['_id'])))
                tempList.append({'house_id': h_id,
                                 'house_name': house['house_name'],
                                 'users': house['users']})
            return self._responsJson(tempList, True)
        else:
            return self._responsJson('No Result', False)

    def get_rooms(self, house_id):
        '''
        Return list of rooms for a house
        '''
        query = self.db.rooms.find({'house_id': house_id}, {'house_id': 0})
        if query.count() >= 1:
            tempList = []
            for room in query:
                room_name = room['room_name']
                room_id = str(ObjectId(str(room['_id'])))
                tempList.append({'room_name': room_name, 'room_id': room_id})
            return self._responsJson(tempList, True)
        else:
            return self._responsJson('No Result', False)

    def get_sensors(self, room_id):
        '''
        Return list of sensors for a room
        '''
        query = self.db.sensors.find({'room_id': room_id},
                                     {'_id': 0, 'room_id': 0})
        if query.count() >= 1:
            tempList = list(query)
            return self._responsJson(tempList, True)
        else:
            return self._responsJson('NA', False)

    def get_sensor_actuators(self, dev_id):
        '''
        Return List of actuators for an sensor
        '''
        query = self.db.actuators.find({'sens_id': dev_id},
                                       {'_id': 0, 'sens_id': 0})
        res = None
        if query.count() >= 1:
            res = list(query)
        if res:
            return self._responsJson(res, True)
        else:
            return self._responsJson('No Actuators found', False)

    def get_sensor_topic(self, devID):
        '''
        Return subscribing topic of sensor 
        '''
        room = self.db.sensors.find_one({'sensor_id': devID},
                                        {'_id': 0})
        if room:
            room_id = str(room['room_id'])
            house = self.dbclient.iotsys.rooms.find_one(
                {'_id': ObjectId(str(room_id))}, {'_id': 0, 'house_id': 1})
            house_id = str(house['house_id'])
            temptopic = 'readings/' + house_id + '/' + room_id + '/' + devID
            return self._responsJson({'topic': temptopic}, True)
        else:
            return self._responsJson('Device not registered', False)

    def get_sensor_threshold(self, sens_id):
        '''
        Return the sensor threshold
        '''
        query = self.db.sensors.find_one({'sensor_id': sens_id},
                                         {'_id': 0, 'threshold': 1})
        if query:
            return self._responsJson(query, True)
        else:
            return self._responsJson('Cannot get threshold', False)

    def get_actuator_wtime(self, sens_id, act_id):
        '''
        Return the actuator wating time
        '''
        query = self.db.actuators.find_one({'$and': [
                                            {'sens_id': sens_id},
                                            {'act_id': act_id}]},
                                           {'_id': 0})
        if query:
            return self._responsJson(query, True)
        else:
            return self._responsJson('Cannot get wtime', False)

    def add_house(self, user_id, house_name):
        ''' 
        Add new house for a user
        '''
        res = None
        # Check if user is associated with the current house
        # house not found add new one
        tempHouse = {'house_name': house_name,
                     'users': [{'user_id': user_id}]}
        query = self.db.houses.insert(tempHouse)
        if query:
            res = self._responsJson('House added', True)
        if res:
            return res
        else:
            return self._responsJson('Cannot add house', False)

    def add_house_user(self, user_id, house_id):
        '''
        Add an existing house for a user
        '''
        h_id = ObjectId(str(house_id))
        query = self.db.houses.update_one({"_id": h_id},
                                          {'$addToSet':
                                           {"users":
                                            {"user_id": user_id}}})
        if query:
            return self._responsJson('User added to house', True)
        else:
            return self._responsJson('Cannot add user', False)

    def add_room(self, house_id, room_name):
        '''
        Add a room for a house 
        '''
        query = self.db.rooms.insert({'room_name': room_name,
                                      'house_id': house_id})
        if query:
            return self._responsJson('Room added', True)
        else:
            return self._responsJson('Cannot add room', False)

    def add_sensor(self, room_id, sensor_id, sensor_name):
        '''
        Add sensor in a room
        '''
        res = None
        sensor = self.db.sensors.find_one({'sensor_id': sensor_id})
        if sensor:
            # sensor already in registered with another room
            res = self._responsJson('Device already registered', False)
        else:
            query = self.db.sensors.insert({'sensor_name': sensor_name,
                                            'sensor_id': sensor_id,
                                            'room_id': room_id,
                                            'threshold': 90})
            if query:
                res = self._responsJson('Device added', True)
        if res:
            return res
        else:
            return self._responsJson('Cannot add device', False)

    def add_sensor_actuator(self, sens_id, act_id, act_name, w_time):
        '''
        Associate an actuator with a sensor
        '''
        temp_setting = {'sens_id': sens_id,
                        'act_id': act_id,
                        'act_name': act_name,
                        'w_time': int(w_time)}
        query = self.db.actuators.update({'$and':
                                          [{'sens_id': sens_id},
                                           {'act_id': act_id}]},
                                         temp_setting,
                                         upsert=True)
        if query:
            return self._responsJson('Actuator added', True)
        else:
            return self._responsJson('Counld not save DB', False)

    def update_sensor(self, sens_id, sens_name, threshold):
        '''
        Update a sensor
        '''
        query = self.db.sensors.update_one({'sensor_id': sens_id},
                                           {'$set':
                                            {'sensor_name': sens_name,
                                             'threshold': threshold}})
        if query:
            return self._responsJson('Sensor Updated', True)
        else:
            return self._responsJson('Cannot Update Sensor', False)

    def delete_actuator(self, act_id, sens_id):
        '''
        UnAssociate an actuator
        '''
        query = self.db.actuators.delete_one({'$and':
                                              [{'act_id': act_id},
                                               {'sens_id': sens_id}]})
        if query:
            return self._responsJson('Successfully deleted', True)
        else:
            return self._responsJson('Cannot delete', False)

    def _responsJson(self, result, success):
        ''' function to handle the format of response messages '''
        tempJson = {'result': result, 'success': success}
        return json.dumps(tempJson)
