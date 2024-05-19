#!/usr/bin/env python3

import sys
import os

PROM_FILE = '/var/lib/prometheus/node-exporter/autoup.prom'
LOCKED_CONTENT = """# HELP node_exporter_autoup_locked State of last maintenance job on the machine (0 = unlocked, 1 = locked)
# TYPE node_exporter_autoup_locked gauge
node_exporter_autoup_locked 1
"""
UNLOCKED_CONTENT = """# HELP node_exporter_autoup_locked State of last maintenance job on the machine (0 = unlocked, 1 = locked)
# TYPE node_exporter_autoup_locked gauge
node_exporter_autoup_locked 0
"""

def print_help():
    print("Usage:")
    print("  autoup lock      Locking machine for future maintenances")
    print("  autoup unlock    Unlocking machine for future maintenances")
    print("  autoup           Returns the content of /var/lib/prometheus/node-exporter/autoup.prom")
    print("  autoup --help    Prints this help message")
    print("  autoup -h        Prints this help message")

def lock_machine():
    print("Locking machine for future maintenances...")
    with open(PROM_FILE, 'w') as f:
        f.write(LOCKED_CONTENT)
    print_content()

def unlock_machine():
    print("Unlocking machine for future maintenances...")
    with open(PROM_FILE, 'w') as f:
        f.write(UNLOCKED_CONTENT)
    print_content()

def print_content():
    if os.path.exists(PROM_FILE):
        with open(PROM_FILE, 'r') as f:
            print(f.read())
    else:
        print(f"File {PROM_FILE} does not exist.")

def main():
    if len(sys.argv) == 1:
        print_content()
    elif len(sys.argv) == 2:
        if sys.argv[1] in ['--help', '-h']:
            print_help()
        elif sys.argv[1] == 'lock':
            lock_machine()
        elif sys.argv[1] == 'unlock':
            unlock_machine()
        else:
            print("Unknown command. Use --help or -h for usage instructions.")
            sys.exit(1)
    else:
        print("Too many arguments. Use --help or -h for usage instructions.")
        sys.exit(1)

if __name__ == '__main__':
    main()
