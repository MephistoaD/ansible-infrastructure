#!/usr/bin/env bash

TEMPFILE=/tmp/upgradable_packages.prom
EXPORTER_DIR=/var/lib/prometheus/node-exporter/

UPGRADABLE_PACKAGES=$(apt-get -s --no-download dist-upgrade -V | grep '=>')

echo "# upgradable packages" > $TEMPFILE

# Process each line in UPGRADABLE_PACKAGES
while IFS= read -r line; do
    # Extract the package name
    package=$(echo "$line" | awk '{print $1}')
    # Trim leading and trailing spaces and escape double quotes in the line for Prometheus syntax
    escaped_line=$(echo "$line" | sed 's/"/\\"/g' | sed 's/^ *//;s/ *$//')
    # Append the line to the TEMPFILE
    echo "upgradable_package{package=\"$package\",origin=\"$escaped_line\"} 1" >> $TEMPFILE
done <<< "$UPGRADABLE_PACKAGES"

# Move the tempfile to the exporter directory
mv $TEMPFILE $EXPORTER_DIR
