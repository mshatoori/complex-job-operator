#!/bin/sh

kubectl apply -f src/k8s/crd.yaml
kubectl apply -f src/k8s/operator-deployment.yaml
kubectl apply -f example/somejob.yaml
