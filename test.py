import sys
import sys
import os

token=os.environ.get('LN_TOKEN')

import requests
import time
from datetime import datetime
#dt_utcnow = datetime.datetime.utcnow()
#print(dt_utcnow)

ts = int(time.time()) - 6000
timestamp = datetime.utcfromtimestamp(ts).strftime('%Y-%m-%dT%H:%M:%S')
print(timestamp)


#https://www.linode.com/docs/api/#filtering-and-sorting
my_filter = {'status': 'finished'}

time = time.time()


my_headers={
    'Authorization': 'Bearer ' + token,
    'X-FILTER': '{"+and": [{"created": {"+gte": "' + timestamp + '"}}, {"created": {"+lte": "' + timestamp + '"}}] }'
}


print(my_headers)
r = requests.get(url="https://api.linode.com/v4/account/events", headers=my_headers)
print(r.headers)
print("\n\n\n")
print(r.json())