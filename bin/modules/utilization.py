import datetime
import json
import threading
import time
import sys
from urllib3 import Retry
import concurrent.futures

# 3rd party
import requests
from requests.adapters import HTTPAdapter

# Our own modules
import modules.aka_log as aka_log
import ln_config.default_config as default_config

#follow_interval_sec = default_config.utilization_loop_time

class linode_api_client(object):

    LINODE_API = 'https://api.linode.com/v4'

    def __init__(self, api_headers):
        self.api_headers = api_headers
        # Since this CLI can be used with Unified Log Streamer, we are gonna try our best to handle
        # any glitches coming from the API, while not flooding the API infrastructure
        retries = Retry(total=16, status_forcelist=[500, 502, 503], allowed_methods=['GET'], backoff_factor=2)
        adapter = HTTPAdapter(max_retries=retries)
        self.session = requests.Session()
        self.session.mount(linode_api_client.LINODE_API, adapter)

    def get(self, url_path, params=None, **kwargs):
        return self.session.get(
            f'{linode_api_client.LINODE_API}{url_path}', 
            params=params,
            headers=self.api_headers)


class linode_count(object):

    def __init__(self, api_headers):
        self.api_client = linode_api_client(api_headers)

    def domains(self):
        resp_domains = requests.get(f'{linode_count.LINODE_API}/domains', headers=self.api_headers)
        return resp_domains.json().get('results')

    def instances(self):
        resp_instances = self.api_client.get('/linode/instances')
        return resp_instances.json().get('results')

    def instances_details(self):
        page_size = 500
        doc = {
            "by_region": {},
            "by_type": {}
        }

        resp_instances = self.api_client.get('/linode/instances', params={'page_size': page_size})
        for instance in resp_instances.json().get('data'):
            if instance.get('region') not in doc["by_region"]:
                doc["by_region"][instance.get('region')] = 0
            doc["by_region"][instance.get('region')] += 1
            if instance.get('type') not in doc["by_type"]:
                doc["by_type"][instance.get('type')] = 0
            doc["by_type"][instance.get('type')] += 1

        # We receive all instances, including the one shared from other Linode customers
        for extra_page in range(resp_instances.json().get('pages')-1):
            page_num = extra_page + 1
            resp_instance_ss = self.api_client.get('/linode/instances', params={'page_size': page_size, 'page': page_num})
            if resp_instance_ss.status_code == 200:
                for instance in resp_instance_ss.json().get('data'):
                    if instance.get('region') not in doc["by_region"]:
                        doc["by_region"][instance.get('region')] = 0
                    doc["by_region"][instance.get('region')] += 1
                    if instance.get('type') not in doc["by_type"]:
                        doc["by_type"][instance.get('type')] = 0
                    doc["by_type"][instance.get('type')] += 1

            else:
                aka_log.log.warning(f"HTTP/{resp_instance_ss.status_code} {resp_instance_ss.url}")
                aka_log.log.warning(resp_instance_ss.text)

        # print(json.dumps(resp_instances.json(), indent=2))
        return doc

    def lkes(self):
        resp_lkes = self.api_client.get('/lke/clusters')
        return resp_lkes.json().get('results')

    def vpcs(self):
        resp_vpcs = self.api_client.get('/vpcs')
        return resp_vpcs.json().get('results')

    def vlans(self):
        resp_vlans = self.api_client.get('/networking/vlans')
        return resp_vlans.json().get('results')

    def cloudfws(self):
        resp_cloudfws = self.api_client.get('/networking/firewalls')
        return resp_cloudfws.json().get('results')

    def nodebalancers(self):
        resp_nbs = self.api_client.get('/nodebalancers')
        return resp_nbs.json().get('results')
    
    def object_storage(self):
        resp_os = self.api_client.get('/object-storage/buckets')
        return resp_os.json().get('results')

    def images(self):
        stats = {
            "private_count": 0, # number of private images
            "private_size": 0, # sum of all the private original images
            "private_total_size": 0 # sum of all replicas for all images
        }
        pages = []
        pages.append(self.api_client.get('/images').json())
        stats['total'] = pages[0].get('results')
        total_pages = pages[0].get('pages', 1)
        if total_pages > 1:
            for page in range(2, total_pages):
                pages.append(self.api_client.get('/images', params={'page': page}))
        for p in pages:
            for i in p.get('data', []):
                if i.get('is_public') is False and i.get('expiry') is None:
                    stats['private_count'] += 1
                    stats['private_size'] += i.get('size')
                    stats['private_total_size'] += i.get('total_size')
        return stats

    def stackscripts(self):
        page_size = 500 # Reduce chances to get HTTP/429 too many requests
        resp_ss = self.api_client.get('/linode/stackscripts', params={'page_size': page_size})
        if resp_ss.status_code != 200:
            aka_log.log.warning(f"HTTP/{resp_ss.status_code} {resp_ss.url}")
            aka_log.log.warning(resp_ss.text)
            return None
        total = 0
        for script in resp_ss.json().get('data'):
            if script.get('mine') is True:
                total += 1

        if resp_ss.json().get('pages') == 1:
            return total
        else:
            # We receive all Stackscript, including the one shared from other Linode customers
            for extra_page in range(resp_ss.json().get('pages')-1):
                page_num = extra_page + 1
                resp_page_ss = self.api_client.get('/linode/stackscripts', params={'page_size': page_size, 'page': page_num})
                if resp_page_ss.status_code == 200:
                    for script in resp_page_ss.json().get('data', []):
                        if script.get('mine') is True:
                            total += 1
                else:
                    aka_log.log.warning(f"HTTP/{resp_page_ss.status_code} {resp_page_ss.url}")
                    aka_log.log.warning(resp_page_ss.text)
        return total

    def volumes(self):
        resp_volumes = self.api_client.get('/volumes')
        return resp_volumes.json().get('results')


def stats_one(ln_edgerc, stackscripts: bool = False):
    api_token = ln_edgerc.get('linode_token')
    if not api_token:
        aka_log.log.fatal("API Token not found or empty in EdgeRC file.")
        exit(1)

    linode_api_headers = {
        'Authorization': 'Bearer ' + api_token,
    }
    api_client = linode_api_client(linode_api_headers)

    account_info = api_client.get('/account')
    if account_info.status_code != 200:
        sys.stderr.write(f"Can't fetch Linode account info, likely invalid/expired\nLINODE_API_TOKEN=<snip>{ln_edgerc['linode_token'][:4]}\n")
        exit(2)
    company = account_info.json().get('company')

    c = linode_count(linode_api_headers)
    # output dict
    info = {
        "time": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "account": company,
    }

    # mapping between key - which will be added into info dict above
    # and the function to call asynchronously to fill the data.
    map_key_function = {
        # for consistency, keep key as a singular word
        "linode": c.instances,
        "linode_details": c.instances_details,
        "lke_cluster": c.lkes,
        "vpc": c.vpcs,
        "vlan": c.vlans,
        "cloud_firewall": c.cloudfws,
        "node_balancer": c.nodebalancers,
        "object_storage": c.object_storage,
        "volume": c.volumes,
        "image": c.images
    }
    if stackscripts:
        map_key_function["stackscript"] = c.stackscripts

    def fetch_for_output_dict(key, func):
        return key, func()

    with concurrent.futures.ThreadPoolExecutor() as executor:
        future_to_key = {}
        for key, func in map_key_function.items():
            future = executor.submit(fetch_for_output_dict, key, func)
            future_to_key[future] = key
        for future in concurrent.futures.as_completed(future_to_key):
            key, result = future.result()
            info[key] = result

    print(json.dumps(info), flush=True) # Flush to allow process pipelining like ULS


def stats(ln_edgerc, stackscript: bool=False, follow=False, stop_event: threading.Event=None, follow_interval_sec=default_config.utilization_loop_time):
    if follow and stop_event:
        while not stop_event.is_set():
            tick = time.time()
            stats_one(ln_edgerc, stackscript)
            stop_event.wait(follow_interval_sec - (time.time() - tick))
    else:
        stats_one(ln_edgerc, stackscript)
