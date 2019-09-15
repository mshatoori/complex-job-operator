import kopf
import os
from kubernetes import client
import yaml

def _create_pod(namespace, complex_job, pod_def, logger):
    api = client.CoreV1Api()

    print (f"pod_def: {pod_def}")

    #pod_def2 = yaml.safe_load(pod_def)

    #path = os.path.join(os.path.dirname(__file__), 'templates/job-pod-tpl.yaml')
    #pod = yaml.safe_load(open(path, 'rt').read())

    podName = pod_def.get('name')
    if not podName:
        raise kopf.PermanentError(f"'spec.pods.pod.name' must be set.")

    podSpec = pod_def.get('spec')
    if not podName:
        raise kopf.PermanentError(f"'spec.pods.pod.spec' must be set.")

    pod = client.V1Pod()
    pod.metadata = client.V1ObjectMeta(name=podName)
    pod.spec = podSpec #yaml.safe_load(podSpec)
    
    #data = yaml.safe_load(yaml.dump(pod))

    pod_dict = pod.to_dict()
    kopf.adopt(pod_dict, owner=complex_job)

    pod_obj = api.create_namespaced_pod(
        namespace=namespace,
        body=pod_dict
    )

    logger.info(f"POD child is created: %s", pod)

@kopf.on.create('mytracks4mac.info', 'v1', 'complexjobs')
def create_fn(body, spec, meta, namespace, logger, **kwargs):

    job_name = meta.get('name')
    pods = spec.get('pods')
    if not pods:
        raise kopf.PermanentError(f"'pods' must be set.")

    for pod_def in pods:
        _create_pod(namespace, body, pod_def,logger)

    return {'pod-name': "foo bar"}

