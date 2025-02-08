#!/usr/bin/env python3

import subprocess
import json
import re
import socket

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
    hostname = socket.gethostname()
    output = run_command(["pvesh", "get", f"/nodes/{hostname}/ceph/status", "--output-format", "json"])
    if not output:
        return None
    return json.loads(output)

def format_prometheus(cluster_status, quorum_info, membership_info, ceph_status):
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
    
    return "\n".join(output)

def main():
    cluster_status = get_cluster_status()
    quorum_info, membership_info = get_votequorum_status()
    ceph_status = get_ceph_status()
    print(format_prometheus(cluster_status, quorum_info, membership_info, ceph_status))

if __name__ == "__main__":
    main()
