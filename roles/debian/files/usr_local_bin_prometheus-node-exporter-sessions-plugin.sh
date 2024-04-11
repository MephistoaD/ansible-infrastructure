#!/usr/bin/env sh

OPEN_SESSIONS=$(who | wc -l)

echo "# HELP node_exporter_open_user_shells Number of current open user sessions of users on the system."
echo "# TYPE node_exporter_open_user_shells gauge"
echo "node_exporter_open_user_shells ${OPEN_SESSIONS}"