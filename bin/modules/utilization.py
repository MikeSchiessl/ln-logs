import datetime
import json
import requests
import threading
import time
import concurrent.futures

import modules.aka_log as aka_log
import ln_config.default_config as default_config

#follow_interval_sec = default_config.utilization_loop_time

class linode_count(object):

    LINODE_API = 'https://api.linode.com/v4'

    def __init__(self, api_headers):
        self.api_headers = api_headers

    def domains(self):
        resp_domains = requests.get(f'{linode_count.LINODE_API}/domains', headers=self.api_headers)
        return resp_domains.json().get('results')

    def instances(self):
        resp_instances = requests.get(f'{linode_count.LINODE_API}/linode/instances', headers=self.api_headers)
        return resp_instances.json().get('results')

    def lkes(self):
        resp_lkes = requests.get(f'{linode_count.LINODE_API}/lke/clusters', headers=self.api_headers)
        return resp_lkes.json().get('results')

    def vpcs(self):
        resp_vpcs = requests.get(f'{linode_count.LINODE_API}/vpcs', headers=self.api_headers)
        return resp_vpcs.json().get('results')

    def vlans(self):
        resp_vlans = requests.get(f'{linode_count.LINODE_API}/networking/vlans', headers=self.api_headers)
        return resp_vlans.json().get('results')

    def cloudfws(self):
        resp_cloudfws = requests.get(f'{linode_count.LINODE_API}/networking/firewalls', headers=self.api_headers)
        return resp_cloudfws.json().get('results')

    def nodebalancers(self):
        resp_nbs = requests.get(f'{linode_count.LINODE_API}/nodebalancers', headers=self.api_headers)
        return resp_nbs.json().get('results')
    
    def object_storage(self):
        resp_os = requests.get(f'{linode_count.LINODE_API}/object-storage/buckets', headers=self.api_headers)
        return resp_os.json().get('results')

    def images(self):
        stats = {
            "private_count": 0, # number of private images
            "private_size": 0, # sum of all the private original images
            "private_total_size": 0 # sum of all replicas for all images
        }
        pages = []
        pages.append(requests.get(f'{linode_count.LINODE_API}/images',
                                  headers=self.api_headers).json())
        stats['total'] = pages[0].get('results')
        total_pages = pages[0].get('pages', 1)
        if total_pages > 1:
            for page in range(2, total_pages):
                pages.append(requests.get(f'{linode_count.LINODE_API}/images', 
                                          params={'page': page}, 
                                          headers=self.api_headers).json())
        for p in pages:
            for i in p.get('data', []):
                if i.get('is_public') is False and i.get('expiry') is None:
                    stats['private_count'] += 1
                    stats['private_size'] += i.get('size')
                    stats['private_total_size'] += i.get('total_size')
        return stats

    def stackscripts(self):
        page_size = 500 # Reduce chances to get HTTP/429 too many requests
        resp_ss = requests.get(f'{linode_count.LINODE_API}/linode/stackscripts', params={'page_size': page_size}, headers=self.api_headers)
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
                resp_page_ss = requests.get(f'{linode_count.LINODE_API}/linode/stackscripts', params={'page_size': page_size, 'page': page_num}, headers=self.api_headers)
                if resp_page_ss.status_code == 200:
                    for script in resp_page_ss.json().get('data', []):
                        if script.get('mine') is True:
                            total += 1
                else:
                    aka_log.log.warning(f"HTTP/{resp_page_ss.status_code} {resp_page_ss.url}")
                    aka_log.log.warning(resp_page_ss.text)
        return total

    def volumes(self):
        resp_volumes = requests.get(f'{linode_count.LINODE_API}/volumes', headers=self.api_headers)
        return resp_volumes.json().get('results')


def stats_one(ln_edgerc, stackscripts: bool=False):

    api_token = ln_edgerc.get('linode_token')
    if not api_token:
        aka_log.log.fatal("API Token not found or empty in EdgeRC file.")
        exit(1)

    linode_api_headers = {
        'Authorization': 'Bearer ' + api_token,
    }

    account_info = requests.get('https://api.linode.com/v4/account', headers=linode_api_headers)
    if account_info.status_code != 200:
        aka_log.log.fatal(f"Can't fetch Linode account info with provided API token {api_token[:4]}...{api_token[-4:]}. "
                          f"Ensure API scope are set properly. API HTTP/{account_info.status_code}")
        exit(1)
    company = account_info.json().get('company')

    c = linode_count(linode_api_headers)


    info = {
        # for consistency, keep key as a singular word
        "time": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "account": company,
        "linode": c.instances(),
        "lke_cluster": c.lkes(),
        "vpc": c.vpcs(),
        "vlan": c.vlans(),
        "cloud_firewall": c.cloudfws(),
        "node_balancer": c.nodebalancers(),
        "object_storage": c.object_storage(),
        "volume": c.volumes(),
        "domain": c.domains()
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
