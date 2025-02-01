#!/usr/bin/env python3

import socket

def fetch_openvpn_status(host='localhost', port=7505, timeout=10):
    try:
        with socket.create_connection((host, port), timeout) as sock:
            sock.recv(1024)  # Read initial OpenVPN interface message
            sock.sendall(b"status 3\r\n")
            data = b""
            while True:
                chunk = sock.recv(4096)
                if not chunk:
                    break
                data += chunk
                if b"END" in data:
                    break
            sock.sendall(b"exit\r\n")
            return data.decode('utf-8')
    except Exception as e:
        print(f"Error connecting to OpenVPN management interface: {e}")
        return None

def parse_client_list(data):
    clients = {}
    for line in data.split('\n'):
        if line.startswith("CLIENT_LIST"):
            fields = line.split('\t')
            client = {
                "Common Name": fields[1],
                "Real Address": fields[2],
                "Virtual Address": fields[3],
                "Virtual IPv6 Address": fields[4],
                "Bytes Received": int(fields[5]),
                "Bytes Sent": int(fields[6]),
                "Connected Since": fields[7],
                "Connected Since (time_t)": int(fields[8]),
                "Username": fields[9],
                "Client ID": fields[10],
                "Peer ID": fields[11],
                "Data Channel Cipher": fields[12],
                "Origin": f"{fields[1]} since: {fields[7]} ({fields[2]} -> {fields[3]})"
            }
            clients[fields[1]] = client  # Use Common Name as key
    return clients

def print_prometheus_metrics(clients):
    for client_name, client_data in clients.items():
        print(f"openvpn_active_client_connection{{common_name=\"{client_name}\", real_address=\"{client_data['Real Address']}\", virtual_address=\"{client_data['Virtual Address']}\", connected_since=\"{client_data['Connected Since']}\", origin=\"{client_data['Origin']}\"}} 1")

if __name__ == "__main__":
    status_output = fetch_openvpn_status()
    if status_output:
        clients = parse_client_list(status_output)
        print_prometheus_metrics(clients)
