import json
import urllib.request
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from datetime import datetime, timezone

ES_HOST = "http://localhost:9200"

def fetch_metrics():
    """Fetch metrics from Elasticsearch"""
    query = {
        "size": 1000,
        "sort": [{"@timestamp": {"order": "desc"}}],
        "query": {"match_all": {}},
        "_source": ["@timestamp", "system.cpu.total.pct", 
                   "system.memory.actual.used.pct",
                   "system.network.in.bytes",
                   "system.network.out.bytes"]
    }
    
    data = json.dumps(query).encode('utf-8')
    req = urllib.request.Request(
        f"{ES_HOST}/.ds-metricbeat-*/_search",
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            result = json.loads(r.read())
            hits = result['hits']['hits']
            print(f"Fetched {len(hits)} metric records")
            return hits
    except Exception as e:
        print(f"Error fetching metrics: {e}")
        return []

def prepare_features(hits):
    """Extract and prepare features for anomaly detection"""
    records = []
    
    for hit in hits:
        source = hit['_source']
        record = {
            'timestamp': source.get('@timestamp', ''),
            'cpu': source.get('system', {}).get('cpu', {}).get('total', {}).get('pct', 0) or 0,
            'memory': source.get('system', {}).get('memory', {}).get('actual', {}).get('used', {}).get('pct', 0) or 0,
            'net_in': source.get('system', {}).get('network', {}).get('in', {}).get('bytes', 0) or 0,
            'net_out': source.get('system', {}).get('network', {}).get('out', {}).get('bytes', 0) or 0,
        }
        records.append(record)
    
    df = pd.DataFrame(records)
    print(f"Prepared {len(df)} records with features: {list(df.columns)}")
    return df

def detect_anomalies(df):
    """Apply Isolation Forest anomaly detection"""
    features = ['cpu', 'memory', 'net_in', 'net_out']
    
    # Fill NaN values
    df[features] = df[features].fillna(0)
    
    # Normalize features
    scaler = StandardScaler()
    X = scaler.fit_transform(df[features])
    
    # Train Isolation Forest
    model = IsolationForest(
        n_estimators=100,
        contamination=0.1,
        random_state=42
    )
    
    df['anomaly_score'] = model.fit_predict(X)
    df['anomaly_raw_score'] = model.score_samples(X)
    df['is_anomaly'] = df['anomaly_score'] == -1
    
    anomaly_count = df['is_anomaly'].sum()
    print(f"Detected {anomaly_count} anomalies out of {len(df)} records ({anomaly_count/len(df)*100:.1f}%)")
    
    return df, model, scaler

def calculate_metrics(df):
    """Calculate evaluation metrics"""
    total = len(df)
    anomalies = df['is_anomaly'].sum()
    normal = total - anomalies
    
    metrics = {
        'total_records': int(total),
        'anomalies_detected': int(anomalies),
        'normal_records': int(normal),
        'anomaly_rate': round(float(anomalies/total*100), 2),
        'avg_cpu': round(float(df['cpu'].mean()), 4),
        'max_cpu': round(float(df['cpu'].max()), 4),
        'avg_memory': round(float(df['memory'].mean()), 4),
        'max_memory': round(float(df['memory'].max()), 4),
    }
    
    print("\n=== Evaluation Metrics ===")
    for k, v in metrics.items():
        print(f"  {k}: {v}")
    
    return metrics

def send_results_to_es(df, metrics):
    """Send anomaly scores back to Elasticsearch"""
    index = "anomaly-scores"
    success = 0
    
    for _, row in df.iterrows():
        doc = {
            "@timestamp": row['timestamp'],
            "host": "edge",
            "cpu": float(row['cpu']),
            "memory": float(row['memory']),
            "net_in": float(row['net_in']),
            "net_out": float(row['net_out']),
            "anomaly_score": int(row['anomaly_score']),
            "anomaly_raw_score": float(row['anomaly_raw_score']),
            "is_anomaly": bool(row['is_anomaly']),
            "model": "IsolationForest",
            "contamination": 0.1
        }
        
        data = json.dumps(doc).encode('utf-8')
        req = urllib.request.Request(
            f"{ES_HOST}/{index}/_doc",
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        
        try:
            with urllib.request.urlopen(req, timeout=5) as r:
                if r.status == 201:
                    success += 1
        except Exception as e:
            pass
    
    print(f"\nSent {success}/{len(df)} records to Elasticsearch index '{index}'")
    
    # Also save summary metrics
    summary_doc = {
        "@timestamp": datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
        "type": "evaluation_summary",
        **metrics
    }
    
    data = json.dumps(summary_doc).encode('utf-8')
    req = urllib.request.Request(
        f"{ES_HOST}/{index}/_doc",
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    urllib.request.urlopen(req, timeout=5)
    
    return success

def main():
    print("=" * 50)
    print("SAT Systems - AI Anomaly Detection Pipeline")
    print("Model: Isolation Forest")
    print("=" * 50)
    
    # Step 1: Fetch data
    print("\n[1/4] Fetching metrics from Elasticsearch...")
    hits = fetch_metrics()
    
    if not hits:
        print("No data found! Make sure Metricbeat is running.")
        return
    
    # Step 2: Prepare features
    print("\n[2/4] Preparing features...")
    df = prepare_features(hits)
    
    # Step 3: Detect anomalies
    print("\n[3/4] Running Isolation Forest...")
    df, model, scaler = detect_anomalies(df)
    
    # Step 4: Calculate metrics
    print("\n[4/4] Calculating evaluation metrics...")
    metrics = calculate_metrics(df)
    
    # Step 5: Send to Elasticsearch
    print("\n[5/5] Sending results to Elasticsearch...")
    send_results_to_es(df, metrics)
    
    print("\n✅ Pipeline complete!")
    print(f"Results stored in Elasticsearch index: anomaly-scores")

if __name__ == "__main__":
    main()
