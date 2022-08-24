#!/usr/bin/env python3
import sys
import time
from datetime import datetime
import json

import modules.aka_log as aka_log
import modules.generic as generic
import config.default_config as default_config


def audit(given_args=None, ln_edgerc=None):
    starttime = given_args.event_starttime - default_config.audit_log_delay - default_config.audit_loop_time
    endtime = given_args.event_endtime - default_config.audit_log_delay
    follow_mode = given_args.event_follow
    user_agent = given_args.ln_user_agent_prefix


    while True:
        aka_log.log.debug(f"Netlog starttime: {starttime}, Endtime: {endtime}, follow mode: {follow_mode}")


        ts_starttime = datetime.utcfromtimestamp(starttime).strftime('%Y-%m-%dT%H:%M:%S')
        ts_endtime = datetime.utcfromtimestamp(endtime).strftime('%Y-%m-%dT%H:%M:%S')


        my_headers = {
            'Authorization': 'Bearer ' + ln_edgerc['ln_token'],
            'X-FILTER': '{"+and": [{"created": {"+gte": "' + ts_starttime + '"}}, {"created": {"+lte": "' + ts_endtime + '"}}] }'
        }

        # Walk pages
        walk_pages = True
        my_page = 1
        while walk_pages:

            my_params = {
                'page': my_page,
                'page_size': default_config.audit_page_size
            }

            my_result = generic.api_request(method="GET", scheme="https://", url=ln_edgerc['ln_hostname'], path='/v4/account/events', params=my_params, headers=my_headers, payload=None, user_agent=user_agent)

            for line in my_result['data']:
                print(json.dumps(line))

            if my_result['page'] == my_result['pages']:
                walk_pages = False
            my_page = my_page + 1


        if follow_mode:
            starttime = endtime
            endtime = endtime + default_config.audit_loop_time
            time.sleep(default_config.audit_loop_time)
        else:
            break
