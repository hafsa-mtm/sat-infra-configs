import time
import json
import urllib.request
from datetime import datetime

ES_HOST = "http://192.168.87.132:9200"
INDEX = "metricbeat-edge"

def get_cpu():
    with open('/proc/stat') as f:
        line = f.readline()
    fields = [float(x) for x in line.split()[1:]]
    idle = fields[3]
    total = sum(fields)
    time.sleep(0.1)
    with open('/proc/stat') as f:
        line = f.readline()
    fields2 = [float(x) for x in line.split()[1:]]
    idle2 = fields2[3]
    total2 = sum(fields2)
    return round((1 - (idle2-idle)/(total2-total)) * 100, 2)

def get_memory():
    mem = {}
    with open('/proc/meminfo') as f:
        for line in f:
            key, val = line.split(':')
            mem[key.strip()] = int(val.split()[0])
    total = mem['MemTotal']
    free = mem['MemFree'] + mem['Buffers'] + mem.get('Cached', 0)
    used_pct = round((1 - free/total) * 100, 2)
    return used_pct, total * 1024, (total - free) * 1024

def send_to_es(doc):
    data = json.dumps(doc).encode('utf-8')
    req = urllib.request.Request(
        f"{ES_HOST}/{INDEX}/_doc",
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    with urllib.request.urlopen(req, timeout=5) as r:
        return r.status

def collect_and_send():
    print("Starting Edge Metrics Collector...")
    while True:
        try:
            cpu = get_cpu()
            mem_pct, mem_total, mem_used = get_memory()
            doc = {
                "@timestamp": datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ'),
                "host": {"name": "edge"},
                "system": {
                    "cpu": {"usage": cpu},
                    "memory": {
                        "usage_pct": mem_pct,
                        "total": mem_total,
                        "used": mem_used
                    }
                },
                "service": "metricbeat-edge"
            }
            status = send_to_es(doc)
            print(f"[{doc['@timestamp']}] CPU={cpu}% MEM={mem_pct}% → ES status={status}")
        except Exception as e:
            print(f"Error: {e}")
        time.sleep(30)

if __name__ == "__main__":
    collect_and_send()
