Pinba HTTP Gateway
==================

Pinba-HTTP is a HTTP interface for [Pinba](http://pinba.org/). It allows to forge Pinba timers from simple HTTP queries with optional tags. This is useful to time things on the client (javascript, flash) in the same backend as for you backend code.

This is a bit of a hack as Pinba isn't really meant to do that, but who cares? :)

Usage
-----

To account the frequency of an event, request the following URL from your client code:

    http://hostname/track/mycounter

This will create a Pinba request, with `script_name` set to `mycounter`. You can then graph the number of request per second for this counter using a query like this:

    SELECT req_per_sec FROM report_by_server_name WHERE script_name = 'mycounter';

You can add a time value to your counter by adding the time in seconds (float) to the request:

    http://hostname/track/mytimer?t=0.231

The time value will be set as the `request_time` value. You can then get the average time for this timer using a query like this:

    SELECT req_time_total/req_count FROM report_by_server_name WHERE script_name = 'mytimer';

Finaly, you can add tags to your timer by adding a query string to your request. If at least one tag is present, a single sub-timer will be created with the provided tags:

    http://hostname/track/mytimer?t=0.231&tag1=value1&tag2=value2

You can then create corresponding report table for the tags you want to query.

Installation
------------

This project requires the [Protocol Buffer Python library](http://code.google.com/apis/protocolbuffers/docs/pythontutorial.html).
