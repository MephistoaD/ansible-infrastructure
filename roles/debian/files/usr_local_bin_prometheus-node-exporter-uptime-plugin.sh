#!/bin/bash

# Retrieve the elapsed time for the process with PID 1
elapsed_time=$(ps -p 1 -o etime=)

# Extract hours, minutes, and seconds from the elapsed time
IFS=':' read -r hours minutes seconds <<< "$elapsed_time"

# Calculate total elapsed time in seconds
#total_seconds=$(( (hours * 3600) + (minutes * 60) + seconds ))

echo "# HELP node_exporter_system_uptime is a customized export"
echo "# TYPE node_exporter_system_uptime gauge"
echo "node_exporter_system_uptime $hours"

exit 0