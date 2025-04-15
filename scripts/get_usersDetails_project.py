import requests
import csv
import os

# Usage example
organization = "__org__"
project_name = "__project__"
personal_access_token = os.getenv('ADO_PAT')
csv_file = 'users_details.csv'


def get_project_users(organization, project_name, personal_access_token):
    project_id_url = f"https://dev.azure.com/{organization}/_apis/projects?api-version=6.0"

    project_response = requests.get(project_id_url, auth=('', personal_access_token))
    project_details=project_response.json().get('value',[])

    ids=[]
    for i in range(0,len(project_details)):
        if(project_details[i]['name']==project_name):
            ids.append(project_details[i]['id'])


    descriptor_url = f"https://vssps.dev.azure.com/{organization}/_apis/graph/descriptors/{ids[0]}?api-version=5.0-preview.1"

    scope_descriptor=[]
    response = requests.get(descriptor_url, auth=('', personal_access_token))
    details=response.json().get('value',[])
    scope_descriptor.append(details)

    user_url = f"https://vssps.dev.azure.com/{organization}/_apis/graph/users?scopeDescriptor={scope_descriptor[0]}&api-version=6.0-preview.1"

    user_details = requests.get(user_url, auth=('', personal_access_token))
    user_count=user_details.json().get('count',[])
    user_names = user_details.json().get('value', [])

    return user_names

def update_csv(organization, project_name, personal_access_token, csv_file):
    users = get_project_users(organization, project_name, personal_access_token)
    
    if users is None:
        print(f"No users found for project {project_name}.")
        return

    with open(csv_file, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['Project Name', 'User Principal Name'])

        for user in users:
            writer.writerow([project_name, user['principalName']])

    print(f"CSV file '{csv_file}' updated successfully with project name '{project_name}' and user details.")



update_csv(organization, project_name, personal_access_token, csv_file)
