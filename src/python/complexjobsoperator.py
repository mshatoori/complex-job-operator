import kopf

def _create_pod(pod):
    path = os.path.join(os.path.dirname(__file__), 'templates/job-pod-tpl.yaml')
    pod = yaml.safe_load(open(path, 'rt').read())

    podName = pod.get('name')
    if not podName:
        raise kopf.PermanentError(f"'spec.pods.pod.name' must be set.")

    pod['metadata']['name'] = podName
    
    #data = yaml.safe_load(yaml.dump(pod))

    kopf.adopt(pod, owner=body)

    api = kubernetes.client.CoreV1Api()
    pod = api.create_namespaced_pod(
        namespace=namespace,
        body=pod,
    )

    logger.info(f"POD child is created: %s", pod)

@kopf.on.create('mytracks4mac.info', 'v1', 'complexjobs')
def create_fn(spec, meta, namespace, logger, **kwargs):

    jobName = meta.get('name')
    pods = spec.get('pods')
    if not pods:
        raise kopf.PermanentError(f"'pods' must be set.")

    for pod in pods:
        _create_pod(pod)

    #return {'pod-name': obj.metadata.name}

