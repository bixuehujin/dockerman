#! /usr/bin/env python

import sys
import os
import json
import re
import subprocess

"""
Event handler for configure and reload HAproxy server.

Payload:
{
    "name": "service.start",
    "data": {
        "name": "blink-server",
        "id": "123",
        "attributes": {
            "via_haproxy": true,
            "from_host": "notify.chalk.me",
            "from_port": 80
        }
    }
}
"""

try:
    haproxy_cfg_file = sys.argv[1]
except IndexError:
    haproxy_cfg_file = '/etc/haproxy/haproxy.cfg'

if not os.path.exists(haproxy_cfg_file):
    sys.exit(1)

def get_content():
    fd = open(haproxy_cfg_file, 'r')
    data = fd.read(10000)
    fd.close()
    return data


def save_content(content):
    fd = open(haproxy_cfg_file, 'w')
    fd.write(content)
    fd.close()


class Renderer(object):

    regexp_frontend_section = '(frontend\s+http_in)(.+?)(^\s*backend|\Z)'
    regexp_frontend_section_backend = '(#\s*begin %s\s*#)(.+?)(#\s*end %s\s*#)'

    regexp_backend_section = '(backend\s+%s\n)(.+?)(\Z|backend\s+)'

    def __init__(self, content):
        self.content = content

    def added_backend_server(self, domain, sid, backend):
        name = self._normalize_name(domain)
        self.render_frontend_section_if_needed(name, domain)
        self.render_backend_section_if_needed(name, sid, backend)


    def remove_backend_server(self, sid):
        self.content = re.sub('^\s*server\s+%s\s.+\n' % sid, '', self.content, flags=re.MULTILINE)


    def render_backend_section_if_needed(self, name, sid, backend):
        r = re.search(self.regexp_backend_section % name, self.content, re.DOTALL)

        def replace3(m):
            if re.search('server\s+%s\s+' % name, r.group(2)) is not None:
                return m.group(0)
            else:
                entry = '    server %s %s check' % (sid, backend) + '\n\n'
                return m.group(1) + m.group(2) + entry + m.group(3)

        regexp = self.regexp_backend_section % name
        r = re.search(regexp, self.content, flags=re.DOTALL)
        if r is None:
            self.content += '\n' + self.format_backend_entries(name, sid, backend) + '\n'
        else:
            self.content = re.sub(regexp, replace3, self.content, flags=re.DOTALL)

    def format_backend_entries(self, name, sid, backend):
        lines = ['backend %s' % name]
        lines.append('    balance leastconn')
        lines.append('    server %s %s check' % (sid, backend))

        return '\n'.join(lines)

    def format_frontend_comment(self, service, identity):
        return '    # %s %s #' % (identity, service)

    def format_frontend_entries(self, name, domain):
        lines = []
        lines.append(self.format_frontend_comment(name, 'begin'))

        lines.append('    acl %s hdr(host) -i %s' % (name, domain))
        lines.append('    use_backend %s if %s' % (name, name))

        lines.append(self.format_frontend_comment(name, 'end'))

        return '\n'.join(lines)

    def render_frontend_section_if_needed(self, name, domain):

        def _replace_frontend_backend(m):
            print m.group(0)
            a = m.group(2) + '\n' + self.format_frontend_entries(name, domain) + '\n\n'
            return m.group(1) + a + m.group(3)

        r = re.search(self.regexp_frontend_section_backend % (name, name), self.content, flags=re.DOTALL)

        if r is None:
            self.content = re.sub(self.regexp_frontend_section, _replace_frontend_backend, self.content, flags=re.DOTALL|re.MULTILINE)

    def get_content(self):
        return self.content

    def _normalize_name(self, name):
        return re.sub('[\.-]', '_', name)


event = json.load(sys.stdin)
# event = {
#     'name': 'service.start',
#     'data': {
#         'name': 'blink-server',
#         'id': '12345',
#         'attributes': {
#             'via_haproxy': True,
#             'from_host': 'notify.chalk.me,chalk.me',
#             'from_port': 80
#         },
#         'network': {
#             'ip': '129.0.0.1',
#             'port': '7777'
#         }
#     }
# }

name = event['name']
attributes = event['data']['attributes']


def resolve_backend():
    if 'network' not in event['data']:
        return None
    network = event['data']['network']

    if network['ip'] == '' or network['port'] is None:
        return None

    return network['ip'] + ':' + network['port']


def main():
    if attributes['via_haproxy']:
        backend = resolve_backend()
        if backend is None:
            return

        renderer = Renderer(get_content())
        hosts = re.split('\s*,\s*', attributes['from_host'])

        for host in hosts:
            if name == 'service.start':
                renderer.added_backend_server(host, event['data']['id'], backend)
            elif name == 'service.stop':
                renderer.remove_backend_server(event['data']['id'])

        save_content(renderer.get_content())

        subprocess.call(['/usr/sbin/service', 'haproxy', 'reload'])

main()
