import kopf
import os
from kubernetes import client
from kubernetes.client.apis import core_v1_api
import yaml
import string

def _get_complex_job(name, namespace):
    api = client.CustomObjectsApi()
    complex_job = api.get_namespaced_custom_object(
        group="mytracks4mac.info",
        version="v1",
        name=name,
        namespace=namespace,
        plural="complexjobs",
    )

    return complex_job

def _get_pod(name, namespace):
    pod = core_v1_api.CoreV1Api().read_namespaced_pod(name=name, namespace=namespace)

    return pod

def _create_pod(namespace, complex_job, pod_def, logger):
    api = client.CoreV1Api()
    complex_job_name = complex_job['metadata']['name']

    pod_name = pod_def.get('name')
    if not pod_name:
        raise kopf.PermanentError(f"'spec.pods.pod.name' must be set.")

    podSpec = pod_def.get('spec')
    if not pod_name:
        raise kopf.PermanentError(f"'spec.pods.pod.spec' must be set.")

    pod = client.V1Pod()
    pod.metadata = client.V1ObjectMeta(name=f'{complex_job_name}-{pod_name}')
    pod.spec = podSpec


    pod.metadata.labels = {"complexJob": complex_job_name, "podName": pod_name}
    
    # Create resource in cluster
    pod_dict = pod.to_dict()
    kopf.adopt(pod_dict, owner=complex_job)

    pod_obj = api.create_namespaced_pod(
        namespace=namespace,
        body=pod_dict
    )

    logger.info(f"POD child is created: %s", pod)

def _add_env(obj, name, value):
    if not 'env' in obj:
        obj['env'] = []
    
    obj['env'].append({'name': name, 'value': value})

def _add_env_to_containers(pod, name, value):
    spec = pod['spec']
    if 'containers' in spec:
        containers = spec['containers']

        for container in containers:
            _add_env(container, name, value)

    if 'initContainers' in spec:
        init_containers = pod['spec']['initContainers']

        for container in init_containers:
            _add_env(container, name, value)

def _replace_env(obj, search, replacement):
    print("********************* 1")
    if 'env' in obj:
        print("********************* 2")
        new_envs = []
        for env in obj['env']:
            print("********************* 3")
            name = env['name']
            value = env['value']
            new_value = value.replace(search, replacement)
            print(f"******* {name} {value} {new_value}")
            new_envs.append({'name': name, 'value': new_value})

        obj['env'] = new_envs

def _replace_env_of_containers(pod, search, replacement):
    spec = pod['spec']
    if 'containers' in spec:
        containers = spec['containers']

        for container in containers:
            _replace_env(container, search, replacement)

    if 'initContainers' in spec:
        init_containers = pod['spec']['initContainers']

        for container in init_containers:
            _replace_env(container, search, replacement)

@kopf.on.create('mytracks4mac.info', 'v1', 'complexjobs')
def complex_job_create_fn(body, spec, meta, namespace, logger, **kwargs):

    job_name = meta.get('name')
    pods = spec.get('pods')
    if not pods:
        raise kopf.PermanentError(f"'pods' must be set.")

    if len(pods) > 0:
        _create_pod(namespace, body, pods[0],logger)

    return {'pod-name': "foo bar"}

@kopf.on.update('mytracks4mac.info', 'v1', 'complexjobs')
def pod_update_fn(body, spec, status, namespace, logger, **kwargs):
    print(f"###### Complex Job updated: {body}")

@kopf.on.create('', 'v1', 'pods', labels={'complexJob': None})
def pod_create_fn(body, spec, meta, status, namespace, logger, **kwargs):
    print(f"###### POD created: {status}")

@kopf.on.update('', 'v1', 'pods', labels={'complexJob': None})
def pod_update_fn(spec, status, meta, namespace, logger, **kwargs):
    print(f"###### POD updated: {status}")

    if status.get('phase') == "Running":
        hostIP = status.get('hostIP')
        complex_job_name = meta['labels']['complexJob']
        pod_name = meta['labels']['podName']

        complex_job = _get_complex_job(complex_job_name, namespace)

        # Try to find next pod
        pods = complex_job['spec']['pods']

        create_next = False
        additional_envs = []
        for pod in pods:
            if create_next:
                for additional_env in additional_envs:
                    _add_env_to_containers(pod, additional_env['name'], additional_env['value'])
                    _replace_env_of_containers(pod, f"${additional_env['name']}", additional_env['value'])
                _create_pod(namespace, complex_job, pod, logger)
                break

            if pod['name'] == pod_name:
                create_next = True

            pod_res = _get_pod(f"{complex_job_name}-{pod['name']}", namespace)
            pod_ip = pod_res.status.pod_ip
            additional_envs.append({'name': f"{pod['name'].upper()}_POD_IP", 'value': pod_ip})

@kopf.on.field('', 'v1', 'pods', field='status.phase', labels={'complexJob': None})
def somefield_changed(old, new, **_):
    print(f"###### phase updated {new}")