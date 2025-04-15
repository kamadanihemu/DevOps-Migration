import requests
from requests.auth import HTTPBasicAuth
import subprocess

ado_pat = "__ADO_PAT__"
organization = "__org__"
project = "__project__"
prefix = "__prefix__"
ghorg = "__ghorg__"

headers = {
        "content-type": "application/json"
    }

url1 = f"https://dev.azure.com/{organization}/{project}/_apis/git/repositories?api-version=4.1"
auth = HTTPBasicAuth("",ado_pat)
response = (requests.get(url=url1, auth=auth, headers=headers)).json()
repos = response["value"]

f = open("migratetogh.ps1", "w")
for repo in repos:
    f.write(f'gh ado2gh migrate-repo --ado-org "{organization}" --ado-team-project "{project}" --ado-repo "{repo["name"]}" --github-org "{ghorg}" --github-repo "{prefix}{repo["name"]}"\n')
f.close()