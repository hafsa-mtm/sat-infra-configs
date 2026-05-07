import json
import urllib.request
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from datetime import datetime, timezone, timedelta

ES_HOST = "http://localhost:9200"
ES_HEADERS = {
    "Content-Type": "application/json",
    "Authorization": "Basic ZWxhc3RpYzpzYXRfZWxhc3RpY18yMDI2"
}
ES_USER = "elastic"
ES_PASS = "sat_elastic_2026"
def fetch_metrics(size=1000):
    query = {
        "size": size,
        "sort": [{"@timestamp": {"order": "asc"}}],
        "query": {"match_all": {}},
        "_source": [
            "@timestamp",
            "system.cpu.total.pct",
            "system.memory.actual.used.pct",
            "system.network.in.bytes",
            "system.network.out.bytes",
            "system.diskio.read.bytes",
            "system.diskio.write.bytes",
            "system.process.summary.total"
        ]
    }
    data = json.dumps(query).encode('utf-8')
    req = urllib.request.Request(
        f"{ES_HOST}/.ds-metricbeat-*/_search",
        data=data,
        headers={"Content-Type": "application/json", "Authorization": "Basic ZWxhc3RpYzpzYXRfZWxhc3RpY18yMDI2"},
        method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            result = json.loads(r.read())
            hits = result['hits']['hits']
            print(f"  Fetched {len(hits)} metric records from Metricbeat")
            return hits
    except Exception as e:
        print(f"  Error fetching metrics: {e}")
        return []

def prepare_features(hits):
    records = []
    for hit in hits:
        source = hit['_source']
        record = {
            'timestamp': source.get('@timestamp', ''),
            'cpu': source.get('system', {}).get('cpu', {}).get('total', {}).get('pct', 0) or 0,
            'memory': source.get('system', {}).get('memory', {}).get('actual', {}).get('used', {}).get('pct', 0) or 0,
            'net_in': source.get('system', {}).get('network', {}).get('in', {}).get('bytes', 0) or 0,
            'net_out': source.get('system', {}).get('network', {}).get('out', {}).get('bytes', 0) or 0,
            'disk_read': source.get('system', {}).get('diskio', {}).get('read', {}).get('bytes', 0) or 0,
            'disk_write': source.get('system', {}).get('diskio', {}).get('write', {}).get('bytes', 0) or 0,
            'process_count': source.get('system', {}).get('process', {}).get('summary', {}).get('total', 0) or 0,
        }
        records.append(record)
    df = pd.DataFrame(records)
    print(f"  Prepared {len(df)} records with {len(df.columns)-1} base features")
    return df

def enrich_with_multisource(df):
    print("  Fetching log volume...")
    try:
        req = urllib.request.Request(
            f"{ES_HOST}/logs-*/_count",
            headers=ES_HEADERS,
            data=json.dumps({"query": {"match_all": {}}}).encode(),
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=5) as r:
            total_logs = json.loads(r.read()).get('count', 0)
        avg_log_rate = total_logs / max(len(df), 1)
        print(f"  Total logs: {total_logs}, avg per window: {avg_log_rate:.2f}")
    except Exception as e:
        print(f"  Could not fetch logs: {e}")
        avg_log_rate = 0

    print("  Fetching security alerts by minute...")
    alert_by_minute = {}
    failed_by_minute = {}
    try:
        query = {
            "size": 0,
            "aggs": {
                "alerts_over_time": {
                    "date_histogram": {
                        "field": "timestamp",
                        "calendar_interval": "minute"
                    },
                    "aggs": {
                        "failed_logins": {
                            "filter": {
                                "terms": {
                                    "rule.id.keyword": ["5710", "5503", "5401", "5502"]
                                }
                            }
                        }
                    }
                }
            }
        }
        data = json.dumps(query).encode('utf-8')
        req = urllib.request.Request(
            f"{ES_HOST}/wazuh-alerts/_search",
            data=data,
            headers=ES_HEADERS,
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=10) as r:
            result = json.loads(r.read())
            buckets = result['aggregations']['alerts_over_time']['buckets']
            for bucket in buckets:
                minute_key = bucket['key_as_string'][:16]
                alert_by_minute[minute_key] = bucket['doc_count']
                failed_by_minute[minute_key] = bucket['failed_logins']['doc_count']
        print(f"  Found {len(buckets)} alert time windows")
    except Exception as e:
        print(f"  Could not fetch security data: {e}")

    def get_minute_key(ts):
        return ts[:16] if ts else ''

    df['log_volume'] = avg_log_rate
    df['security_alerts'] = df['timestamp'].apply(
        lambda x: alert_by_minute.get(get_minute_key(x), 0)
    )
    df['failed_logins'] = df['timestamp'].apply(
        lambda x: failed_by_minute.get(get_minute_key(x), 0)
    )

    print(f"  Security alerts mapped: {df['security_alerts'].sum()}")
    print(f"  Failed logins mapped: {df['failed_logins'].sum()}")
    print(f"  Total features: {len(df.columns) - 1}")
    return df

def detect_anomalies(df):
    features = [
        'cpu', 'memory', 'net_in', 'net_out',
        'disk_read', 'disk_write', 'process_count',
        'log_volume', 'security_alerts', 'failed_logins'
    ]
    available = [f for f in features if f in df.columns]
    print(f"  Using {len(available)} features: {available}")

    df[available] = df[available].fillna(0)

    scaler = StandardScaler()
    X = scaler.fit_transform(df[available])

    model = IsolationForest(
        n_estimators=100,
        contamination=0.1,
        random_state=42
    )

    df['anomaly_score'] = model.fit_predict(X)
    df['anomaly_raw_score'] = model.score_samples(X)
    df['is_anomaly'] = df['anomaly_score'] == -1

    anomaly_count = df['is_anomaly'].sum()
    print(f"  Detected {anomaly_count} anomalies ({anomaly_count/len(df)*100:.1f}%)")
    return df, model, scaler, available

def calculate_metrics(df, features_used):
    total = len(df)
    anomalies = int(df['is_anomaly'].sum())
    normal = total - anomalies

    metrics = {
        'total_records': total,
        'anomalies_detected': anomalies,
        'normal_records': normal,
        'anomaly_rate': round(float(anomalies/total*100), 2),
        'features_used': len(features_used),
        'avg_cpu': round(float(df['cpu'].mean()), 6),
        'max_cpu': round(float(df['cpu'].max()), 6),
        'avg_memory': round(float(df['memory'].mean()), 6),
        'max_memory': round(float(df['memory'].max()), 6),
        'avg_security_alerts': round(float(df['security_alerts'].mean()), 4),
        'max_security_alerts': int(df['security_alerts'].max()),
        'avg_failed_logins': round(float(df['failed_logins'].mean()), 4),
        'total_failed_logins': int(df['failed_logins'].sum()),
        'min_anomaly_score': round(float(df['anomaly_raw_score'].min()), 4),
        'max_anomaly_score': round(float(df['anomaly_raw_score'].max()), 4),
        'avg_anomaly_score': round(float(df['anomaly_raw_score'].mean()), 4),
    }

    print("\n=== Evaluation Metrics ===")
    for k, v in metrics.items():
        print(f"  {k}: {v}")
    return metrics

def send_results_to_es(df, metrics, features_used):
    index = "anomaly-scores-v2"
    success = 0

    for _, row in df.iterrows():
        doc = {
            "@timestamp": row['timestamp'],
            "host": "edge",
            "model": "IsolationForest-MultiSource",
            "version": "2.0",
            "features_count": len(features_used),
            "cpu": float(row['cpu']),
            "memory": float(row['memory']),
            "net_in": float(row['net_in']),
            "net_out": float(row['net_out']),
            "disk_read": float(row.get('disk_read', 0)),
            "disk_write": float(row.get('disk_write', 0)),
            "process_count": float(row.get('process_count', 0)),
            "log_volume": float(row.get('log_volume', 0)),
            "security_alerts": int(row.get('security_alerts', 0)),
            "failed_logins": int(row.get('failed_logins', 0)),
            "anomaly_score": int(row['anomaly_score']),
            "anomaly_raw_score": float(row['anomaly_raw_score']),
            "is_anomaly": bool(row['is_anomaly']),
        }
        data = json.dumps(doc).encode('utf-8')
        req = urllib.request.Request(
            f"{ES_HOST}/{index}/_doc",
            data=data,
            headers=ES_HEADERS,
            method="POST"
        )
        try:
            with urllib.request.urlopen(req, timeout=5) as r:
                if r.status == 201:
                    success += 1
        except:
            pass

    summary = {
        "@timestamp": datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
        "type": "evaluation_summary",
        "model": "IsolationForest-MultiSource",
        **metrics
    }
    data = json.dumps(summary).encode('utf-8')
    req = urllib.request.Request(
        f"{ES_HOST}/{index}/_doc",
        data=data,
        headers=ES_HEADERS,
        method="POST"
    )
    urllib.request.urlopen(req, timeout=5)
    print(f"\n  Sent {success}/{len(df)} records to '{index}'")
    return success

def main():
    print("=" * 60)
    print("SAT Systems - Multi-Source AI Anomaly Detection Pipeline")
    print("Model: Isolation Forest v2.0")
    print("Sources: Metricbeat + Filebeat Logs + Wazuh Security")
    print("=" * 60)

    print("\n[1/5] Fetching infrastructure metrics...")
    hits = fetch_metrics(1000)
    if not hits:
        print("No data! Make sure Metricbeat is running.")
        return

    print("\n[2/5] Extracting base features...")
    df = prepare_features(hits)

    print("\n[3/5] Enriching with multi-source security and log data...")
    df = enrich_with_multisource(df)

    print("\n[4/5] Running Isolation Forest anomaly detection...")
    df, model, scaler, features_used = detect_anomalies(df)

    print("\n[5/5] Evaluating and storing results...")
    metrics = calculate_metrics(df, features_used)
    send_results_to_es(df, metrics, features_used)

    print("\n" + "=" * 60)
    print("✅ Multi-Source AI Pipeline Complete!")
    print(f"   Model: Isolation Forest")
    print(f"   Features: {len(features_used)} (infrastructure + security + logs)")
    print(f"   Anomalies: {metrics['anomalies_detected']}/{metrics['total_records']} ({metrics['anomaly_rate']}%)")
    print(f"   Results: {index if 'index' in dir() else 'anomaly-scores-v2'}")
    print("=" * 60)

if __name__ == "__main__":
    main()
