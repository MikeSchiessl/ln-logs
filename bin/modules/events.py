#!/usr/bin/env python3
import sys
import time
from datetime import datetime
import json

import modules.aka_log as aka_log
import modules.generic as generic
import config.default_config as default_config


def get_log(given_args=None, ln_edgerc=None, config_lopp_time=None, config_log_delay=None, config_page_size=500, route='/', params={}):
    starttime = given_args.event_starttime - config_log_delay - config_lopp_time
    endtime = given_args.event_endtime - config_log_delay
    follow_mode = given_args.event_follow
    user_agent = given_args.ln_user_agent_prefix


    while True:
        aka_log.log.debug(f"Request starttime: {starttime}, Endtime: {endtime}, follow mode: {follow_mode}")


        ts_starttime = datetime.utcfromtimestamp(starttime).strftime('%Y-%m-%dT%H:%M:%S')
        ts_endtime = datetime.utcfromtimestamp(endtime).strftime('%Y-%m-%dT%H:%M:%S')


        my_headers = {
            'Authorization': 'Bearer ' + ln_edgerc['linode_token'],
            'X-FILTER': '{"+and": [{"created": {"+gte": "' + ts_starttime + '"}}, {"created": {"+lte": "' + ts_endtime + '"}}] }'
        }

        # Walk pages
        walk_pages = True
        my_page = 1
        while walk_pages:

            my_params = params
            my_params['page'] = my_page
            my_params['page_size'] = config_page_size

            my_result = generic.api_request(method="GET", scheme="https://", url=ln_edgerc['linode_hostname'], path=route, params=my_params, headers=my_headers, payload=None, user_agent=user_agent)

            for line in my_result['data']:
                print(json.dumps(line))

            if my_result['page'] == my_result['pages']:
                walk_pages = False
            my_page = my_page + 1


        if follow_mode:
            starttime = endtime
            endtime = endtime + config_lopp_time
            time.sleep(config_lopp_time)
        else:
            break

def audit(given_args=None, ln_edgerc=None):
    get_log(given_args=given_args,
            ln_edgerc=ln_edgerc,
            config_lopp_time=default_config.audit_loop_time,
            config_log_delay=default_config.audit_log_delay,
            config_page_size=default_config.audit_page_size,
            route="/v4/account/events")

# EOF