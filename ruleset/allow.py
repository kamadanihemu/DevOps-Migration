import requests
from requests.auth import HTTPBasicAuth
import json
import re
import ast

# Define the path to the terraform.tfvars file
file_path = "gh_repos.txt"
gh_pat = "__github_token__"
owner = "__ghorg__"
prefix = "__prefix__"

def parse_tfvars(file_path):
    with open(file_path,'r') as file:
        data=file.read()
    lines=data.splitlines()
    lines=[line.strip() for line in lines if not line.strip().startswith("#")]
    cleaned_content=" ".join(lines)
 
    if '=' in cleaned_content:
        key,value=cleaned_content.split('=',1)
        key=key.strip()
        value=value.strip()
 
        if value:
            parsed_value=ast.literal_eval(value)
            return parsed_value
        
repos = parse_tfvars(file_path)
print(repos)

filtered_repos = [repo for repo in repos if repo['merge-strategy']]
extracted_data_list = []

headers = {
    "Accept": "application/vnd.github.v3+json",
    "X-GitHub-Api-Version": "2022-11-28",
}

for repo in filtered_repos:
    url = f"https://api.github.com/repos/{owner}/{prefix}{repo['repo-id']}/rulesets"
    auth = HTTPBasicAuth("", gh_pat)
    response = requests.get(url=url, auth=auth, headers=headers)
    if response.status_code == 200:
        output = response.json()
        for ruleset in output:
            ruleset_name = ruleset.get('name')
            if repo['branch-name'] in ruleset_name:
                extracted_data = {
                    'repo-id': repo['repo-id'],
                    'branch-name': repo['branch-name'],
                    'merge-strategy': [repo['merge-strategy']],
                    'id': ruleset.get('id'),
                    'ruleset-name': ruleset_name
                }
                extracted_data_list.append(extracted_data)

parallels = {
    'allowSquash': 'squash',
    'allowRebase': 'rebase',
    'allowRebaseMerge': 'rebase'
}

def map_and_filter_merge_strategies(merge_strategies, parallels):
    mapped_strategies = []
    for strategy in merge_strategies[0]:  # Access the first (and only) list in merge-strategy
        if strategy == 'allowNoFastForward':
            continue
        if strategy in parallels:
            mapped_strategies.append(parallels[strategy])
    return mapped_strategies

# Update the extracted_data_list
for repo in extracted_data_list:
    repo['merge-strategy'] = [map_and_filter_merge_strategies(repo['merge-strategy'], parallels)]

def get_existing_ruleset(owner, repo, ruleset_id, headers):
    url = f"https://api.github.com/repos/{owner}/{repo}/rulesets/{ruleset_id}"
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Failed to retrieve ruleset: {response.status_code}")
        print(response.json())
        return None

# Function to update the ruleset
def update_ruleset(owner, repo, ruleset_id, data, headers):
    url = f"https://api.github.com/repos/{owner}/{repo}/rulesets/{ruleset_id}"
    response = requests.put(url, headers=headers, json=data)
    if response.status_code == 200:
        print("Ruleset updated successfully")
        print(response.json())
    else:
        print(f"Failed to update ruleset: {response.status_code}")
        print(response.json())

# Iterate through the extracted_data_list and update the rulesets
for ruleset in extracted_data_list:
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "Authorization": f"Bearer {gh_pat}"
    }

    # Retrieve the existing ruleset
    existing_ruleset = get_existing_ruleset(owner, f"{prefix}{ruleset['repo-id']}", ruleset['id'], headers)
    
    if existing_ruleset:
        # Update the allowed_merge_methods in the pull_request rule
        for rule in existing_ruleset['rules']:
            if rule['type'] == 'pull_request':
                rule['parameters']['allowed_merge_methods'] = ruleset['merge-strategy'][0]
        
        # Prepare the data payload
        data = {
            "name": existing_ruleset['name'],
            "target": existing_ruleset['target'],
            "source_type": existing_ruleset['source_type'],
            "source": existing_ruleset['source'],
            "enforcement": existing_ruleset['enforcement'],
            "conditions": existing_ruleset['conditions'],
            "rules": existing_ruleset['rules']
        }

        print("Data to be sent:", data)
        
        # Update the ruleset
        update_ruleset(owner, f"{prefix}{ruleset['repo-id']}", ruleset['id'], data, headers)