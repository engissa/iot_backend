import cherrypy
import os, os.path

from node import confUpdater as cu

WS_PORT = 8585
WS_ADDRESS = "0.0.0.0"
@cherrypy.expose
class ConfigurationWebService(object):
    '''
    local webserver to enable the user to update device configuration through 
    web interface
    '''
    exposed = True

    def __init__(self):
        self.conf_updater = cu.confUpdater()

    def GET(self, ):
        url = (os.path.abspath(os.getcwd())) + '/resources/conf.html'
        return open(url, 'r').read()

    def POST(self, *uri, **params):
        self.conf_updater.update_rc_address(params["ip_address"])
        url = (os.path.abspath(os.getcwd())) + '/resources/confSuccess.html'
        #restart rpi
        return open(url, 'r').read()


if __name__ == '__main__':
    conf = {
        '/': {
            'request.dispatch': cherrypy.dispatch.MethodDispatcher(),
            'tools.staticdir.root': os.path.abspath(os.getcwd()),
            'tools.staticdir.on': True,
            'tools.staticdir.dir': './resources'
        },
        '/static': {
            'tools.staticdir.on': True,
            'tools.staticdir.dir': 'resources'
        }

    }

    cherrypy.tree.mount(ConfigurationWebService(), '/', conf)
    cherrypy.server.socket_host = WS_ADDRESS
    cherrypy.server.socket_port = WS_PORT
    cherrypy.engine.start()
    cherrypy.engine.block()
