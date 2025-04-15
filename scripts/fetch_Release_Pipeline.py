import requests
import base64
import csv
import os

# Variables
ado_org_name= "__org__"
project_name= "__project__"
PAT= os.getenv('ADO_PAT')

# Headers for authentication
headers = {
    'Content-Type': 'application/json',
    'Authorization': f'Basic {base64.b64encode(f":{PAT}".encode()).decode()}'
}

project_name = project_name.replace(' ', '%20')

# Function to fetch release pipelines
def get_release_pipelines():
    url = f"https://vsrm.dev.azure.com/{ado_org_name}/{project_name}/_apis/release/definitions?api-version=6.0"
    print(url)
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()["value"]
    else:
        print(f"Error fetching release pipelines: {response.status_code}")
        return []

# Function to fetch associated build pipeline for a release pipeline
def get_associated_build_pipelines(pipeline_id):
    url = f"https://vsrm.dev.azure.com/{ado_org_name}/{project_name}/_apis/release/definitions/{pipeline_id}?api-version=6.0"
    print(url)
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        artifacts = response.json().get("artifacts", [])
        build_pipelines = [artifact["definitionReference"]["definition"]["name"] for artifact in artifacts if artifact["type"] == "Build"]
        return build_pipelines
    else:
        print(f"Error fetching associated build pipelines for pipeline {pipeline_id}: {response.status_code}")
        return []

# Get list of release pipelines
release_pipelines = get_release_pipelines()

# Prepare CSV file
csv_file = "release_pipelines_report.csv"
with open(csv_file, mode='w', newline='') as file:
    writer = csv.writer(file)
    writer.writerow(["Release Pipeline Name", "Associated Build Pipelines"])

    # Get associated build pipelines for each release pipeline and write to CSV
    for pipeline in release_pipelines:
        pipeline_id = pipeline["id"]
        pipeline_name = pipeline["name"]
        associated_build_pipelines = get_associated_build_pipelines(pipeline_id)
        writer.writerow([pipeline_name, ", ".join(associated_build_pipelines)])

print(f"Report saved to {csv_file}")
