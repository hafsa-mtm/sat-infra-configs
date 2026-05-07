import json
import urllib.request
import os
ES_HOST = "http://localhost:9200"
ES_HEADERS = {
    "Content-Type": "application/json",
    "Authorization": "Basic ZWxhc3RpYzpzYXRfZWxhc3RpY18yMDI2"
}
INDEX = "wazuh-alerts"
ALERTS_FILE = "/tmp/wazuh-alerts.json"

def get_existing_ids():
    try:
        req = urllib.request.Request(
            f"{ES_HOST}/{INDEX}/_search?size=10000&_source=id",
            headers=ES_HEADERS,
            data=json.dumps({"query": {"match_all": {}}}).encode()
        )
        with urllib.request.urlopen(req, timeout=5) as r:
            data = json.loads(r.read())
            return {hit['_source']['id'] for hit in data['hits']['hits'] if 'id' in hit.get('_source', {})}
    except:
        return set()

def index_alerts():
    existing_ids = get_existing_ids()
    new_count = 0
    
    with open(ALERTS_FILE, 'r') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                doc = json.loads(line)
                alert_id = doc.get('id', '')
                if alert_id in existing_ids:
                    continue
                data = json.dumps(doc).encode('utf-8')
                req = urllib.request.Request(
                    f"{ES_HOST}/{INDEX}/_doc",
                    data=data,
                    headers=ES_HEADERS,
                    method="POST"
                )
                with urllib.request.urlopen(req, timeout=5) as r:
                    new_count += 1
            except Exception as e:
                print(f"Error: {e}")
    
    print(f"Indexed {new_count} new alerts")

if __name__ == "__main__":
    index_alerts()
