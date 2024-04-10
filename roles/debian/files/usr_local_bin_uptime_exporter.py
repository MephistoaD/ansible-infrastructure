#!/usr/bin/env python3

import time

seconds_since_boot = time.clock_gettime(time.CLOCK_BOOTTIME)


print(f"""
# HELP node_exporter_system_uptime is a customized export
# TYPE node_exporter_system_uptime gauge
node_exporter_system_uptime {seconds_since_boot}
""")