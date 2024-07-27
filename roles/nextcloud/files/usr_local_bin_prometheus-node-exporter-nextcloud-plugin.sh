#!/bin/bash

# Global variable to store the latest release version
LATEST_NEXTCLOUD_RELEASE=""
NEXTCLOUD_LOCAL_VERSION=""

TEMPFILE=/tmp/nextcloud_pending_upgrades.prom
OUTPUT=/var/lib/prometheus/node-exporter/nextcloud_pending_upgrades.prom

function write_to_exporter {
    local value=$1
    local origin=$2
    local local_version=$3
    local latest_version=$4

    echo "# HELP node_exporter_nextcloud_upgrade_pending Shows the need for an upgrade of nextcloud (0 = Everything up to date, 1 = upgrade available)" > $TEMPFILE
    echo -e "# TYPE node_exporter_nextcloud_upgrade_pending gauge" >> $TEMPFILE
    echo -e "node_exporter_nextcloud_upgrade_pending{origin=\"$origin\",local_version=\"$local_version\",latest_version=\"$latest_version\"} $value\n" >> $TEMPFILE

    mv $TEMPFILE $OUTPUT
}

function get_local_nextcloud_version {
    local config_file="/var/www/nextcloud/config/config.php"

    if [[ -f "$config_file" ]]; then
        NEXTCLOUD_LOCAL_VERSION=$(php -r "
        include '$config_file';
        echo \$CONFIG['version'];
        ")
    else
        echo "Config file not found"
        exit 1
    fi
}

function get_latest_nextcloud_release() {
    local repo="nextcloud/server"
    local api_url="https://api.github.com/repos/$repo"
    local latest_url="$api_url/releases/latest"

    # Fetch the latest release version using curl and jq
    local response=$(curl -s $latest_url)
    if [ $? -ne 0 ]; then
        echo "Failed to fetch the latest release information"
        return 1
    fi

    local latest_release=$(echo $response | jq -r '.tag_name' | sed 's/^v//')

    if [ -z "$latest_release" ]; then
        echo "Failed to parse the latest release version"
        return 1
    fi

    # Store the latest release version in the global variable
    LATEST_NEXTCLOUD_RELEASE="$latest_release"
}

# Call the function
get_latest_nextcloud_release
get_local_nextcloud_version

# Compare the local and latest release versions
if [[ "$NEXTCLOUD_LOCAL_VERSION" == "$LATEST_NEXTCLOUD_RELEASE"* ]]; then
    write_to_exporter 0 \
        "Nextcloud is on the current version $NEXTCLOUD_LOCAL_VERSION" \
        $NEXTCLOUD_LOCAL_VERSION \
        $LATEST_NEXTCLOUD_RELEASE
else
    write_to_exporter 1 \
        "Nextcloud has a pending version upgrade $NEXTCLOUD_LOCAL_VERSION -> $LATEST_NEXTCLOUD_RELEASE" \
        $NEXTCLOUD_LOCAL_VERSION \
        $LATEST_NEXTCLOUD_RELEASE
fi

# FIXME: bug when nextcloud local version is higher than latest version