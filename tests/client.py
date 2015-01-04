__author__ = 'hujin'

import time

from dockerman.docker import Client

from twisted.internet import reactor


client = Client('127.0.0.1', 4243)
d = client.create_container('bixuehujin/blink-db-server:1.0.0', name='test')


def inspect_container(response):
    print(response)
    print("container created\n")

    dd = client.inspect_container(response['Id'])
    dd.addCallback(start_container)
    return dd

def start_container(response):
    print(response)
    print("container inspected\n")

    dd = client.start_container(response['Id'])
    dd.addCallback(stop_container, response)
    return dd

def stop_container(response, info):
    print(response)
    print("container started\n")

    dd = client.stop_container(info['Id'])
    dd.addCallback(remove_container, info)
    return dd

def remove_container(response, info):
    print(response)
    print("container stopped\n")

    dd = client.remove_container(info['Id'])
    dd.addCallback(done)
    return dd


def done(response):
    print("removed\n")


def on_error(error):
    print error

d.addCallback(inspect_container)
d.addErrback(on_error)


reactor.run()
