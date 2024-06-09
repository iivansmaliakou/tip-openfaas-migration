#!/bin/bash
kubectl -n kube-system create sa tiller
kubectl create clusterrolebinding tiller-cluster-rule --clusterrole=cluster-admin --serviceaccount=kube-system:tiller
kubectl apply -f https://raw.githubusercontent.com/openfaas/faas-netes/master/namespaces.yml
export PASSWORD=$(head -c 12 /dev/urandom | shasum | cut -d' ' -f1)
kubectl -n openfaas create secret generic basic-auth --from-literal=basic-auth-user=admin --from-literal=basic-auth-password=$PASSWORD
helm repo add openfaas https://openfaas.github.io/faas-netes/
helm repo update
helm upgrade openfaas --install openfaas/openfaas --namespace openfaas --set functionNamespace=openfaas-fn --set serviceType=LoadBalancer --set basic_auth=true  --set gateway.replicas=2 --set queueWorker.replicas=2
echo "openfaas password is: $(kubectl -n openfaas get secret basic-auth -o jsonpath="{.data.basic-auth-password}" | base64 --decode)"
eval export OPENFAAS_PASSWORD$1=$(kubectl -n openfaas get secret basic-auth -o jsonpath="{.data.basic-auth-password}" | base64 --decode)
kubectl --namespace=openfaas get deployments -l "release=openfaas, app=openfaas"
kubectl get svc -n openfaas -o wide
eval export OPENFAAS_URL$1=$(kubectl get svc -n openfaas gateway-external -o  jsonpath='{.status.loadBalancer.ingress[*].hostname}'):8080
eval echo Your gateway URL is: \$OPENFAAS_URL$1