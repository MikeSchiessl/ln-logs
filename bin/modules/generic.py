#!/usr/bin/env python3

import requests
import os
import sys
import configparser
import config.version as gc_version
import config.default_config as default_config
import modules.aka_log as aka_log


def version():
    """
    Print this tools version #
    :return:
    """
    print(gc_version.__version__)
    sys.exit(0)


def edgerc_reader(configfile, configsection, configvalues):
    """
    Load the given EDGERC File
    :param filename: file to edgerc
    :return: dict {'gc_username': gc_username, 'gc_password': gc_password, 'gc_hostname': gc_hostname}
    """
    my_return = {'gc_username': '', 'gc_password': '', 'gc_hostname': ''}

    config = configparser.ConfigParser()
    if not config.read(os.path.expanduser(configfile)):
        aka_log.log.critical(f"Config file '{os.path.expanduser(configfile)}' could not be loaded. - Exiting.")
        sys.exit(1)
    else:
        aka_log.log.debug(f"Config file '{os.path.expanduser(configfile)}' was found and is readable.")

    # Check config section
    if configsection not in config:
        aka_log.log.critical(f"Section '{configsection}' not found. Available sections: '{config.sections()}'. - Exiting")
        sys.exit(1)
    else:
        aka_log.log.debug(f"Section '{configsection}' found.")

    # check for specified values
    for configvalue in configvalues:
        if not configvalue in config[configsection]:
            aka_log.log.critical(f"Required configuration value '{configvalue}' not found in section  - Exiting")
            sys.exit(1)
        else:
            my_return[configvalue] = config.get(section=configsection, option=configvalue)
            aka_log.log.debug(f"Required configuration value '{configvalue}' found.")
    return my_return




def api_request(method="GET", scheme="https://", url=None, path=None, params={}, payload={}, headers={}, content_type='application/json', expected_status_list=[200], user_agent=None):
    """
    Generic API Request handler including debugging handlers
    :param self:
    :param method:
    :param scheme:
    :param url:
    :param path:
    :param params:
    :param payload:
    :param headers:
    :param content_type:
    :param expected_status_list:
    :return:
    """
    try:
        my_url = scheme + url + path
        headers['Content-Type'] = content_type
        headers['User-Agent'] = user_agent
        aka_log.log.debug( f"Sending Request (URL: {my_url}, Method: {method}, Params: {params}, Payload: {payload}, Headers: {headers}, expected status: {expected_status_list} ")
        my_request = requests.request(method=method.upper(), url=my_url, params=params, headers=headers,
                                      json=payload)
        # my_request = urequests.request(method=method, url=my_url, headers=my_headers, json=payload)
        if my_request.status_code in expected_status_list and my_request.text:
            aka_log.log.debug(f"Request successful (status, text):  {my_request.status_code} {my_request.text}")
            return my_request.json()
        else:
            aka_log.log.critical(f"Request error (status, text):  {my_request.status_code} {my_request.text}")
            # return False
    except Exception as error:
        aka_log.log.critical(f"Critical request error: {error}")


def gc_get_auth_token(gc_edgerc=None):
    """
    Returns the Guardicore auth token for later use
    :param gc_edgerc:
    :return: {'access_token': 'token'}
    """
    my_payload = {'username': gc_edgerc['gc_username'], 'password': gc_edgerc['gc_password']}

    my_return = api_request(method="POST", url=gc_edgerc['gc_hostname'], path='/api/v3.0/authenticate', payload=my_payload)
    if not my_return or not 'access_token' in my_return:
        aka_log.log.critical(f"Not able to retreive an authentication token, exiting")
        sys.exit(1)
    else:
        return my_return