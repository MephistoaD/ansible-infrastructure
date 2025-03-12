import requests
import json
from ansible.module_utils.basic import AnsibleModule

# Query Prometheus API
def fetch_metrics(prometheus_server, hostname, validate_certs):
    query = f"{{instance='{hostname}'}}"
    url = f"{prometheus_server}/api/v1/query"
    response = requests.get(url, params={'query': query}, verify=validate_certs)
    if response.status_code == 200:
        return response.json().get('data', {}).get('result', [])
    else:
        return []

# Structure data into hostvars
def process_metrics(metrics):
    prometheus_metrics = {}
    
    for metric in metrics:
        labels = metric.get('metric', {})
        value = float(metric.get('value', [0, 0])[1])
        metric_name = labels.pop('__name__', 'unknown_metric')
        if metric_name not in prometheus_metrics:
            prometheus_metrics[metric_name] = []
        prometheus_metrics[metric_name].append({**labels, "value": value})
    
    return prometheus_metrics

def main():
    module = AnsibleModule(
        argument_spec={
            'instances': {'type': 'list', 'required': True},
            'prometheus_server': {'type': 'str', 'required': True},
            'validate_certs': {'type': 'bool', 'default': True}
        }
    )
    
    instances = module.params['instances']
    prometheus_server = module.params['prometheus_server']
    validate_certs = module.params['validate_certs']
    
    result = dict(changed=False)
    for hostname in instances:
        metrics = fetch_metrics(prometheus_server, hostname, validate_certs)
        result[hostname] = process_metrics(metrics)
    
    module.exit_json(**result)

if __name__ == "__main__":
    main()
