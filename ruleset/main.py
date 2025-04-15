import requests
from requests.auth import HTTPBasicAuth
import subprocess, json
from collections import defaultdict

organization = "__org__"
project = "__project__"
ado_pat = "__ADO_PAT__"
prefix = "__prefix__"
ghorg = "__ghorg__"
gh_pat = "__GH_PAT__"
headers = {
    "content-type": "application/json"
}
gh_repos = {}

# get the repos and repo ids from a project
subprocess.run(["echo", f"{ado_pat}", "|", "az", "devops", "login", "--org", f"https://dev.azure.com/{organization}"], shell=True, text=True, capture_output=True)


repo_id = {}
project = project.replace(' ', '%20')
url1 = f"https://dev.azure.com/{organization}/{project}/_apis/git/repositories?api-version=7.1"
auth = HTTPBasicAuth("",ado_pat)
response = requests.get(url=url1, auth=auth, headers=headers)
if response.status_code == 200:
        output = response.json()
        for repo in output["value"]:
            repo_id[output["value"][output["value"].index(repo)]["name"]] = output["value"][output["value"].index(repo)]["id"]
# print(repo_id)
seen_entries = set()

repos_gh = []

subprocess.run(["echo", f"{gh_pat}", "|", "gh", "auth", "login", "--with-token"], shell=True, capture_output=True, text=True)
for repo in repo_id:
    branches_gh = subprocess.run(["gh", "api", f"repos/{ghorg}/{prefix}{repo}/branches", "--paginate"], shell=True, capture_output=True, text=True)
    branches_gh = json.loads(branches_gh.stdout)
    if isinstance(branches_gh, list):
        repos_gh.append(repo)
# print(repos_gh)

filtered_repo_id = {key: value for key, value in repo_id.items() if key in repos_gh}
# print(filtered_repo_id)

# get the policy for each branch
branch_with_policies = {}
result=[]
for repo in filtered_repo_id:
    # url2 = f"https://dev.azure.com/{organization}/{project}/_apis/policy/configurations?repositoryId={filtered_repo_id[repo]}&api-version=7.1"
    url2 = f"https://dev.azure.com/{organization}/{project}/_apis/policy/configurations?repositoryId={filtered_repo_id[repo]}&api-version=6.0"
    # url2 = f"https://dev.azure.com/{organization}/{project}/_apis/policy/configurations?repositoryId={filtered_repo_id[repo]}&api-version=6.0"
    # print(url2)
    auth = HTTPBasicAuth("",ado_pat)
    response = requests.get(url=url2, auth=auth, headers=headers)
    if response.status_code == 200:
        output = response.json()
        data = output
        # break
        # test(output["value"])
        names=[]
        branch=[]
        branch_policy_keys=[]
        branch_policy_values=[]
        repo_ids=[]
        result=[]
        comments=[]
        results=[]
        approver_count=[]
        merge_strategy=[]
        vote_count=[]
        allow_down_vote=[]
        reset=[]
        requirevote=[]
        reset_rejection=[]
        block_vote=[]
        require_vote_per_iteration=[]
        keys_to_search=["minimumApproverCount","allowSquash","allowRebase","allowRebaseMerge","allowNoFastForward","creatorVoteCounts","allowDownvotes","resetOnSourcePush","requireVoteOnLastIteration","resetRejectionsOnSourcePush","blockLastPusherVote","requireVoteOnEachIteration"]
        for i in range(0,len(data['value'])):
        #     repo_ids.append(data['value'][i]['type']['id'])
            if 'refName' in data['value'][i]['settings']['scope'][0]:
                repo_ids.append(data['value'][i]['settings']['scope'][0]['repositoryId'])
                branch.append(data['value'][i]['settings']['scope'][0]['refName'])
                comment=data['value'][i]['type']['displayName']
                if comment=='Comment requirements':
                    comments.append(True)
                else:
                    comments.append(False)
                result=[]
                settings=data['value'][i]['settings']
                for key in keys_to_search:
                    if key in settings:
                        result.append(settings[key])
                    else:
                        if key==keys_to_search[0]:
                            result.append(0)
                        else:
                            result.append(False)
            #     print(result)
                lst=[]
                keys=[]
                settings_value=[]
            #     for i in range(1,len(result)):
                for i in range(1,5):
                    if result[i]==True:
                        keys.append(keys_to_search[i])
                for j in range(5,len(result)):
                    settings_value.append(result[j])
                lst.append(result[0])
                lst.append(keys)
                lst.append(settings_value)
                approver_count.append(lst[0])
                merge_strategy.append(lst[1])
                vote_count.append(lst[2][0])
                allow_down_vote.append(lst[2][1])
                reset.append(lst[2][2])
                requirevote.append(lst[2][3])
                reset_rejection.append(lst[2][4])
                block_vote.append(lst[2][5])
                require_vote_per_iteration.append(lst[2][6])
        # for i in range(0,len(data['value'])):
        data1=[]
        for val1,val2,val3,val4,val5,val6,val7,val8,val9,val10,val11,val12 in zip(repo_ids,branch,approver_count,comments,vote_count,allow_down_vote,reset,requirevote,reset_rejection,block_vote,require_vote_per_iteration,merge_strategy):
            data1.append({"repo-id":val1,"branch-name":val2,"min-approver":val3,"comment-requirement":val4,"creatorVoteCounts":val5,"allowDownvotes":val6,"resetOnSourcePush":val7,"requireVoteOnLastIteration":val8,"resetRejectionsOnSourcePush":val9,"blockLastPusherVote":val10,"requireVoteOnEachIteration":val11,"merge-strategy":val12})
        merged_data = defaultdict(lambda: {'min-approver': 0,'comment-requirement':False,"creatorVoteCounts":False,"allowDownvotes":False,"resetOnSourcePush":False,"requireVoteOnLastIteration":False,"resetRejectionsOnSourcePush":False,"blockLastPusherVote":False,"requireVoteOnEachIteration":False,'merge-strategy': []})
        for entry in data1:
            key = (entry['repo-id'], entry['branch-name'])
            merged_data[key]['min-approver'] = max(merged_data[key]['min-approver'], entry['min-approver'])
            merged_data[key]['comment-requirement'] = merged_data[key]['comment-requirement'] or entry['comment-requirement']
            merged_data[key]['creatorVoteCounts'] = merged_data[key]['creatorVoteCounts'] or entry['creatorVoteCounts']
            merged_data[key]['allowDownvotes'] = merged_data[key]['allowDownvotes'] or entry['allowDownvotes']
            merged_data[key]['resetOnSourcePush'] = merged_data[key]['resetOnSourcePush'] or entry['resetOnSourcePush']
            merged_data[key]['requireVoteOnLastIteration'] = merged_data[key]['requireVoteOnLastIteration'] or entry['requireVoteOnLastIteration']
            merged_data[key]['resetRejectionsOnSourcePush'] = merged_data[key]['resetRejectionsOnSourcePush'] or entry['resetRejectionsOnSourcePush']
            merged_data[key]['blockLastPusherVote'] = merged_data[key]['blockLastPusherVote'] or entry['blockLastPusherVote']
            merged_data[key]['requireVoteOnEachIteration'] = merged_data[key]['requireVoteOnEachIteration'] or entry['requireVoteOnEachIteration']

            if len(entry['merge-strategy']) > len(merged_data[key]['merge-strategy']):
                merged_data[key]['merge-strategy'] = entry['merge-strategy']
        result = [{'repo-id': k[0], 'branch-name': k[1], 'min-approver': v['min-approver'],'comment-requirement':v['comment-requirement'],"creatorVoteCounts":v['creatorVoteCounts'],"allowDownvotes":v['allowDownvotes'],"resetOnSourcePush":v['resetOnSourcePush'],"requireVoteOnLastIteration":v['requireVoteOnLastIteration'],"resetRejectionsOnSourcePush":v['resetRejectionsOnSourcePush'],"blockLastPusherVote":v['blockLastPusherVote'],"requireVoteOnEachIteration":v['requireVoteOnEachIteration'], 'merge-strategy': v['merge-strategy']} for k, v in merged_data.items()]
        break
# print(result)
reverse_repo_id = {v: k for k, v in filtered_repo_id.items()}
for item in result:
    repo_id_value = item.get('repo-id')
    if repo_id_value in reverse_repo_id:
        item['repo-id'] = reverse_repo_id[repo_id_value]

filtered_results = [repo for repo in result if repo['repo-id'] in repos_gh]
print(filtered_results)

string = f"gh_repos = {filtered_results}"
new_string = string.replace("'", '"')
with open('gh_repos.txt', 'w') as file:
    file.write(new_string)
    file.close()

string = f"gh_repos = {filtered_results}"
new_string = string.replace("'", '"')
json_output=json.dumps(string, indent=4).replace("True","true").replace("False","false")
print(json_output)
with open('terraform.tfvars', 'w') as file:
    file.write(json_output.replace('"', '').replace("'", '"'))
    file.close()
