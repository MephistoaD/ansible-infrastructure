#!/usr/bin/env python3

import re
import sys
import os
import json
import argparse

CONFIG_PATH = "/etc/pve/nodes/{}/config"
STATE_BLOCK_START = "```node-state"
STATE_BLOCK_END = "```"

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

def save_node_state(hostname, state):
    """Saves the node state to the config file without modifying other lines."""
    config_path = CONFIG_PATH.format(hostname)
    state_json = json.dumps(state, indent=2)
    block = f"{STATE_BLOCK_START}\n{state_json}\n{STATE_BLOCK_END}\n"
    
    try:
        if not os.path.exists(config_path):
            lines = []
        else:
            with open(config_path, 'r') as file:
                lines = file.readlines()
        
        new_lines = []
        inside_block = False
        block_inserted = False
        
        for line in lines:
            if line.strip().startswith(f"# {STATE_BLOCK_START}"):
                inside_block = True
                new_lines.append("# " + block.replace("\n", "\n# "))
                block_inserted = True
                continue
            if inside_block and line.strip().startswith(f"# {STATE_BLOCK_END}"):
                inside_block = False
                continue
            if not inside_block:
                new_lines.append(line)
        
        if not block_inserted:
            new_lines.append("# " + block.replace("\n", "\n# "))
        
        with open(config_path, 'w') as file:
            file.writelines(new_lines)
        
        print(f"Node state updated successfully for {hostname}.")
    except Exception as e:
        print(f"Error writing node state for {hostname}: {e}")

def init_node_state(hostname):
    """Initializes the node state if not present."""
    default_state = {
        "accept_guests": {"lxc": False, "vm": False},
        "drain": {"lxc": False, "vm": False, "eject_pinned": False}
    }
    save_node_state(hostname, default_state)

def get_node_state(hostname, key):
    """Retrieves a specific node state value."""
    state = load_node_state(hostname)
    if not state:
        print(f"Node state not initialized for {hostname}.")
        return
    
    keys = key.split('.')
    value = state
    for k in keys:
        value = value.get(k)
        if value is None:
            print(f"Key '{key}' not found in node state for {hostname}.")
            return
    
    print(value)

def set_node_state(hostname, key, value):
    """Sets a specific node state value."""
    state = load_node_state(hostname) or {}
    keys = key.split('.')
    ref = state
    for k in keys[:-1]:
        ref = ref.setdefault(k, {})
    ref[keys[-1]] = value.lower() == "true"
    save_node_state(hostname, state)

def main():
    parser = argparse.ArgumentParser(description="Manage node state.")
    parser.add_argument("--node", help="Specify the target node", default=os.uname().nodename)
    parser.add_argument("command", choices=["show", "init", "get", "set"], help="Command to execute")
    parser.add_argument("args", nargs="*", help="Additional arguments for the command")

    args = parser.parse_args()
    hostname = args.node

    if args.command == "show":
        state = load_node_state(hostname)
        print(json.dumps(state, indent=2) if state else f"Node state not initialized for {hostname}.")
    elif args.command == "init":
        state = load_node_state(hostname)
        if state:
            print(f"Node state already initialized for {hostname}.")
            sys.exit(2)
        else:
            init_node_state(hostname)
    elif args.command == "get" and len(args.args) == 1:
        get_node_state(hostname, args.args[0])
    elif args.command == "set" and len(args.args) == 2:
        set_node_state(hostname, args.args[0], args.args[1])
    else:
        parser.print_help()
        sys.exit(1)

if __name__ == "__main__":
    main()
