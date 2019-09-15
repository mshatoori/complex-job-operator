#!/bin/sh

kubectl delete -f example/somejob.yaml
kubectl delete -f src/k8s/operator-deployment.yaml
kubectl delete -f src/k8s/crd.yaml
