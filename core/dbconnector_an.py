''' Disco Library '''
from pymongo import MongoClient
import json
import datetime
from datetime import timedelta


class analyticsDbConnector(object):
    '''
    Class for connecting with MongoDB for data analytics microservice
    '''

    def __init__(self):
        self.dbclient = MongoClient()
        self.db = self.dbclient.iotdb
        self.json_db = None
        self.sysname = ''

    def get_data_day_hour(self, sens_id, sens_type):
        '''
        Returns sensor values by day
        '''
        query = self.db.sensor.aggregate(
            [{'$match':
              {'$and':
               [{'bn': sens_id},
                {'n': sens_type},
                {'bt':
                 {'$lt': datetime.datetime.utcnow(),
                  '$gt': datetime.datetime.utcnow() -
                  timedelta(hours=24)}}]}},
             {'$project': {
              'year': {'$year': '$bt'},
              'month': {'$month': '$bt'},
              'day': {'$dayOfMonth': '$bt'},
              'hour': {'$hour': '$bt'},
              'minute': {'$minute': '$bt'},
              'v': True}},
             {'$group': {
              '_id': {
                  'year': '$year',
                  'month': '$month',
                  'day': '$day',
                  'hour': '$hour',
                  'minute': '$minute'},
              'avg': {'$avg': '$v'}}},
              {'$sort' : { 'day' : 1,'hour':1,'minute':1 }}])
        if query:
            tempList = [doc for doc in query]
            return self.mongodbtojson(tempList)
        else:
            return self._responsJson('No Data', False)

    def get_data_week(self, sens_id, sens_type):
        '''
        Returns sensor data by week
        '''
        query = self.db.sensor.aggregate(
            [{'$match':
              {'$and':
               [{'bn': sens_id},
                {'n': sens_type},
                {'bt':
                 {'$lt': datetime.datetime.utcnow(),
                  '$gt': datetime.datetime.utcnow() -
                  timedelta(days=7)}}]}},
             {'$project': {
              'year': {'$year': '$bt'},
              'month': {'$month': '$bt'},
              'day': {'$dayOfMonth': '$bt'},
              'v': True}},
             {'$group': {
              '_id': {
                  'year': '$year',
                  'month': '$month', 'day': '$day'},
              'avg': {'$avg': '$v'}}}])
        if query:
            tempList = [doc for doc in query]
            return self.mongodbtojson(tempList)
        else:
            return self._responsJson('No Data', False)

    def get_data_month(self, sens_id, sens_type):
        '''
        Return sensor data by month 
        '''
        query = self.db.sensor.aggregate(
            [{'$match':
              {'$and':
               [{'bn': sens_id},
                {'n': sens_type},
                {'bt':
                 {'$lt': datetime.datetime.utcnow(),
                  '$gt': datetime.datetime.utcnow() -
                  timedelta(days=30)}}]}},
             {'$project': {
              'year': {'$year': '$bt'},
              'month': {'$month': '$bt'},
              'day': {'$dayOfMonth': '$bt'},
              'v': True}},
             {'$group': {
              '_id': {
                  'year': '$year',
                  'month': '$month', 'day': '$day'},
              'avg': {'$avg': '$v'}}}])
        if query:
            tempList = [doc for doc in query]
            return self.mongodbtojson(tempList)
        else:
            return self._responsJson('No Data Found', False)

    def mongodbtojson(self, mdbList):
        '''
        Function to handle the conversion of MongoDb datetime type
        '''
        def _myconverter(o):
            if isinstance(o, datetime.datetime):
                unixtime = int('{:%s}'.format(o))
                return unixtime
        resp = ''
        if len(list(mdbList)) == 0:
            resp = {'result': None, 'success': False}
        else:
            resp = {'result': list(mdbList), 'success': True}
        return json.dumps(resp, default=_myconverter)

    def _responsJson(self, result, success):
        ''' function to handle the format of response messages '''
        tempJson = {'result': result, 'success': success}
        return json.dumps(tempJson)
