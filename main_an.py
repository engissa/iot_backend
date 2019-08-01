import cherrypy
import json
import datetime
from core import dbconnector_an as an


@cherrypy.expose
class analyticsWebService(object):
    '''
    Anaylitcs microservice class
    '''
    exposed = True

    def __init__(self):
        self.sc = an.analyticsDbConnector()

    def GET(self, *uri, **params):
        """ GET URL uri parameters """
        #  Can be managed as an array
        res = None
        try:
            if uri and 'q' in params and 's' in params:
                sens_id = uri[0]
                period = params['q']
                sens_type = params['s']
                if period == 'day':
                    res = self.sc.get_data_day_hour(sens_id, sens_type)
                elif period == 'week':
                    res = self.sc.get_data_week(sens_id, sens_type)
                elif period == 'month':
                    res = self.sc.get_data_month(sens_id, sens_type)
        except Exception as e:
            # res = self.sc._responsJson('Cannot get data', False)
            res = self.sc._responsJson(str(e), False)
        if res:
            return res
        else:
            return self.sc._responsJson('Wrong Request', False)


if __name__ == '__main__':
    CONFIG = {'/': {'request.dispatch': cherrypy.dispatch.MethodDispatcher(),
                    'tools.sessions.on': True,
                    'tools.response_headers.on': True,
                    'tools.response_headers.headers':
                    [('Content-Type', 'application/json')],
                    }}

    cherrypy.tree.mount(analyticsWebService(), '/analytics', CONFIG)
    cherrypy.server.socket_host = "0.0.0.0"
    cherrypy.server.socket_port = 8383
    cherrypy.engine.start()
    cherrypy.engine.block()
