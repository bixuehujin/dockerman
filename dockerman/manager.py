__author__ = 'hujin'

import copy

from twisted.python import log
from twisted.internet.defer import succeed, fail
from dockerman.storage import Service
from dockerman.event import Event


class Manager(object):

    def __init__(self, client, store, dispatcher):
        """
        :type client: dockerman.docker.Client
        :type store: dockerman.storage.ServiceStore
        :type dispatcher: dockerman.event.Dispatcher
        :return:
        """
        self.client = client
        self.store = store
        self.dispatcher = dispatcher

    def create_service(self, definition):
        """
        Create a service

        :param definition: The definition of the service to create
        :return: twisted.internet.defer.Deferred
        """

        service = Service(definition)

        try:
            self.store.validate_service(service)
        except RuntimeError as e:
            return fail(e)

        d = self.client.create_container(**definition)

        def success(result):
            service['id'] = str(result['Id'])

            self.store.add_service(service)
            return service

        d.addCallback(success)

        return d

    def start_service(self, _id):
        """
        Start a service

        :param _id: The id of the service
        :return: twisted.internet.defer.Deferred
        """

        service = self.store.find_by_id(_id)
        if service is None:
            return fail(RuntimeError('Service is not exists'))

        d = self.client.start_container(_id)

        def success(result):
            self.store.start_service(service)
            return result

        d.addCallback(success)

        return d

    def stop_service(self, _id):
        """
        Stop a service

        :param _id: The id of the service
        :return: twisted.internet.defer.Deferred
        """

        service = self.store.find_by_id(_id)
        if service is None:
            return fail(RuntimeError('Service is not exists'))

        d = self.client.stop_container(_id)

        def success(result):
            self.store.stop_service(service)
            return result

        d.addCallback(success)

        return d

    def resolve_port(self, ports):
        if ports is None:
            return None

        for key, value in ports.items():
            return key.split('/')[0]
        return None

    def get_service(self, sid):
        service = self.store.find_by_id(sid)
        if service is None:
            return fail(RuntimeError('Service is not exists'))

        service = copy.deepcopy(service)
        d = self.client.inspect_container(sid)

        def success(result):
            service['network'] = {
                'ip': result['NetworkSettings']['IPAddress'],
                'port': self.resolve_port(result['NetworkSettings']['Ports'])
            }
            return service

        d.addCallback(success)

        return d

    def handle_event(self, message):
        if message['status'] not in ['start', 'die']:
            return

        service = self.store.find_by_id(str(message['id']))

        if message['status'] == 'start':
            self._on_container_start(service)
        else:
            self.store.stop_service(service)
            self.dispatcher.dispatch(Event('service.stop', service))

    def _on_container_start(self, service):

        def success(result):
            service['network'] = {
                'ip': result['NetworkSettings']['IPAddress'],
                'port': self.resolve_port(result['NetworkSettings']['Ports'])
            }
            self.store.start_service(service)
            self.dispatcher.dispatch(Event('service.start', service))

        d = self.client.inspect_container(service['id'])
        d.addCallback(success)
