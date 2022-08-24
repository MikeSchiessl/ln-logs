# ln-logs

## Usage

### Audit logs
Setup the .edgerc file as described [here](#authentication)
```bash

akamai-linode events audit --follow
```

Please make sure you enter the hostname **without** any scheme (http:// or https://)
```bash
[default]
; Guardicore integration credentials
linode_hostname = your_hostname.guardicore.com          # Do not prepend https://
linode_token = XXXXXXXXXXXX
```