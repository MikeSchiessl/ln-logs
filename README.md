# ln-logs

## Usage

### Audit logs
Setup the .edgerc file as described [here](#authentication)
```bash

akamai-ln events audit --follow
```

Please make sure you enter the hostname **without** any scheme (http:// or https://)
```bash
[default]
ln_hostname = api.linode.com       # Do not prepend http(s)://m
ln_token = your_linode_token
```