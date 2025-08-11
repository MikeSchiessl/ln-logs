# Akamai Linode (LOGGING) CLI

## Getting started

We recommend to use a separate (api) user, dedicated to this CLI.

Under the Linode user of your choice, create a READ-ONLY Linode API Token in Cloud Manager, with access to all scopes.  
For more info check out [Manage personal access tokens](https://techdocs.akamai.com/cloud-computing/docs/manage-personal-access-tokens).

Create an INI configuration file (by default we use `~/.edgerc`)

```INI
[default]
; Linode integration credentials
linode_hostname = api.linode.com  # Do not prepend https://
linode_token = XXXXXXXXXXXX       # Read-only permission suffices
```

Please make sure you enter the hostname **without** any scheme (`http://` or `https://`)

## Usage

### Audit logs

Setup the `.edgerc` file as described [here](#authentication)
```bash
akamai-linode events audit --follow
```

### Objects utilization

```
akamai-linode utilization --include-stackscripts --follow
```

In follow mode, it will print the different counters by object type from your account.  
Example:
```json
{
    "time": "2025-08-11T23:15:44.531463+00:00", 
    "account": "My company name", 
    "linode": 3605, 
    "linode_details": {
        "by_region": {
        "in-maa": 394,
        "se-sto": 913,
        "de-fra-2": 694,
        "us-iad": 226,
        "jp-osa": 263,
        "br-gru": 741,
        "sg-sin-2": 561,
        "us-lax": 208
        },
        "by_type": {
        "g6-standard-4": 468,
        "g6-standard-8": 266,
        "g6-standard-2": 546,
        "g6-nanode-1": 2474,
        "g6-standard-1": 246
        }
    },
    "image": {
        "private_count": 9,
        "private_size": 52438,
        "private_total_size": 179251,
        "total": 90
    },
    "lke_cluster": 0, 
    "vpc": 1, 
    "vlan": 0, 
    "cloud_firewall": 2, 
    "node_balancer": 0, 
    "object_storage": 0, 
    "volume": 2,
    "stackscript": 12
}
```

Note the last counter, `stackscript` will be reported only when using `--include-stackscripts` argument is added to the command line.

To send these events into your SIEM, please checkout [Akamai Unified Log Streamer](https://github.com/akamai/uls)
