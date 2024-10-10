#!/usr/bin/env python3

import subprocess
import json
import http.client
import urllib.parse
import argparse
import os

class CommandRunner:
    """
    Handles running shell commands.
    """
    def __init__(self):
        pass

    def run(self, command, cwd=None):
        """
        Runs a shell command in the specified working directory.
        Returns the result of the command.
        """
        try:
            result = subprocess.run(command, stderr=subprocess.PIPE, stdout=subprocess.PIPE, check=True, cwd=cwd)
            return result.stdout.decode('utf-8').strip()
        except subprocess.CalledProcessError as e:
            print(f"Command failed with error:\n{e.stderr.decode('utf-8')}")
            exit(1)

class JSONLoader:
    """
    Handles loading and processing JSON files.
    """
    @staticmethod
    def load(file_path):
        try:
            with open(file_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading JSON file {file_path}: {e}")
            exit(1)

class FlakeUpdater:
    """
    Handles updating the flake.lock file.
    """
    def __init__(self, command_runner, revision, temp_lockfile):
        self.command_runner = command_runner
        self.revision = revision
        self.temp_lockfile = temp_lockfile

    def update(self):
        command = [
            "nix", "flake", "update",
            "--override-input", "nixpkgs", f"github:NixOS/nixpkgs/{self.revision}",
            "--output-lock-file", self.temp_lockfile
        ]
        self.command_runner.run(command, cwd="/etc/nixos/")

class LockfileComparator:
    """
    Compares two flake lock files and returns the differences.
    """
    def __init__(self, json_loader):
        self.json_loader = json_loader

    def get_differences(self, current_lockfile, new_lockfile):
        current_data = self.json_loader.load(current_lockfile)
        new_data = self.json_loader.load(new_lockfile)

        differences = []

        for node_name, node_data in current_data.get("nodes", {}).items():
            if node_name == "root":
                continue  # Skip the root node

            new_node_data = new_data.get("nodes", {}).get(node_name)
            if not new_node_data:
                continue

            current_locked = node_data.get("locked", {})
            new_locked = new_node_data.get("locked", {})

            rev_current = current_locked.get("rev")
            rev_new = new_locked.get("rev")

            if rev_current != rev_new:
                differences.append({
                    "input": node_name,
                    "type": current_locked.get("type", "unknown"),
                    "owner": current_locked.get("owner", "unknown"),
                    "repo": current_locked.get("repo", "unknown"),
                    "rev_current": rev_current,
                    "rev_new": rev_new,
                    "commit_count": 0  # Initialize with 0; will be updated later
                })

        return differences

class GitHubAPI:
    """
    Handles API requests to GitHub.
    """
    def __init__(self, api_host):
        self.api_host = api_host

    def get_commit_count(self, owner, repo, base, head):
        conn = http.client.HTTPSConnection(self.api_host)
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

class DifferenceProcessor:
    """
    Processes differences and writes the result to the output file.
    """
    def __init__(self, github_api, output_file, severity_factor):
        self.github_api = github_api
        self.output_file = output_file
        self.severity_factor = severity_factor

    def process(self, differences):
        results = []
        for diff in differences:
            owner = diff['owner']
            repo = diff['repo']
            rev_current = diff['rev_current']
            rev_new = diff['rev_new']

            if owner != "unknown" and repo != "unknown":
                commit_count = self.github_api.get_commit_count(owner, repo, rev_current, rev_new)
                diff['commit_count'] = commit_count

                origin = f"{diff['input']}: {diff['type']}/{owner}/{repo}/{rev_current} -> {rev_new}"
                prometheus_metric = (
                    f'nixos_pending_flake_upgrade{{origin="{origin}",'
                    f'rev_current="{rev_current}",rev_new="{rev_new}"}} '
                    f'{commit_count * self.severity_factor}'
                )
                results.append(prometheus_metric)

        with open(self.output_file, 'w') as f:
            f.write("\n".join(results))

def parse_arguments():
    """
    Parses command-line arguments.
    """
    parser = argparse.ArgumentParser(description='Flake upgrade checker script.')
    parser.add_argument('--revision', required=True, help='The revision to be used in the flake update (e.g., main, unstable)')
    return parser.parse_args()

def main():
    # Parse arguments
    args = parse_arguments()

    # Set up constants
    ORIG_LOCKFILE = "/etc/nixos/flake.lock"
    TEMP_LOCKFILE = "/etc/nixos/flake.lock.new"
    OUTPUT_FILE = "/var/lib/prometheus/node-exporter/pending_flake_upgrades.prom"
    SEVERITY_FACTOR = 0.01

    # Initialize helpers and services
    command_runner = CommandRunner()
    json_loader = JSONLoader()
    flake_updater = FlakeUpdater(command_runner, args.revision, TEMP_LOCKFILE)
    lockfile_comparator = LockfileComparator(json_loader)
    github_api = GitHubAPI("api.github.com")
    difference_processor = DifferenceProcessor(github_api, OUTPUT_FILE, SEVERITY_FACTOR)

    # Orchestrate the flake upgrade and comparison
    flake_updater.update()

    differences = lockfile_comparator.get_differences(
        current_lockfile=ORIG_LOCKFILE,
        new_lockfile=TEMP_LOCKFILE
    )

    if differences:
        difference_processor.process(differences)

    print(json.dumps(differences, indent=2))

if __name__ == "__main__":
    main()
