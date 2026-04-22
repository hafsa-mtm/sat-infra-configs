# SAT Systems Infrastructure Configurations

## Project: Secure Automated Telemetry - Edge Cloud IaaS Platform
## Author: Hafsa Metmari
## Master PFE - 2026

## VM Infrastructure
- VM1 (Cloud): 192.168.87.132 - OpenStack + ELK + Wazuh + Kafka
- VM2 (Edge): 192.168.87.131 - Docker + Filebeat + Metricbeat + Wazuh Agent + Prometheus

## Structure
- elk-docker-compose.yml       → ELK Stack deployment
- logstash.conf                → Logstash pipeline config
- wazuh-docker-compose.yml     → Wazuh Manager deployment
- kafka-docker-compose.yml     → Kafka + Zookeeper deployment
- kolla-globals.yml            → OpenStack Kolla-Ansible config
