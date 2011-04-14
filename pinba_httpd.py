#!/usr/bin/env python

from flask import Flask, request
from socket import socket, gethostname, AF_INET, SOCK_DGRAM
from sys import argv
import pinba_pb2

DEBUG = True
PINBA_HOST = '127.0.0.1'
PINBA_PORT = 30002

app = Flask(__name__)
app.config.from_object(__name__)
app.config.from_envvar('PINBA_HTTPD_SETTINGS', silent=True)

udpsock = socket(AF_INET, SOCK_DGRAM)
hostname = gethostname()

@app.route('/track/<tracker>')
@app.route('/track/<tracker>;<float:timer>')
def track(tracker, timer=0.0):
    # Create a default "empty" Pinba request message
    msg = pinba_pb2.Request()
    msg.hostname = hostname
    msg.server_name = request.environ['HTTP_HOST']
    msg.script_name = tracker
    msg.request_count = 1
    msg.document_size = 0
    msg.memory_peak = 0
    msg.request_time = timer
    msg.ru_utime = 0.0
    msg.ru_stime = 0.0
    msg.status = 200

    if request.args:
        # Add a single timer
        msg.timer_hit_count.append(1)
        msg.timer_value.append(timer)
        msg.timer_tag_count.append(len(request.args))

        # Encode associated tags
        dictionary = [] # contains mapping of tags name or value => uniq id
        for name, value in request.args.items():
            value = str(value)
            if name not in dictionary:
                dictionary.append(name)
            if value not in dictionary:
                dictionary.append(value)
            msg.timer_tag_name.append(dictionary.index(name))
            msg.timer_tag_value.append(dictionary.index(value))

        # Global tags dictionary
        msg.dictionary.extend(dictionary);

    # Send message to Pinba server
    udpsock.sendto(msg.SerializeToString(), (app.config['PINBA_HOST'], app.config['PINBA_PORT']))

    return ''

@app.after_request
def after_request(response):
    response.headers['Server'] = 'Pinba-HTTPD/1.0';
    return response

if __name__ == '__main__':
    app.run()