__author__ = 'hujin'

from zope.interface import implements
from twisted.internet import reactor, protocol
from twisted.internet.defer import Deferred, succeed
from twisted.web.client import Agent, readBody
from twisted.web.http_headers import Headers
from twisted.web.iweb import IBodyProducer


class BeginningPrinter(protocol.Protocol):

    def __init__(self, finished, callback):
        self.finished = finished
        self.callback = callback

    def dataReceived(self, bytes):
        if self.callback is not None:
            self.callback(bytes)

    def connectionLost(self, reason):
        self.finished.callback(None)


def streaming(url, callback, headers={}):
    agent = Agent(reactor)
    d = agent.request(
        'GET',
        url,
        Headers(headers),
        None)

    def cbResponse(response):
        finished = Deferred()
        response.deliverBody(BeginningPrinter(finished, callback))

        return finished

    d.addCallback(cbResponse)

    return d


class StringProducer(object):
    implements(IBodyProducer)

    def __init__(self, body):
        self.body = body
        self.length = len(body)

    def startProducing(self, consumer):
        consumer.write(self.body)
        return succeed(None)

    def pauseProducing(self):
        pass

    def stopProducing(self):
        pass


def request(method, url, body=None, headers={}):
    agent = Agent(reactor)

    if body is not None:
        body = StringProducer(body)

    d = agent.request(
        method,
        url,
        Headers(headers),
        body)

    def cb_request(response):

        if response.code == 204 or response.code == 304:
            response.body = None
            return response

        finished = Deferred()

        def cb_body(body):
            response.body = body
            finished.callback(response)

        def cb_error(err):
            finished.errback(err)

        dd = readBody(response)
        dd.addCallback(cb_body)
        dd.addErrback(cb_error)

        return finished

    d.addCallback(cb_request)

    return d


def get(url, headers={}):
    return request('GET', url, headers)


def post(url, body=None, headers={}):
    return request('POST', url, body, headers)


def delete(url, headers={}):
    return request('DELETE', url, headers)


def put(url, body=None, headers={}):
    return request('PUT', url, body, headers)

