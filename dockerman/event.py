__author__ = 'hujin'

from twisted.python import log

class Dispatcher(object):

    def __init__(self, app):
        """
        :type app: dockerman.application.Application
        :return:
        """
        self.app = app

    def dispatch(self, event):
        """
        :type event: Event
        :return:
        """
        handlers = self.app.get_config('handlers', {})
        name = event['name']
        if name not in handlers:
            return

        log.msg('Start run handler of %s: %s' % (name, handlers[name]))

        filename = self.app.get_config('handler_path', '') + '/' + handlers[name]

        run_handler(filename, event)



class Event(dict):

    def __init__(self, name, data):
        self['name'] = name
        self['data'] = data



from twisted.internet import protocol, reactor
import json
from os import path


class ProcessProtocol(protocol.ProcessProtocol):

    def __init__(self, event):
        self.event = event
        self.errmsg = ''

    def connectionMade(self):
        self.transport.write(json.dumps(self.event))
        self.transport.closeStdin()

    def outReceived(self, data):
        print data
        self.transport.loseConnection()

    def errReceived(self, data):
        self.errmsg += data

    def processEnded(self, reason):
        print self.errmsg
        print "processEnded, status %d" % (reason.value.exitCode,)
        print "quitting"

def run_handler(handler, event):
    process = ProcessProtocol(event)
    reactor.spawnProcess(process, handler, [path.basename(handler)])
