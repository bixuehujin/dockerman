#! /usr/bin/env python

import os

from dockerman.application import Application


if __name__ == '__main__':
    app = Application({
        'store_file': './store.json',
        'docker_host': '127.0.0.1',
        'docker_port': '4243',
        'handler_path': os.getcwd() + '/handlers',
        'handlers': {
            'service.start': 'haproxy.py',
            'service.stop': 'haproxy.py'
        }
    })
    app.start(8888)

