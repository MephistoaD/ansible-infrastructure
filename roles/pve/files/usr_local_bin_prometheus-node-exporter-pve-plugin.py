#!/usr/bin/env python3

import subprocess
import json
import re
import socket
import os

CONFIG_PATH = "/etc/pve/nodes/{}/config"
METRIC_PATH = "/var/lib/prometheus/node-exporter/pve.prom"
LOCALHOST = socket.gethostname()

def load_node_state(hostname):
    """Loads the node state from the config file, tolerating '# ' prefixes."""
    config_path = CONFIG_PATH.format(hostname)
    if not os.path.exists(config_path):
        return None
    
    try:
        with open(config_path, 'r') as file:
            content = file.readlines()
            cleaned_content = "\n".join(line.lstrip('# ').rstrip() for line in content)
            match = re.search(r"```node-state\n(.*?)\n```", cleaned_content, re.DOTALL)
            if match:
                return json.loads(match.group(1))
    except Exception as e:
        print(f"Error reading node state: {e}")
    
    return None

def run_command(command):
    """Runs a shell command and returns the output as a string."""
    try:
        return subprocess.check_output(command, universal_newlines=True).strip()
    except subprocess.CalledProcessError:
        return None

def get_cluster_status():
    """Fetches cluster status information."""
    return json.loads(run_command(["pvesh", "get", "/cluster/status", "--output-format", "json"]))

def get_votequorum_status():
    """Fetches votequorum status using pvecm status."""
    output = run_command(["pvecm", "status"])
    return parse_votequorum_status(output)

def parse_votequorum_status(output):
    """Parses votequorum status from pvecm output."""
    quorum_info = {}
    membership_info = []
    
    if not output:
        return quorum_info, membership_info
    
    for line in output.split("\n"):
        line = line.strip()
        if line.startswith("Expected votes"):
            quorum_info["expected_votes"] = int(line.split(":")[1].strip())
        elif line.startswith("Highest expected"):
            quorum_info["highest_expected"] = int(line.split(":")[1].strip())
        elif line.startswith("Total votes"):
            quorum_info["total_votes"] = int(line.split(":")[1].strip())
        elif line.startswith("Quorum:"):
            quorum_info["quorum"] = int(line.split(":")[1].strip())
        elif re.match(r"0x[0-9a-fA-F]+", line):
            parts = line.split()
            membership_info.append({
                "nodeid": int(parts[0], 16),
                "votes": int(parts[1]),
                "ip": parts[2]
            })
    
    return quorum_info, membership_info

def get_ceph_status():
    """Fetches Ceph cluster health status."""
    hostname = LOCALHOST
    output = run_command(["pvesh", "get", f"/nodes/{hostname}/ceph/status", "--output-format", "json"])
    if not output:
        return None
    return json.loads(output)

def format_prometheus(cluster_status, quorum_info, membership_info, ceph_status, node_states):
    """Formats the data in Prometheus syntax."""
    cluster_name = next(item["name"] for item in cluster_status if item["type"] == "cluster")
    nodes = [item for item in cluster_status if item["type"] == "node"]
    
    output = []
    
    for node in nodes:
        output.append(f'pve_node_online{{cluster="{cluster_name}", node="{node["name"]}", ip="{node.get("ip", "")}", nodeid="{node["nodeid"]}"}} {node["online"]}')
    
    for member in membership_info:
        output.append(f'pve_quorum_votes{{cluster="{cluster_name}", node="{member["ip"]}", ip="{member["ip"]}", nodeid="{member["nodeid"]}"}} {member["votes"]}')
    
    output.append(f'pve_quorum_expected_votes{{cluster="{cluster_name}"}} {quorum_info.get("expected_votes", 0)}')
    output.append(f'pve_quorum_highest_expected{{cluster="{cluster_name}"}} {quorum_info.get("highest_expected", 0)}')
    output.append(f'pve_quorum_total_votes{{cluster="{cluster_name}"}} {quorum_info.get("total_votes", 0)}')
    output.append(f'pve_quorum_threshold{{cluster="{cluster_name}"}} {quorum_info.get("quorum", 0)}')
    
    if ceph_status:
        ceph_health = ceph_status["health"]
        health_status = 1 if ceph_health["status"] == "HEALTH_OK" else 0
        health_message = ceph_health["status"]
        output.append(f'pve_ceph_health_status{{cluster="{cluster_name}", origin="{health_message}"}} {health_status}')
        for check, details in ceph_health.get("checks", {}).items():
            severity = details.get("severity", "UNKNOWN")
            message = details.get("summary", {}).get("message", "")
            count = details.get("summary", {}).get("count", 0)
            output.append(f'pve_ceph_health_checks{{cluster="{cluster_name}", check="{check}", severity="{severity}", origin="{check}({severity}): {message}"}} {count}')
    
    if node_states:
        for node, state in node_states.items():
            if state is not None:
                for key1, value in state.items():
                    for key2, value in value.items():
                        output.append(f'pve_node_state_{key1}_{key2}{{cluster="{cluster_name}", node="{node}", origin="{key1}.{key2}={value}"}} {int(value)}')
        if node_states[LOCALHOST]:
            state = node_states[LOCALHOST]
            accept_lxc = state['accept_guests']['lxc'] and not state['drain']['lxc']
            accept_vm = state['accept_guests']['vm'] and not state['drain']['vm']
            if (accept_lxc or accept_vm): # node accepts guest
                accepted_types = []
                if accept_lxc:
                    accepted_types.append('lxc')
                if accept_vm:
                    accepted_types.append('vm')
                accepted_types = json.dumps(accepted_types).replace('"', '')
                output.append(f'pve_node_state_active{{cluster="{cluster_name}", node="{LOCALHOST}", state="ACTIVE", origin="Node accepts guests of the type {accepted_types}"}} 1')
            else: # node does not accept guest
                output.append(f'pve_node_state_active{{cluster="{cluster_name}", node="{LOCALHOST}", state="DRAIN", origin="Node is drained"}} 0')

    return "\n".join(output)

def main():
    cluster_status = get_cluster_status()
    quorum_info, membership_info = get_votequorum_status()
    ceph_status = get_ceph_status()
    nodes = [node["name"] for node in cluster_status if node["type"] == "node"]
    node_states = {node: load_node_state(node) for node in nodes}
    metrics = format_prometheus(cluster_status, quorum_info, membership_info, ceph_status, node_states)
    
    with open(METRIC_PATH, "w") as file:
        file.write(metrics + "\n")

if __name__ == "__main__":
    main()