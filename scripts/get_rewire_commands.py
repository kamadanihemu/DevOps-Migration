import requests
from requests.auth import HTTPBasicAuth

ado_org = "__org__"
ado_project_normal = "__project__"
ado_project = ado_project_normal.replace(' ', '%20')
ado_pat = "__ADO_PAT__"
gh_org = "__ghorg__"
ServiceConn = "__serviceconn__"
prefix = "__prefix__"

# Base URL for Azure DevOps REST API
BASE_URL = f"https://dev.azure.com/{ado_org}/{ado_project}/_apis"

# Headers for the API requests
headers = {
    "Content-Type": "application/json"
}

# Function to get the list of pipelines
def get_pipelines():
    url = f"{BASE_URL}/pipelines?api-version=6.0"
    response = requests.get(url, headers=headers, auth=HTTPBasicAuth('', ado_pat))
    response.raise_for_status()
    return response.json()["value"]

# Function to get the repository details for a pipeline
def get_pipeline_repository(pipeline_id):
    url = f"{BASE_URL}/build/definitions/{pipeline_id}?api-version=6.0"
    response = requests.get(url, headers=headers, auth=HTTPBasicAuth('', ado_pat))
    response.raise_for_status()
    definition = response.json()
    repository = definition.get("repository", {})
    return repository

# Function to get the full name of the pipeline
def get_full_pipeline_name(pipeline):
    folder = pipeline.get("folder", "")
    name = pipeline["name"]
    if folder:
        return f"{folder}\\{name}"
    return name

pipeline_info = []

# Main function to get pipelines and their source repositories
def main():
    pipelines = get_pipelines()
    for pipeline in pipelines:
        pipeline_id = pipeline["id"]
        full_pipeline_name = get_full_pipeline_name(pipeline).replace('\\\\', '\\')
        repository = get_pipeline_repository(pipeline_id)
        
        repo_name = repository.get("name", "Repository name not found")
        repo_url = repository.get("url", "Repository URL not found")
        
        pipeline_info.append({
            "pipelinename": full_pipeline_name,
            "reponame": repo_name
        })


main()


def rewire():
        text_file_name = "pipelines.txt"

    # Write the extracted information to a text file
        with open(text_file_name, mode='w') as file:
                for repo in pipeline_info:
                        file.write(
                                f"gh ado2gh rewire-pipeline --ado-org '{ado_org}' --ado-team-project '{ado_project_normal}' --ado-pipeline '{repo['pipelinename']}' --github-org '{gh_org}' --github-repo '{prefix}{repo['reponame']}' --service-connection-id '{ServiceConn}'\n\n\n"
                        )

        print(f"Data has been written to {text_file_name}")
rewire()