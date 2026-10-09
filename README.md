# SAT — Secure AI-Enhanced Telemetry for Edge-Cloud IaaS Infrastructure

## Author: Hafsa Metmari
## Master PFE - 2026

SAT is a unified Edge-Cloud observability and security platform that integrates six telemetry pipelines, three security enforcement layers, a multi-source AI anomaly detection engine, and a DevSecOps automation framework into a single operationally validated system.
## VM Infrastructure
- VM1 (Cloud): 192.168.87.132 - OpenStack + ELK + Wazuh + Kafka
- VM2 (Edge): 192.168.87.131 - Docker + Filebeat + Metricbeat + Wazuh Agent + Prometheus
  VM2 (Edge Gateway — 192.168.87.131)          VM1 (Cloud Control Plane — 192.168.87.132)
## Architecture Overview

<img width="251" height="75" alt="image" src="https://github.com/user-attachments/assets/43591d38-0623-48a8-8144-99339d56f44e" />

## End-to-End Telemetry and Security Data Flow
<img width="1403" height="747" alt="enddiagramwith animation (1)" src="https://github.com/user-attachments/assets/374e4309-93bf-43c1-a980-618d8a4defe5" />

## SAT Operations Center
<img width="915" height="395" alt="image" src="https://github.com/user-attachments/assets/27744be6-c7c5-4abb-995c-1d10b2024504" />

## Grafana Node Exporter Dashboard
<img width="945" height="450" alt="image" src="https://github.com/user-attachments/assets/5c0a9181-1747-4097-a251-93e73170af40" />

## Grafana cAdvisor Dashboard
<img width="945" height="491" alt="image" src="https://github.com/user-attachments/assets/0be256bd-d31a-4bdf-b3b5-0d812a8b3cb2" />

## Grafana Alert Rules Status
<img width="945" height="254" alt="image" src="https://github.com/user-attachments/assets/4a05d217-4f14-4f78-b889-185d605657dc" />

## Kibana Edge Gateway Dashboard
<img width="784" height="325" alt="image" src="https://github.com/user-attachments/assets/86023c8a-5fb1-4d29-b8b2-ef41c3ebec9e" />

## Kibana Container Metrics Dashboard
<img width="945" height="322" alt="image" src="https://github.com/user-attachments/assets/a96ff3ff-da99-42a0-a51c-74ba25f7e735" />

## Kibana Security Analytics Dashboard
<img width="818" height="319" alt="image" src="https://github.com/user-attachments/assets/7b6ecb02-7c2d-4d6a-ab69-7776538114d7" />

##  Kibana Wazuh Alert Discovery
<img width="843" height="365" alt="image" src="https://github.com/user-attachments/assets/79887209-b698-4eb2-a8bc-9077bee6a465" />

## Kibana Alert Field Statistics
<img width="945" height="161" alt="image" src="https://github.com/user-attachments/assets/ac11f859-3e21-4f75-ba23-9528f265f0ae" />

## Kibana AI Anomaly Detection Dashboard
<img width="945" height="349" alt="image" src="https://github.com/user-attachments/assets/af156fd3-03d8-43f5-ad3a-11b24c030400" />

## Software Prerequisites
- Docker Engine 24+ and Docker Compose v2+
- Python 3.10+ with pip
- Ansible 2.14+
- Kolla-Ansible (for OpenStack deployment)
- WireGuard
## Deployment Guide
### Step 1 — WireGuard VPN (run on both VMs)
Install WireGuard and apply the configurations:
```
# On VM1 (Cloud)
sudo apt install wireguard -y
sudo cp vpn/vm1-wg0.conf.txt /etc/wireguard/wg0.conf
sudo systemctl enable wg-quick@wg0
sudo systemctl start wg-quick@wg0

# On VM2 (Edge)
sudo apt install wireguard -y
sudo cp vpn/vm2-wg0.conf.txt /etc/wireguard/wg0.conf
sudo systemctl enable wg-quick@wg0
sudo systemctl start wg-quick@wg0

# Verify tunnel (from VM1)
ping 10.0.0.2
```
### Step 2 — Cloud Control Plane (VM1)
2a — OpenStack via Kolla-Ansible
```
# Install Kolla-Ansible
pip install kolla-ansible

# Copy globals config
cp cloud/kolla-globals.yml /etc/kolla/globals.yml

# Deploy OpenStack (377 tasks, ~30 min)
kolla-ansible -i inventory bootstrap-servers
kolla-ansible -i inventory prechecks
kolla-ansible -i inventory deploy
```
### 2b — ELK Stack
```
cd cloud/
docker compose -f elk-docker-compose.yml up -d

# Verify Elasticsearch is running
curl -u elastic:sat_elastic_2026 http://localhost:9200/_cluster/health
```
### 2c — Wazuh Manager
```
docker compose -f wazuh-docker-compose.yml up -d
```
2d — Kafka + ZooKeeper
```
docker compose -f kafka-docker-compose.yml up -d
```
2e — Wazuh Alert Ingestion (cron job)
```
# Install dependencies
pip install elasticsearch requests

# Add to crontab (every 5 minutes)
crontab -e
# Add this line:
# */5 * * * * python3 /path/to/cloud/wazuh-to-es.py
```
Step 3 — Edge Gateway (VM2)
Option A — Automated with Ansible (recommended)
````
# From VM1 or your local machine
cd ansible/sat-edge-deploy/

# Edit inventory.ini with your VM2 IP
nano inventory.ini

# Run the playbook (16 tasks, ~30 seconds)
ansible-playbook -i inventory.ini site.yml
````
Option B — Manual with Docker Compose
````
# On VM2
cd edge/

# Deploy workload services
docker compose -f services-docker-compose.yml up -d

# Deploy Filebeat
docker compose -f filebeat-docker-compose.yml up -d

# Deploy Metricbeat
docker compose -f metricbeat-docker-compose.yml up -d

# Start Prometheus and Node Exporter
sudo systemctl start prometheus
sudo systemctl start node-exporter
````
Step 4 — AI Anomaly Detection Pipeline (VM1)
```
# Install dependencies
pip install elasticsearch scikit-learn pandas numpy

# Step 1 — Extract features from Elasticsearch
python3 ai/compute_metrics_v3.py

# Step 2 — Run Isolation Forest detection
python3 ai/anomaly_detection.py

# Results are indexed into anomaly-scores-v2 index in Elasticsearch
# View results in Kibana → AI Anomaly Detection dashboard
```
## Key Results

| Metric | Value |
|--------|-------|
| Total documents indexed | 252,348 |
| Evaluation period | 10 days continuous |
| Pipeline failures | 0 |
| VPN packet loss | 0% |
| VPN latency | < 2ms RTT |
| AI Recall | 100% |
| AI Accuracy | 92.5% |
| Edge RAM utilization | 7.9% |
| Ansible tasks executed | 393 (0 failures) |
| Security alerts | 1,451 |
| MITRE ATT&CK techniques detected | 3 (T1040, T1110, T1548) |
## Verification Commands

```bash
# Check all Edge containers running
docker ps

# Check Elasticsearch indices
curl -u elastic:sat_elastic_2026 http://VM1_IP:9200/_cat/indices?v

# Check WireGuard tunnel
sudo wg show

# Check Wazuh agent status (VM2)
sudo systemctl status wazuh-agent

# Check Prometheus targets
curl http://localhost:9090/api/v1/targets
```
## Repository Structure

```
sat-infra-configs/
├── cloud/
│   ├── elk-docker-compose.yml        # ELK Stack deployment
│   ├── logstash.conf                 # Logstash pipeline config
│   ├── wazuh-docker-compose.yml      # Wazuh Manager deployment
│   ├── wazuh-logstash.conf           # Wazuh → Logstash pipeline
│   ├── wazuh-to-es.py                # Wazuh alert ingestion script
│   ├── kafka-docker-compose.yml      # Kafka + ZooKeeper deployment
│   └── kolla-globals.yml             # OpenStack Kolla-Ansible config
├── edge/
│   ├── filebeat.yml                  # Filebeat log collection config
│   ├── metricbeat.yml                # Metricbeat metrics config
│   ├── prometheus.yml                # Prometheus scraping config
│   ├── filebeat-docker-compose.yml   # Filebeat container
│   ├── metricbeat-docker-compose.yml # Metricbeat container
│   └── services-docker-compose.yml   # Edge workload services
├── ansible/
│   └── sat-edge-deploy/
│       ├── site.yml                  # Main Ansible playbook
│       ├── inventory.ini             # Host inventory
│       └── roles/edge_monitoring/    # Custom Ansible role (16 tasks)
├── ai/
│   ├── compute_metrics_v3.py         # Feature extraction
│   └── anomaly_detection.py          # Isolation Forest pipeline
└── vpn/
    ├── vm1-wg0.conf.txt              # WireGuard config VM1
    └── vm2-wg0.conf.txt              # WireGuard config VM2
```

