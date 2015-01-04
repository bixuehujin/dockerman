__author__ = 'hujin'

import json

from datetime import datetime
from uuid import uuid1


class ServiceStore(object):

    def __init__(self, filename):
        self._services = []
        self._file = filename

        self._load_from_file()

    def _load_from_file(self):
        fd = open(self._file, 'r')
        try:
            self._services = json.load(fd)
        except ValueError:
            pass

        fd.close()

    def _save_file(self):
        fd = open(self._file, 'w')
        json.dump(self._services, fd, indent=True)
        fd.close()

    @classmethod
    def validate_service(cls, service, include_id=False):
        if not isinstance(service, Service):
            raise RuntimeError('The service is invalid')

        if ('id' not in service and include_id) or 'name' not in service or 'image' not in service or 'command' not in service:
            if include_id:
                raise RuntimeError('A service must have id, name, image and command defined')
            else:
                raise RuntimeError('A service must have name, image and command defined')

    def add_service(self, service):
        self.validate_service(service, include_id=True)

        service['created_at'] = str(datetime.now())
        service['status'] = 'stopped'

        self._services.append(service)
        self._save_file()
        return True

    def find_by_id(self, _id):
        for value in self._services:
            if value['id'] == _id:
                return value
        return None

    def find_by_name(self, name):
        ret = []
        for value in self._services:
            if value['name'] == name:
                ret.append(value)

        return ret

    def get_all(self):
        return self._services

    def _make_status_as(self, service, status):
        for value in self._services:
            if value['id'] == service['id']:
                value['status'] = status
                self._save_file()
                return True

        return False

    def stop_service(self, service):
        return self._make_status_as(service, 'stopped')

    def start_service(self, service):
        return self._make_status_as(service, 'running')

    def stop_service_by_id(self, service_id):
        service = self.find_by_id(service_id)
        if service is not None:
            self.stop_service(service)

    def start_service_by_id(self, service_id):
        service = self.find_by_id(service_id)
        if service is not None:
            self.start_service(service)


class Service(dict):
    """
    :var name: The service name
    :var status: stopped, running
    """

