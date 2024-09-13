#!/usr/bin/env python3

import subprocess
import json
import http.client
import urllib.parse

# Static final variables
ORIG_LOCKFILE = "/etc/nixos/flake.lock"
TEMP_LOCKFILE = "/etc/nixos/flake.lock.new"
GITHUB_API_HOST = "api.github.com"
OUTPUT_FILE = "/var/lib/prometheus/node-exporter/pending_flake_upgrades.prom"
SEVERITY_FACTOR = 0.01

def run_command(command, cwd=None):
    """
    Runs a shell command in the specified working directory (cwd).
    """
    try:
        result = subprocess.run(command, stderr=subprocess.PIPE, check=True, cwd=cwd)
        return result
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {e.stderr.decode('utf-8')}")
        exit(1)

def load_json_file(file_path):
    """
    Loads the contents of a JSON file into a Python dictionary.
    """
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading JSON file {file_path}: {e}")
        exit(1)

def update_flake_lock():
    """
    Updates the flake.lock file by running the update command.
    """
    flake_update_command = [
        "nix", "flake", "update",
        "--override-input", "nixpkgs", "github:NixOS/nixpkgs",
        "--output-lock-file", TEMP_LOCKFILE
    ]
    run_command(flake_update_command, cwd="/etc/nixos/")

def get_differences_of_lockfiles(current_lockfile, new_lockfile):
    """
    Loads both lockfiles and returns a list of inputs containing the differences.
    """
    current_data = load_json_file(current_lockfile)
    new_data = load_json_file(new_lockfile)

    differences = []

    # Iterate over nodes in the current lockfile
    for node_name, node_data in current_data.get("nodes", {}).items():
        if node_name == "root":
            continue  # Skip the root node

        # Check if the node is present in both lockfiles
        new_node_data = new_data.get("nodes", {}).get(node_name)
        if not new_node_data:
            continue

        # Get details for comparison
        current_locked = node_data.get("locked", {})
        new_locked = new_node_data.get("locked", {})

        # Compare the revisions (or any other relevant fields)
        rev_current = current_locked.get("rev")
        rev_new = new_locked.get("rev")

        if rev_current != rev_new:
            difference = {
                "input": f"{node_name}",
                "type": current_locked.get("type", "unknown"),
                "owner": current_locked.get("owner", "unknown"),
                "repo": current_locked.get("repo", "unknown"),
                "rev_current": rev_current,
                "rev_new": rev_new,
                "commit_count": 0  # Initialize with 0; will be updated later
            }
            differences.append(difference)

    return differences

def get_commits_between_revisions(owner, repo, base, head):
    """
    Retrieves the list of commits between two revisions from the GitHub API using http.client.

    Args:
        owner (str): The repository owner.
        repo (str): The repository name.
        base (str): The base revision (older commit).
        head (str): The head revision (newer commit).

    Returns:
        int: The number of commits between the two revisions.
    """
    conn = http.client.HTTPSConnection(GITHUB_API_HOST)
    endpoint = f"/repos/{owner}/{repo}/compare/{urllib.parse.quote(base)}...{urllib.parse.quote(head)}"
    headers = {'User-Agent': 'Python http.client'}
    
    conn.request("GET", endpoint, headers=headers)
    response = conn.getresponse()

    if response.status == 200:
        data = json.loads(response.read().decode('utf-8'))
        commits = data.get('commits', [])
        return len(commits)
    else:
        print(f"Error: {response.status} - {response.reason}")
        return 0

def process_differences(differences):
    """
    Processes the differences to fetch commit counts between revisions for each repository.
    Adds the commit count to the differences data structure and writes the results to the output file.
    """
    results = []
    for diff in differences:
        owner = diff['owner']
        repo = diff['repo']
        rev_current = diff['rev_current']
        rev_new = diff['rev_new']

        if owner != "unknown" and repo != "unknown":
            commit_count = get_commits_between_revisions(owner, repo, rev_current, rev_new)
            diff['commit_count'] = commit_count  # Update the commit count in the differences data structure
            origin = f"{diff["input"]}: {diff["type"]}/{owner}/{repo}/{rev_current} -> {rev_new}"
            prometheus_metric = f'''nixos_pending_flake_upgrade{{origin="{origin}",rev_current="{rev_current}",rev_new="{rev_new}"}} {commit_count * SEVERITY_FACTOR}
'''
            results.append(prometheus_metric)

    # Write results to the output file
    with open(OUTPUT_FILE, 'w') as f:
        f.write("\n".join(results))

def main():
    """
    Main function to orchestrate the update and comparison of flake locks.
    """
    update_flake_lock()
    differences = get_differences_of_lockfiles(
        current_lockfile=ORIG_LOCKFILE,
        new_lockfile=TEMP_LOCKFILE
    )

    if differences:
        process_differences(differences)
    
    # Print the differences as JSON with an indent of 2
    print(json.dumps(differences, indent=2))

if __name__ == "__main__":
    main()
