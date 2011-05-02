#!/usr/bin/env python

from cgi import parse_qs
from socket import socket, gethostname, AF_INET, SOCK_DGRAM
from sys import argv
import pinba_pb2

VERSION = 1.0
PINBA_HOST = '127.0.0.1'
PINBA_PORT = 30002
PATH_PREFIX = '/track/'
TIMER_MAX = 10*60

udpsock = socket(AF_INET, SOCK_DGRAM)
hostname = gethostname()
prefix_size = len(PATH_PREFIX)

def app(environ, start_response):
    if not environ['PATH_INFO'].startswith(PATH_PREFIX):
        start_response('404 Not Found', [('Content-Length', 0)])
        return ['']

    tracker = environ['PATH_INFO'][prefix_size:]
    tags = parse_qs(environ['QUERY_STRING'])
    try:
        timer = float(tags.pop('t')[0])
        if timer < 0 or timer > TIMER_MAX: raise ValueError()
    except KeyError:
        timer = 0.0
    except ValueError:
        start_response('400 Invalid Timer', [('Content-Length', 0)])
        return ['']

    # Create a default "empty" Pinba request message
    msg = pinba_pb2.Request()
    msg.hostname = hostname
    msg.server_name = environ['HTTP_HOST']
    msg.script_name = tracker
    msg.request_count = 1
    msg.document_size = 0
    msg.memory_peak = 0
    msg.request_time = timer
    msg.ru_utime = 0.0
    msg.ru_stime = 0.0
    msg.status = 200

    if tags:
        # Add a single timer
        msg.timer_hit_count.append(1)
        msg.timer_value.append(timer)

        # Encode associated tags
        tag_count = 0
        dictionary = [] # contains mapping of tags name or value => uniq id
        for name, values in tags.items():
            if name not in dictionary:
                dictionary.append(name)
            for value in values:
                value = str(value)
                if value not in dictionary:
                    dictionary.append(value)
                msg.timer_tag_name.append(dictionary.index(name))
                msg.timer_tag_value.append(dictionary.index(value))
                tag_count += 1

        # Number of tags
        msg.timer_tag_count.append(tag_count)

        # Global tags dictionary
        msg.dictionary.extend(dictionary);

    # Send message to Pinba server
    udpsock.sendto(msg.SerializeToString(), (PINBA_HOST, PINBA_PORT))

    start_response('200 OK', [('Content-Length', 0)])
    return ['']