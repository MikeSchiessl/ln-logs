#!/usr/bin/env python3
import sys
import time
from datetime import datetime, timezone
import threading

import modules.aka_log as aka_log
import modules.generic as generic
import ln_config.default_config as default_config
import pytz
import json
from pyasn1.type.useful import UTCTime


def get_log(given_args=None, ln_edgerc=None, config_lopp_time=None, config_log_delay=None, config_page_size=500, route='/', params={}, stop_event: threading.Event=None):
    starttime = given_args.event_starttime - config_log_delay - config_lopp_time
    endtime = given_args.event_endtime - config_log_delay
    follow_mode = given_args.event_follow
    user_agent = given_args.ln_user_agent_prefix

    while not stop_event.is_set():
        aka_log.log.debug(f"Request starttime: {starttime}, Endtime: {endtime}, follow mode: {follow_mode}")
        tick = time.time()

        #ts_starttime = datetime.utcfromtimestamp(starttime).strftime('%Y-%m-%dT%H:%M:%S')
        ts_starttime = datetime.fromtimestamp(starttime, tz=pytz.utc).strftime('%Y-%m-%dT%H:%M:%S')
        aka_log.log.debug(f"ts_starttime: {ts_starttime}")
        #print(f"ts_starttime: {ts_starttime}")
        #ts_starttime = datetime.datetime.formtimestamp(starttime, datetime.UTC)

        #ts_endtime = datetime.utcfromtimestamp(endtime).strftime('%Y-%m-%dT%H:%M:%S')
        ts_endtime = datetime.fromtimestamp(endtime, tz=pytz.utc).strftime('%Y-%m-%dT%H:%M:%S')
        aka_log.log.debug(f"ts_endtime: {ts_endtime}")


        my_headers = {
            'Authorization': 'Bearer ' + ln_edgerc['linode_token'],
        }

        if not given_args.event_verbs:
            aka_log.log.debug(f"no additional verbs given, not filtering at all !")
            my_headers.update({'X-FILTER': '{"+and": [{"created": {"+gte": "' + ts_starttime + '"}}, {"created": {"+lte": "' + ts_endtime + '"}}] }'})

        elif given_args.event_verbs:
            aka_log.log.debug(f"Filtering verbs given, creating a filter list")
            verb_filter_list = []
            for verb in list(given_args.event_verbs.split(',')):
                verb_filter_list.append('{"action": "' + verb + '"}')
            my_headers.update({"X-FILTER": '{"+and": [{"created": {"+gte": "' + ts_starttime + '"}}, {"created": {"+lte": "' + ts_endtime + '"}}, {"+or": [' + ', '.join(verb_filter_list) + ' ]}] }'})

        # Walk pages
        walk_pages = True
        my_page = 1
        while walk_pages:
            my_params = params
            my_params['page'] = my_page
            my_params['page_size'] = config_page_size

            my_result = generic.api_request(method="GET", scheme="https://", url=ln_edgerc['linode_hostname'], path=route, params=my_params, headers=my_headers, payload=None, user_agent=user_agent)
            #print(f"my_result: {my_result}")
            #for line in my_result['data']:
            for line in my_result.get('data'):
                print(json.dumps(line))

            if my_result['page'] == my_result['pages']:
                walk_pages = False
            my_page = my_page + 1


        if follow_mode:
            starttime = endtime
            endtime = endtime + config_lopp_time
            stop_event.wait(config_lopp_time - (time.time() - tick))
            #time.sleep(config_lopp_time)
        else:
            break

def audit(given_args=None, ln_edgerc=None, stop_event: threading.Event=None):
        get_log(given_args=given_args,
                ln_edgerc=ln_edgerc,
                config_lopp_time=default_config.audit_loop_time,
                config_log_delay=default_config.audit_log_delay,
                config_page_size=default_config.audit_page_size,
                stop_event=stop_event,
                route="/v4/account/events")

# EOF