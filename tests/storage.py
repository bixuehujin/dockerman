__author__ = 'hujin'

import json

from os import path
from dockerman.storage import Service, ServiceStore


a = {
    "name": "test",
    "image": "test",
    "version": "v1.0",
    "command": []
}

b = {
    "name": "test2",
    "image": "test",
    "version": "v1.0",
    "command": []
}

serviceA = Service(a)
serviceB = Service(b)

filename = './a.json'

open(filename, 'w').close()

store = ServiceStore(filename)

service_id_a = store.add_service(serviceA)
store.start_service(serviceA)
service_id_a = store.add_service(serviceB)

print(service_id_a)
print(store.find_by_id(service_id_a))

print(store.find_by_name('test'))

print(store.get_all())

