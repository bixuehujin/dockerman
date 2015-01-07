__author__ = 'hujin'

import json

from dockerman import http

from twisted.internet.defer import succeed, fail


def dict2query(d):
    query = ''
    for key in d.keys():
        if d[key] is not None:
            query += str(key) + '=' + str(d[key]) + "&"
    return query


class Client(object):

    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.callback = None

    def _normalizeUrl(self):
        return 'http://' + self.host + ':' + str(self.port)

    def _resolve_response(self, d):

        def cb_success(response):
            if response.code == 201 or response.code == 200 or response.code == 204:
                if response.body.startswith('{"status":"Pulling repository'):
                    if response.body.rfind('{"errorDetail":{"') >= 0:
                        return fail(Exception(response.body))
                    else:
                        return succeed(True)
                else:
                    return succeed(json.loads(response.body) if response.body is not None else None)
            else:
                return fail(Exception(response.body))

        d.addCallback(cb_success)
        return d

    def create_container(self, image, command=[], name=None, entry_point="", domain_name="", env=None,
                         volumes={}, volumes_from=[], ports={}, links={}):
        body = {
             "Domainname": domain_name,
             "AttachStdin": False,
             "AttachStdout": True,
             "AttachStderr": True,
             "Tty": False,
             "OpenStdin": False,
             "StdinOnce": False,
             "Env": env,
             "Cmd": command,
             "Entrypoint": entry_point,
             "Image": image,
             "Volumes": volumes,
             "WorkingDir": "",
             "NetworkDisabled": False,
             #"MacAddress": "12:34:56:78:9a:bc",
             "ExposedPorts": ports,
             "SecurityOpts": [""],
             "HostConfig": {
               #"Binds":["/tmp:/tmp"],
               "Links": links,
               #"LxcConf":{"lxc.utsname":"docker"},
               #"PortBindings":{ "22/tcp": [{ "HostPort": "11022" }] },
               "PublishAllPorts": False,
               #"Privileged":False,
               #"Dns": ["8.8.8.8"],
               #"DnsSearch": [""],
               "VolumesFrom": volumes_from,
               #"CapAdd": ["NET_ADMIN"],
               #"CapDrop": ["MKNOD"],
               #"RestartPolicy": { "Name": "", "MaximumRetryCount": 0 },
               "NetworkMode": "bridge",
               #"Devices": []
            }
        }

        body = json.dumps(body)

        url = self._normalizeUrl() + '/containers/create'
        if name is not None:
            url += '?name=' + str(name)

        d = http.post(url, body, {
            'Content-Type': ['application/json']
        })

        return self._resolve_response(d)

    def inspect_container(self, container_id):
        d = http.get(self._normalizeUrl() + '/containers/%s/json' % str(container_id))

        return self._resolve_response(d)

    def start_container(self, container_id):
        d = http.post(self._normalizeUrl() + '/containers/%s/start' % str(container_id))
        return self._resolve_response(d)

    def stop_container(self, container_id, wait_seconds=None):
        url = self._normalizeUrl() + '/containers/%s/stop?' % str(container_id) + dict2query({
            't': wait_seconds
        })
        d = http.post(url)
        return self._resolve_response(d)

    def restart_container(self, container_id, wait_seconds=None):
        url = self._normalizeUrl() + '/containers/%s/restart?' % str(container_id) + dict2query({
            't': wait_seconds
        })
        d = http.post(url)
        return self._resolve_response(d)

    def remove_container(self, container_id, remove_volumes=False, force=False):
        url = self._normalizeUrl() + '/containers/%s?' % str(container_id) + dict2query({
            'v': remove_volumes,
            'force': force
        })
        d = http.delete(url)
        return self._resolve_response(d)

    def pull_image(self, name, tag=None):
        kw = {
            'fromImage': name,
            'tag': tag
        }
        url = self._normalizeUrl() + '/images/create?' + dict2query(kw)
        #http.streaming(url, callback, method='POST')
        d = http.post(url)
        return self._resolve_response(d)

    def subscribe(self, callback):
        self.callback = callback

    def monitor(self):
        def cb_data(data):
            data = json.loads(data)
            if callable(self.callback):
                self.callback(data)

        url = self._normalizeUrl() + '/events'
        return http.streaming(url, cb_data)

