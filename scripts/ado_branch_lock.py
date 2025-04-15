import os
import requests
from requests.auth import HTTPBasicAuth


## User who is locking branch, will have access to commit to the branch

organization = '__org__'
project = '__project__'
personal_access_token = os.getenv('ADO_PAT')
repository_name = '__repo__'
project = project.replace(' ', '%20')


repo_url = f"https://dev.azure.com/{organization}/{project}/_apis/git/repositories?api-version=6.0"

headers = {
    'Content-Type': 'application/json',
    'Accept': 'application/json'
}

response = requests.get(repo_url, headers=headers, auth=HTTPBasicAuth('', personal_access_token))

if response.status_code == 200:
    repositories = response.json()['value']
    repository_id = None

    for repo in repositories:
        if repo['name'].lower() == repository_name.lower():
            repository_id = repo['id']
            print(f"Found repository: {repository_name} (ID: {repository_id})")
            break

    if repository_id:
        branches_url = f"https://dev.azure.com/{organization}/{project}/_apis/git/repositories/{repository_id}/refs?filter=heads/&api-version=6.0"

        branches_response = requests.get(branches_url, headers=headers, auth=HTTPBasicAuth('', personal_access_token))

        if branches_response.status_code == 200:
            branches = branches_response.json()['value']
            for branch in branches:
                branch_name = branch['name'].split('/')[-1]
                print(f"Locking branch: {branch_name}")

                lock_url = f"https://dev.azure.com/{organization}/{project}/_apis/git/repositories/{repository_id}/refs?filter=heads/{branch_name}&api-version=6.0"

                #data payload to lock the branch
                data = {
                    "isLocked": True
                }

                lock_response = requests.patch(lock_url, headers=headers, auth=HTTPBasicAuth('', personal_access_token), json=data)

                if lock_response.status_code == 200:
                    print(f"Branch '{branch_name}' locked successfully.")
                else:
                    print(f"Failed to lock the branch '{branch_name}'. Status code: {lock_response.status_code}, Response: {lock_response.text}")
        else:
            print(f"Failed to fetch branches for repository '{repository_name}'. Status code: {branches_response.status_code}, Response: {branches_response.text}")
    else:
        print(f"Repository '{repository_name}' not found.")
else:
    print(f"Failed to fetch repositories. Status code: {response.status_code}, Response: {response.text}")


