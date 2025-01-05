#!/usr/bin/env python3

import re
import sys
import os

PROMETHEUS_FILE = "/var/lib/prometheus/node-exporter/pve_node_state.prom"

def write_prometheus_metric(state):
    """
    Writes the current state metric to the Prometheus file.
    """
    metric_value = 1 if state == "ACTIVE" else 0
    metric_content = f'pve_node_state_active{{state="{state}"}} {metric_value}\n'

    try:
        os.makedirs(os.path.dirname(PROMETHEUS_FILE), exist_ok=True)
        with open(PROMETHEUS_FILE, 'w') as f:
            f.write(metric_content)
        print(f"Prometheus metric written: {metric_content.strip()}")
    except Exception as e:
        print(f"Error writing Prometheus metric: {e}")

def ensure_node_state(file_path, hostname, state=None):
    """
    Updates or retrieves the node state in the configuration file and updates Prometheus metrics.
    """
    config_path = f"/etc/pve/nodes/{hostname}/config"
    regex = r"^#`node_state%3A (.*)`$"
    line_to_set = f"#`node_state%3A {state.upper()}`" if state else None

    try:
        # Read the file if it exists
        if os.path.exists(config_path):
            with open(config_path, 'r') as file:
                lines = file.readlines()
        else:
            lines = []

        current_state = None
        modified = False

        for i, line in enumerate(lines):
            match = re.match(regex, line)
            if match:
                current_state = match.group(1)
                if state:
                    # Replace matching line with the new state
                    lines[i] = line_to_set + "\n"
                    modified = True
                break

        if state and not modified:
            # Append the new state if no matching line was found
            lines.append(line_to_set + "\n")

        # Write changes to the file
        if state:
            with open(config_path, 'w') as file:
                file.writelines(lines)
            print(f"Node state set to {state.upper()} in {config_path}")
            write_prometheus_metric(state.upper())
        else:
            # Display current state if requested
            print(f"Current node state: {current_state if current_state else 'undefined'}")
            if current_state:
                write_prometheus_metric(current_state)

    except Exception as e:
        print(f"Error accessing or updating {config_path}: {e}")

def main():
    if len(sys.argv) < 2:
        print("Usage: node-state <drain|undrain|show>")
        sys.exit(1)

    hostname = os.uname().nodename
    command = sys.argv[1].lower()

    if command == "drain":
        ensure_node_state('/etc/pve/nodes', hostname, "DRAIN")
    elif command == "undrain":
        ensure_node_state('/etc/pve/nodes', hostname, "ACTIVE")
    elif command == "show":
        ensure_node_state('/etc/pve/nodes', hostname)
    else:
        print(f"Unknown command: {command}")
        print("Usage: node-state <drain|undrain|show>")
        sys.exit(1)

if __name__ == "__main__":
    main()
