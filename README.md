# SAT Systems Infrastructure Configurations

## Project: Secure Automated Telemetry - Edge Cloud IaaS Platform
## Author: Hafsa Metmari
## Master PFE - 2026

## VM Infrastructure
- VM1 (Cloud): 192.168.87.132 - OpenStack + ELK + Wazuh + Kafka
- VM2 (Edge): 192.168.87.131 - Docker + Filebeat + Metricbeat + Wazuh Agent + Prometheus
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

## Structure
- elk-docker-compose.yml       → ELK Stack deployment
- logstash.conf                → Logstash pipeline config
- wazuh-docker-compose.yml     → Wazuh Manager deployment
- kafka-docker-compose.yml     → Kafka + Zookeeper deployment
- kolla-globals.yml            → OpenStack Kolla-Ansible config
