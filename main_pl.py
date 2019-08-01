import cherrypy
import json
from pymongo import MongoClient
import datetime
from datetime import timedelta
import time
from core import dbconnector_pl as pl

@cherrypy.expose
class platformWebService(object):
    """
    Platform microservice
    """
    exposed = True

    def __init__(self):
        self.dbclient = MongoClient()
        self.db = self.dbclient.iotsys
        self.sc = pl.platformDbConnector()

    def PUT(self, *uri, **params):
        res = None
        error_msg = None
        try:
            if uri[0] == 'houses':
                tempJson = json.loads(cherrypy.request.body.read())
                house_name = tempJson['house_name']
                user_id = tempJson['user_id']
                res = self.sc.add_house(user_id, house_name)
            elif uri[0] == 'rooms':
                tempJson = json.loads(cherrypy.request.body.read())
                house_id = tempJson['house_id']
                room_name = tempJson['room_name']
                res = self.sc.add_room(house_id, room_name)
            elif uri[0] == 'sensors':
                tempJson = json.loads(cherrypy.request.body.read())
                sensor_id = tempJson['sens_id']
                sensor_name = tempJson['sens_name']
                room_id = tempJson['room_id']
                res = self.sc.add_sensor(room_id, sensor_id, sensor_name)
            elif uri[0] == 'actuators':
                tempJson = json.loads(cherrypy.request.body.read())
                sens_id = tempJson['sen_id']
                act_id = tempJson['act_id']
                act_name = tempJson['act_name']
                w_time = tempJson['w_time']
                res = self.sc.add_sensor_actuator(sens_id, act_id,
                                                  act_name, w_time)
            elif uri[0] == 'users':
                tempJson = json.loads(cherrypy.request.body.read())
                user_name = tempJson['user_name']
                pwd = tempJson['pwd']
                res = self.sc.add_user(user_name, pwd)
        except Exception as e:
            res = None
            error_msg = str(e)
        if res:
            return res
        else:
            return self._responsJson('wrong request: ' + error_msg, False)

    def POST(self, *uri, **params):
        res = None
        error_msg = None
        try:
            # Cherry py doesn't support receiving json by GET
            # the user authentication is done by POST method
            if uri[0] == 'userAuth':
                tempJson = json.loads(cherrypy.request.body.read())
                user_name = tempJson['user_name']
                pwd = tempJson['pwd']
                res = self.sc.user_sign_in(user_name, pwd)
            elif uri[0] == 'houses':
                tempJson = json.loads(cherrypy.request.body.read())
                house_id = tempJson['house_id']
                user_id = tempJson['user_id']
                res = self.sc.add_house_user(user_id, house_id)
            elif uri[0] == 'sensors':
                tempJson = json.loads(cherrypy.request.body.read())
                sens_id = tempJson['sens_id']
                sens_name = tempJson['sens_name']
                thresh = tempJson['thresh']
                res = self.sc.update_sensor(sens_id, sens_name, thresh)
        except Exception as e:
            res = None
            error_msg = str(e)
        if res:
            return res
        else:
            res = self._responsJson('wrong Request' + error_msg, False)

    def GET(self, *uri, **params):
        """ GET URL uri parameters """
        #  Can be managed as an array
        # url/analytics/sensorid?
        res = None
        error_msg = None
        try:
            if uri[0] == 'houses':
                user_id = params['u']
                res = self.sc.get_houses(user_id)
            elif uri[0] == 'rooms':
                house_id = params['u']
                res = self.sc.get_rooms(house_id)
            elif uri[0] == 'sensors' and len(uri) == 1:
                room_id = params['u']
                res = self.sc.get_sensors(room_id)
            elif uri[0] == 'sensors' and uri[1] == 'topic':
                sens_id = params['u']
                res = self.sc.get_sensor_topic(sens_id)
            elif uri[0] == 'sensors' and uri[1] == 'threshold':
                sens_id = params['u']
                res = self.sc.get_sensor_threshold(sens_id)
            elif uri[0] == 'actuators' and len(uri) == 1:
                sens_id = params['u']
                res = self.sc.get_sensor_actuators(sens_id)
            elif uri[0] == 'actuators' and uri[1] == 'w_time':
                act_id = params['u']
                sens_id = params['s']
                res = self.sc.get_actuator_wtime(sens_id, act_id)
        except Exception as e:
            res = None
            error_msg = str(e)
        if res:
            return res
        else:
            return self._responsJson('Wrong request: ' + error_msg, False)

    def DELETE(self, *uri, **params):
        res = None
        try:
            if uri[0] == 'actuators':
                sens_id = params['sens_id']
                act_id = params['act_id']
                res = self.sc.delete_actuator(act_id, sens_id)
        except Exception as e:
            res = self._responsJson(str(e), False)
        if res:
            return res
        else:
            return self._responsJson('Wrong request', False)

    def _responsJson(self, result, success):
        tempJson = {'result': result, 'success': success}
        return json.dumps(tempJson)


if __name__ == '__main__':
    CONFIG = {'/': {'request.dispatch': cherrypy.dispatch.MethodDispatcher(),
                    'tools.sessions.on': True,
                    'tools.response_headers.on': True,
                    'tools.response_headers.headers':
                    [('Content-Type', 'application/json')],
                    }}

    cherrypy.tree.mount(platformWebService(), '/platform', CONFIG)
    cherrypy.server.socket_host = "0.0.0.0"
    cherrypy.server.socket_port = 8080
    cherrypy.engine.start()
    cherrypy.engine.block()
