from flask import Flask
from flask import Response
import requests
import json
import os
import time

FUNCTION_NAME = 'print-ip'
FUNCTION_IMAGE_URL = 'ghcr.io/openfaas/external-ip-fn:latest'
DEPLOY_ERR_TEXT = 'unable create Deployment: object is being deleted:'

def get_cluster_url(cluster_number):
    hostname = os.environ[f'OPENFAAS_URL{cluster_number}']
    password = os.environ[f'OPENFAAS_PASSWORD{cluster_number}']
    full_url = f'http://admin:{password}@{hostname}'
    return full_url

url_cluster1 = get_cluster_url(1) #"http://admin:AEAEctrk6xMu@a7459eb1453154b4ea2488e55a038782-998957349.us-east-1.elb.amazonaws.com:8080"
url_cluster2 = get_cluster_url(2) #"http://admin:BCxpAaJW5Kng@a761aeaa22ddf445baa0f67246b09e55-829286149.us-east-1.elb.amazonaws.com:8080"
current_cluster = ''
current_url = ''

deployPayload = {
        "service": FUNCTION_NAME,
        "image": FUNCTION_IMAGE_URL
}
deletePayload = {
    "functionName": FUNCTION_NAME
}
default_headers = {'content-type': 'application/json'}

app = Flask(__name__)
@app.route('/<cluster>')
def forward(cluster):
    global current_cluster
    if cluster == '1':
        current_url = url_cluster1
    elif cluster == '2':
        current_url = url_cluster2
    else:
        return Response('value should be either 1 or 2', status=400)
    if cluster != current_cluster:
        thisClusterFunctionsResp = requests.get(current_url + '/system/functions')
        thisClusterFnIsDeleted = True
        if thisClusterFunctionsResp.status_code == 200 and len(thisClusterFunctionsResp.json()) > 0:
            for fn in thisClusterFunctionsResp.json():
                if fn['name'] == FUNCTION_NAME:
                    thisClusterFnIsNotDeleted = False
                    break
        if thisClusterFnIsDeleted:
            deployResponse = None
            timeToSleep = 0.5
            while deployResponse is None or (deployResponse.status_code == 500 and deployResponse.text.startswith(DEPLOY_ERR_TEXT)):
                deployResponse = requests.post(current_url + '/system/functions', json=deployPayload, headers=default_headers)
                if deployResponse.status_code != 200:
                    time.sleep(timeToSleep)
        
        otherClusterUrl = url_cluster2 if current_url == url_cluster1 else url_cluster1
        otherClusterFunctionsResp = requests.get(otherClusterUrl + '/system/functions')
        otherHasFunctionToDelete = False
        if otherClusterFunctionsResp.status_code == 200 and len(otherClusterFunctionsResp.json()) > 0:
            for fn in otherClusterFunctionsResp.json():
                if fn['name'] == FUNCTION_NAME:
                    otherHasFunctionToDelete = True
                    break
        if otherHasFunctionToDelete:
            print(f'delete url is: {url_cluster2 if current_url == url_cluster1 else url_cluster1 + '/system/functions'}')
            deleteResponse = requests.delete(otherClusterUrl + '/system/functions', data=json.dumps(deletePayload))
            print('delete resp: ')
            print(deleteResponse)
        current_cluster = cluster
    custer_ip = requests.request("GET", current_url + '/function/' + FUNCTION_NAME)
    print(custer_ip)
    return Response(f'current cluster IP is {custer_ip.text}', status=200)