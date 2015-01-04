__author__ = 'hujin'

from dockerman.docker import Client

from twisted.internet import reactor


client = Client('127.0.0.1', 4243)

def on_data(data):
    print(data)

def on_complete(error):
    print(error)
    reactor.callLater(10, do_monitor)



def do_monitor():
    d = client.monitor()
    d.addBoth(on_complete)

client.subscribe(on_data)
do_monitor()

reactor.run()
