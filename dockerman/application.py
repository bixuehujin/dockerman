__author__ = 'hujin'


import sys

from os import path

from twisted.internet import reactor
from twisted.web import server, resource
from twisted.python import log

from dockerman.storage import ServiceStore
from dockerman.api import Root
from dockerman.docker import Client
from dockerman.manager import Manager
from dockerman.event import Dispatcher


class Application(object):

    def __init__(self, config):
        self.config = config

        log.startLogging(sys.stdout)
        self._initialize()

    def _initialize(self):
        store_file = self.config['store_file']
        if not path.exists(store_file):
            open(store_file, 'w').close()

        self.store = ServiceStore(store_file)
        self.store.applicaion = self

        host = self.config['docker_host']
        port = self.config['docker_port']

        self.client = Client(host, port)
        self.dispatcher = Dispatcher(self)

        self.manager = Manager(self.client, self.store, self.dispatcher)

    def get_config(self, name, default=None):
        try:
            return self.config[name]
        except KeyError:
            return default

    def _on_event(self, message):
        self.manager.handle_event(message)

    def start(self, port):
        self.startHttpServer(port)
        self.client.subscribe(self._on_event)
        self.client.monitor()
        reactor.run()

    def startHttpServer(self, port):
        site = server.Site(Root(self))
        reactor.listenTCP(port, site)

