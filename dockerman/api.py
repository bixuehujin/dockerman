__author__ = 'hujin'

import json

from twisted.internet import reactor
from twisted.web.resource import Resource
from twisted.web.server import NOT_DONE_YET
from twisted.python.failure import Failure


"""
API


GET /services      Get a list of services
GET /services/:id  Get information of a service
PUT /services/:id  Run or Stop a service

"""


class BaseResource(Resource):

    def __init__(self, application):
        """
        :param application:dockerman.application.Application
        :return:
        """
        self.application = application
        Resource.__init__(self)

    def render(self, request):
        content_type = request.getHeader('Content-Type')
        if request.method != 'GET' and not content_type.startswith('application/json'):
            request.setResponseCode(400)
            return 'Invalid Request'
        else:
            return Resource.render(self, request)

    def handle_deferred(self, d, request, code_on_success=200):
        def done(result):
            if isinstance(result, Failure):
                request.write(result.getTraceback())
            else:
                request.setResponseCode(code_on_success)
                request.write(json.dumps(result))
            request.finish()

        d.addBoth(done)


class Root(BaseResource):

    def __init__(self, application):
        BaseResource.__init__(self, application)

        self.putChild('services', ServiceList(self.application))
        self.putChild('events', EventList(self.application))


class ServiceList(BaseResource):

    def getChild(self, path, request):
        return Service(self.application, path)

    def render_GET(self, request):
        services = self.application.store.get_all()
        return json.dumps(services)

    def render_POST(self, request):
        """
        :type request: twisted.web.server.Request
        """
        definition = json.load(request.content)

        d = self.application.manager.create_service(definition)

        self.handle_deferred(d, request, code_on_success=201)

        return NOT_DONE_YET


class Service(BaseResource):

    def __init__(self, application, _id):
        self.id = _id
        BaseResource.__init__(self, application)

    def render_GET(self, request):
        d = self.application.manager.get_service(self.id)

        self.handle_deferred(d, request, code_on_success=200)

        return NOT_DONE_YET


    def render_PUT(self, request):
        """
        :type request: twisted.web.server.Request
        :return:
        """
        command = json.load(request.content)

        if 'status' not in command:
            request.setResponseCode(400)
            return 'Missing required status field'

        if command['status'] not in ['running', 'stopped']:
            request.setResponseCode(400)
            return 'The status: %s is invalid' % str(command['status'])

        if command['status'] == 'running':
            d = self.application.manager.start_service(self.id)
        else:
            d = self.application.manager.stop_service(self.id)

        self.handle_deferred(d, request, code_on_success=200)

        return NOT_DONE_YET


class EventList(BaseResource):

    def render_GET(self, request):
        return "<html>Hello, GET /events!</html>"

