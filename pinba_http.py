#!/usr/bin/env python

from cgi import parse_qs
from socket import socket, gethostname, AF_INET, SOCK_DGRAM
from sys import argv
import re
import pinba_pb2

VERSION = 1.1
PINBA_HOST = '127.0.0.1'
PINBA_PORT = 30002
TIMER_MAX = 10*60

udpsock = socket(AF_INET, SOCK_DGRAM)
hostname = gethostname()

class InvalidTimer(Exception):
    pass

def pinba(server_name, tracker, timer, tags):
    """
    Send a message to Pinba.

    :param server_name: HTTP server name
    :param tracker:     tracker name
    :param timer:       timer value in seconds
    :param tags:        dictionary of tags
    """
    if timer < 0 or timer > TIMER_MAX:
        raise InvalidTimer()

    msg = pinba_pb2.Request()
    msg.hostname = hostname
    msg.server_name = server_name
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

def generic(prefix, environ):
    """
    Generic Pinba handler.

    The timer is in `t` and other parameters are considered to be
    additional tags. The tracker name is the end of the path.
    """
    tracker = environ["PATH_INFO"][len(prefix):]
    tags = parse_qs(environ['QUERY_STRING'])
    try:
        timer = float(tags.pop('t')[0])
    except KeyError:
        timer = 0.0
    pinba(environ['HTTP_HOST'], tracker, timer, tags)

class Boomerang(object):
    """
    Handler for Yahoo Boomerang.

    https://github.com/yahoo/boomerang

    Parameters matching `.?t_` are considered as timestamps, except
    `t_resp`, `t_page` and `t_done`. Timestamps are transformed into
    timers by making the difference with `nt_nav_st`.
    """

    def __init__(self):
        self.timestamps_re = re.compile("^.?t_")

    def is_timer(self, name):
        """Is it a timer in milliseconds?"""
        return name in ["t_resp", "t_page", "t_done"]

    def is_timestamp(self, name):
        """Is it a timestamp in milliseconds?"""
        if self.timestamps_re.match(name) and not self.is_timer(name):
            return True
        return False

    def __call__(self, prefix, environ):
        tags = parse_qs(environ['QUERY_STRING'])
        try:
            # Start point for other timestamps
            start = int(tags.pop("nt_nav_st")[0])
        except KeyError:
            raise InvalidTimer
        timers = {}
        for t in tags.keys()[:]:
            if self.is_timer(t):
                timers[t] = int(tags.pop(t)[0])
            elif self.is_timestamp(t):
                val = int(tags.pop(t)[0]) - start
                if val < 0:
                    continue
                timers[t] = val
        for t in timers:
            pinba(environ['HTTP_HOST'], "boomerang.%s" % t, timers[t]/1000., tags)

# Simple routing
handlers = {
    "/track/": generic,
    "/track-boomerang/": Boomerang()
}

def app(environ, start_response):
    for h in handlers:
        if environ['PATH_INFO'].startswith(h):
            try:
                handlers[h](h, environ)
            except InvalidTimer:
                start_response('400 Invalid Timer', [('Content-Length', 0)])
                return ['']
            start_response('200 OK', [('Content-Length', 0)])
            return ['']
    start_response('404 Not Found', [('Content-Length', 0)])
    return ['']
