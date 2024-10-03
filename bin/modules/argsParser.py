#!/usr/bin/env python3

import argparse
import os
import time
import ln_config.version as version
import ln_config.default_config as default_config

def init():
    # Argument Parsing
    parser = argparse.ArgumentParser(description=f"{version.__tool_name_long__}",
                                     formatter_class=argparse.RawTextHelpFormatter)

    # Version Information
    parser.add_argument('-v','--version',
                        action='store',
                        type=bool,
                        default=False,
                        nargs='?',
                        const=True,
                        help=f'Display {version.__tool_name_short__} version and operational information')

    # Loglevel
    parser.add_argument('-l', '--loglevel',
                        action='store',
                        type=str.upper,
                        default=(os.environ.get('LN_LOGLEVEL') or default_config.default_log_level),
                        choices=default_config.log_levels_available,
                        help=f'Adjust the loglevel Default: {default_config.default_log_level}')

    # EDGERC
    parser.add_argument('--edgerc',
                             action='store',
                             type=str,
                             dest="credentials_file",
                             default=(os.environ.get('LN_EDGERC') or '~/.edgerc'),
                             help="Location of the credentials file (default is ~/.edgerc)")

    # EDGERC-SECTION
    parser.add_argument('--section',
                             action='store',
                             type=str,
                             dest="credentials_file_section",
                             default=(os.environ.get('LN_SECTION') or 'default'),
                             help="Credentials file Section's name to use ('default' if not specified).")

    # USER AGENT
    parser.add_argument('--user-agent-prefix',
                        action='store',
                        type=str,
                        dest='ln_user_agent_prefix',
                        default=f"LN-CLI {version.__version__}",
                        help="Change the User Agent when making requests"
                        )

    # Commands
    subparsers = parser.add_subparsers(dest='command', help='sub-command help')

    ## EVENTS
    parser_events = subparsers.add_parser(name="events", aliases="e", help=(f"Show {version.__tool_name_long__} events"))

    ### NETLOG
    parser_events.add_argument(dest="event_action",
                                choices=['audit'],
                               action='store',
                               help="Show Events")


    parser_events.add_argument('--start',
                               action='store',
                               dest='event_starttime',
                               type=int,
                               default=int(time.time()),
                               help="Fetch events from $starttime (UNIX TIMESTAMP)")

    parser_events.add_argument('--end',
                               action='store',
                               dest='event_endtime',
                               type=int,
                               default=int(time.time()),
                               help=''"Stop event collection at $endtime (UNIX TIMESTAMP)")

    parser_events.add_argument('-f', '--follow',
                               action='store',
                               dest='event_follow',
                               type=bool,
                               nargs='?',
                               default=False,
                               const=True,
                               help="Continuously follow (tail -f) the log")

    ## UTILIZATION
    parser_usage = subparsers.add_parser(name="utilization", aliases="u", help=(f"Show {version.__tool_name_long__} account utilization"))
    parser_usage.add_argument('--include-stackscripts', action='store_true', dest="stackscripts", default=False, 
                              help="Count also private stackscript (slow)")
    parser_usage.add_argument('-f', '--follow',
                               action='store',
                               dest='follow',
                               type=bool,
                               nargs='?',
                               default=False,
                               const=True,
                               help="Continuously print update every 5 minutes")
    #print(parser.parse_args())
    return parser.parse_args()



# EOF