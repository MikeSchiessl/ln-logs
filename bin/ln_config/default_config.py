#!/usr/bin/env python3

# Generic Settings
## CLI default loglevel
default_log_level = 'ERROR'
## CLI available loglevels
log_levels_available = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
## How often do we want to retry an auth before failing
max_auth_attempts = 3


## Audit
### events per page
audit_page_size = 100
### Delay from $now to ensure 100% of logs are received on the backend (time in seconds)
audit_log_delay = 600
### Loop time in seconds
audit_loop_time = 60
