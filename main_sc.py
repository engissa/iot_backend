import json
import cherrypy
import sys
from core import dbconnector_sc as sc
from core import iotDevice as sd


@cherrypy.expose
class scWebservice(object):
    '''
    Service Catalog MicroService class
    '''
    def __init__(self):
        self.sc = sc.serviceCatalog()

    def GET(self, *uri, **params):
        '''
        - device/<device_type>/<device_id>
        - device/<device_type>
        - services/all || <service_name>
        '''
        res = None
        try:
            if uri[0] == 'device' and len(uri) == 3:
                # Find device by type and id
                device_type = str(uri[1])
                device_id = str(uri[2])
                res = self.sc.get_device(device_type, device_id)
            elif uri[0] == 'device' and len(uri) == 2:
                # Find all devices by type
                device_type = str(uri[2])
                res = self.sc.get_devices(device_type)
            elif uri[0] == 'services' and len(uri) == 2:
                if uri[1] == 'all':
                    res = self.sc.get_services()
                else:
                    s_type = uri[1]
                    res = self.sc.get_setting(s_type)

        except Exception as e:
            res = str(e)
        print(res)
        if res:
            return res
        else:
            return self._responsJson('Bad Request', False)

    def PUT(self, *uri, **params):
        '''
        /device/<device_type>
        accept Device object in JSON format
        '''
        res = None
        try:
            if uri[0] == 'device' and len(uri) == 2:
                device_type = str(uri[1])
                try:
                    tempJson = json.loads(cherrypy.request.body.read())
                    tempDevice = sd.iotDevice()
                    tempDevice.fromJson(tempJson)
                    res = self.sc.add_device(device_type, tempDevice, True)
                except Exception as e:
                    res = self.sc._responsJson('Cannot add device:' +str(e), False)
        except Exception as e:
            res = None
        if res:
            return res
        else:
            return self._responsJson('Bad Request', False)

    def POST(self, *uri, **params):
        '''
        HTTP POST REQUEST
        device/<device_type>
        accept Device object in JSON format
        '''
        res = None
        try:
            if uri[0] == 'device' and len(uri) == 2:
                device_type = str(uri[1])
                try:
                    tempJson = json.loads(cherrypy.request.body.read())
                    tempDevice = sd.iotDevice()
                    tempDevice.fromJson(tempJson)
                    res = self.sc.add_device(device_type, tempDevice, False)
                except Exception as e:
                    res = self.sc._responsJson('Cannot update device: '+str(e), False)
        except Exception as e:
            res = None
        if res:
            return res
        else:
            return self._responsJson('Bad Request', False)

    def _responsJson(self, result, success):
        ''' function to handle the format of response messages '''
        tempJson = {'result': result, 'success': success}
        return json.dumps(tempJson)


if __name__ == '__main__':
    conf = {
        '/': {
            'request.dispatch': cherrypy.dispatch.MethodDispatcher(),
            'tools.sessions.on': True
        }
    }
    cherrypy.tree.mount(scWebservice(), '/catalog', conf)
    cherrypy.server.socket_host = "0.0.0.0"
    cherrypy.server.socket_port = 8181
    cherrypy.engine.start()
    cherrypy.engine.block()
