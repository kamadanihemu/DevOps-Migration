import subprocess, json, os
import pandas as pd
from tabulate import tabulate
import requests
from requests.auth import HTTPBasicAuth
import shutil

organization = "__org__"
project = "__project__"
prefix = "__prefix__"
ghorg = "__ghorg__"
# organization = "Deloitte-RFA"
# project = "Hybrid Operate Dev Portal"
# prefix = ""
repos_ado = {}
repos_gh = {}
comparision = {}
prs = {}
commit_comparision = {}

gh_pat = os.getenv('GH_PAT')
ado_pat = os.getenv('ADO_PAT')

subprocess.run(["echo", f"{ado_pat}", "|", "az", "devops", "login", "--org", f"https://dev.azure.com/{organization}"], shell=True, text=True, capture_output=True)
subprocess.run(["echo", f"{gh_pat}", "|", "gh", "auth", "login", "--with-token"], shell=True, capture_output=True, text=True)

#match branches
#match total prs and specific branch prs
#match commits
#size of the repo

print("script execution started...")

repo_ids = {}
headers = {
    "content-type": "application/json"
}

print("script execution started...")

url1 = f"https://dev.azure.com/{organization}/{project}/_apis/git/repositories?api-version=7.1"
auth = HTTPBasicAuth("",ado_pat)
response = requests.get(url=url1, auth=auth, headers=headers)
if response.status_code == 200:
    output = response.json()
    output = output["value"]
    # print(output)
    for item in output:
        if "defaultBranch" in item:
            repo_ids[item["name"]]=[ item["id"], item["defaultBranch"][11:]]
    # print(repo_ids)

def compare_branches():
    print(f"fetching repos and comparing the branches in project {project}")
    # get the repos present in a project in ADO
    # az repos list --organization https://dev.azure.com/Deloitte-RFA --project 'Hybrid Operate Dev Portal'
    repos_list = subprocess.run(["az", "repos", "list", "--organization", f"https://dev.azure.com/{organization}", "--project", project], shell=True, capture_output=True, text=True)
    # print(repos_list)
    repos_list = json.loads(repos_list.stdout)
    # print(f'number of repos in project {organization} are {len(repos_list)}')
    for i in repos_list:
        repos_ado[repos_list[repos_list.index(i)]['name']] = ""

    # get the number of branches in each repo from ado and gh
    # gh api repos/{ghorg}/ho-dev-portal/branches --paginate --jq 'length'
    # az repos ref list --org https://dev.azure.com/Deloitte-RFA --project 'Hybrid Operate Dev Portal' --repository 'ho-dev-portal' --filter heads/ | select-string descriptor | measure-object -l
    for repo in repos_ado:
        branches = subprocess.run(["az", "repos", "ref", "list", "--org", f"https://dev.azure.com/{organization}", "--project", project, "--repository", repo, "--filter", "heads/", "|", "grep", "refs/heads/", "|", "wc", "-l" ], shell=True, capture_output=True, text=True)
        branches = json.loads(branches.stdout)
        repos_ado[repo] = branches
        repo = repo.replace(' ', '-')
        branches_gh = subprocess.run(["gh", "api", f"repos/{ghorg}/{prefix}{repo}/branches", "--paginate"], shell=True, capture_output=True, text=True)
        branches_gh = json.loads(branches_gh.stdout)
        # try comaring type
        if isinstance(branches_gh, list):
            repos_gh[repo] = len(branches_gh)
        else:
            repos_gh[repo] = 'not migrated'
    d1={k.replace(" ","-"): v for k,v in repos_ado.items()}
 
    for key,value in repos_gh.items():
        if key in d1:
            if value== d1[key]:
    
                comparision[key] = {"branches_ado": d1[key], "branches_gh": repos_gh[key], "matched": True}
            elif value == 'not migrated':
                comparision[key] = {"branches_ado": d1[key], "branches_gh": repos_gh[key], "matched": 'NA'}
            else:
                comparision[key] = {"branches_ado": d1[key], "branches_gh": repos_gh[key], "matched": False}

    # for repo in repos_ado:
    #     if repos_ado[repo] == repos_gh[repo]:
    #         comparision[repo] = {"branches_ado": repos_ado[repo], "branches_gh": repos_gh[repo], "matched": True}
    #     elif repos_gh[repo] == 'not migrated':
    #         comparision[repo] = {"branches_ado": repos_ado[repo], "branches_gh": repos_gh[repo], "matched": 'NA'}
    #     else:
    #         comparision[repo] = {"branches_ado": repos_ado[repo], "branches_gh": repos_gh[repo], "matched": False}

    # print(comparision)
    df = pd.DataFrame.from_dict(comparision, orient='index')
    print(tabulate(df, headers='keys', tablefmt='grid'))
    print("Repo and branch comparision completed")
    print("+++++++++++++++++++++++++++++++++++++++")

compare_branches()

def compare_prs():
    ado_pr_list = []
    gh_pr_list = []

    for repo in repo_ids:
        prs_ado = 0
        skip = 0
        # print(repo)
        prs_gh = subprocess.run(["gh", "pr", "list", "--repo", f"{ghorg}/{prefix}{repo}", "-s", "closed", "-L", "100000", "|", "wc", "-l"], shell=True, capture_output=True, text=True)
        prs_gh = int(prs_gh.stdout.strip())
        gh_pr_list.append({'repo_name': repo, 'prs_gh': prs_gh})
        while True:
            url = f"https://dev.azure.com/{organization}/{project}/_apis/git/repositories/{repo_ids[repo][0]}/pullRequests?searchCriteria.status=completed&$top=1000&$skip={skip}&api-version=7.1"
            response = requests.get(url, auth=HTTPBasicAuth('', ado_pat), headers=headers)
            if response.status_code == 200:
                data = response.json()
                prs_ado += data['count']

                if data['count'] < 1000:
                    break
                else:
                    skip += 1000
            else:
                print(f"Failed to fetch data for repo {repo}. Status code: {response.status_code}")
                break
        ado_pr_list.append({'repo_name': repo, 'prs_ado': prs_ado})
    comparison_results = []

    ado_dict = {item['repo_name']: item['prs_ado'] for item in ado_pr_list}

    for gh_item in gh_pr_list:
        repo_name = gh_item['repo_name']
        prs_gh = gh_item['prs_gh']
        prs_ado = ado_dict.get(repo_name, None)
        if prs_ado is not None:
            comparison_results.append({
                'repo_name': repo_name,
                'prs_gh': prs_gh,
                'prs_ado': prs_ado,
                'match': prs_gh == prs_ado
            })


    df = pd.DataFrame(comparison_results)
    print(tabulate(df, headers='keys', tablefmt='grid'))

compare_prs()


def compare_prs():
    print("comparing total number of pull requests for the migrated repos")
    for repo in comparision:
        if comparision[repo]["branches_gh"] == "not migrated":
            pass
        else:
            prs_ado = subprocess.run(["az", "repos", "pr", "list", "--organization", f"https://dev.azure.com/{organization}", "--project", f"{project}",  "--repository", f"{repo}", "--status", "completed", "--top", "1000000", "|", "grep", "artifactId", "|", "wc", "-l"], shell=True, capture_output=True, text=True)
            prs_gh = subprocess.run(["gh", "pr", "list", "--repo", f"{ghorg}/{prefix}{repo}", "-s", "closed", "-L", "100000", "|", "wc", "-l"], shell=True, capture_output=True, text=True)
            if json.loads(prs_gh.stdout) == json.loads(prs_ado.stdout):
                matched = True
            else:
                matched = False
            prs[repo]={"prs_ado":json.loads(prs_ado.stdout), "prs_gh":json.loads(prs_gh.stdout), "matched": matched}

    df = pd.DataFrame.from_dict(prs, orient='index')
    print(tabulate(df, headers='keys', tablefmt='grid'))
    print('pull requests comparision completed')
    print("+++++++++++++++++++++++++++++++++++++++")

# compare_prs()


def compare_pr_for_each_branch():
    print("comparing number of prs for each branch")
    repo_ado_branch = {}
    for repo in repos_gh:
        if repos_gh[repo] == "not migrated":
            pass
        else:
            branches = subprocess.run(["az", "repos", "ref", "list", "--org", f"https://dev.azure.com/{organization}", "--project", project, "--repository", repo, "--filter", "heads/" ], shell=True, capture_output=True, text=True)
            all_branches = json.loads(branches.stdout)
            for branch in all_branches:
                if repo not in repo_ado_branch:
                    repo_ado_branch[repo] = []
                repo_ado_branch[repo].append(branch["name"][11:])

    pr_match_all_branch = []
    for repo in repo_ado_branch:
        for branch in repo_ado_branch[repo]:
            prs_ado = subprocess.run(["az", "repos", "pr", "list", "--organization", f"https://dev.azure.com/{organization}", "--project", f"{project}",  "--repository", f"{repo}", "--status", "completed", "--top", "1000000", "--target-branch", branch, "|", "grep", "mergeCommitMessage", "|", "wc", "-l"], shell=True, capture_output=True, text=True)
            prs_gh = subprocess.run(["gh", "pr", "list", "--repo", f"{ghorg}/{prefix}{repo}", "-s", "closed", "--base", branch, "-L", "100000", "|", "wc", "-l"], shell=True, capture_output=True, text=True)
            if json.loads(prs_gh.stdout) == json.loads(prs_ado.stdout):
                matched = True
            else:
                matched = False
            pr_match_all_branch.append({repo:{branch:{"prs_ado": json.loads(prs_ado.stdout), "prs_gh": json.loads(prs_gh.stdout), "matched": matched}}})
          
    # print(pr_match_all_branch)
    normalized_data = []
    for item in pr_match_all_branch:
        for key, value in item.items():
            for sub_key, sub_value in value.items():
                flat_dict = {'repo': key, 'branch': sub_key}
                flat_dict.update(sub_value)
                normalized_data.append(flat_dict)

    df = pd.DataFrame(normalized_data)

# Print the DataFrame as a table
    print(tabulate(df, headers='keys', tablefmt='grid'))
    print('pull requests comparision for all branches completed')
    print("+++++++++++++++++++++++++++++++++++++++")


# compare_pr_for_each_branch()


def compare_commits():
    print("comparing the number of commits on the default branch for migrated repos")
    commit_count_ado = {}
    commits_count_gh = {}
    headers = {
        "content-type": "application/json"
    }

    for repo in repo_ids:
        url2 =  f"https://dev.azure.com/{organization}/{project}/_apis/git/repositories/{repo_ids[repo][0]}/commits?searchCriteria.$top=100000&&searchCriteria.itemVersion.version={repo_ids[repo][1]}&api-version=5.1"
        auth = HTTPBasicAuth("",ado_pat)
        response = requests.get(url=url2, auth=auth, headers=headers)
        if response.status_code == 200:
            output = response.json()
            commit_count_ado[repo] = output["count"]

    for repo in comparision:
        if comparision[repo]["branches_gh"] == "not migrated":
            pass
        else:
            command = f"gh api repos/{ghorg}/{prefix}{repo}/commits --paginate | grep -o '\"tree\"' | wc -l"
            commit_gh = subprocess.run(command, text=True, shell=True, capture_output=True)
            commits_count_gh[repo] = int(commit_gh.stdout.strip())
    
    for repo_gh in commits_count_gh:
        for repo_ado in commit_count_ado:
            if repo_ado == repo_gh:
                if commit_count_ado[repo_ado] == commits_count_gh[repo_gh]:
                    match = True
                else:
                    match = False
                commit_comparision[repo_ado]={'commits_ado':commit_count_ado[repo_ado], 'commits_gh':commits_count_gh[repo_gh], 'matched': match}

    df = pd.DataFrame.from_dict(commit_comparision, orient='index')
    print(tabulate(df, headers='keys', tablefmt='grid'))
    print("commits comparision completed")
    print("+++++++++++++++++++++++++++++++++++++++")

compare_commits()

# print("comparing unique commits of all repos...")

# # Function to clone a repository
# def clone_repo(repo_url, clone_path):
#     if os.path.exists(clone_path):
#         # shutil.rmtree(clone_path)
#         pass
#     subprocess.run(['git', 'clone', repo_url, clone_path], check=True)

# # Function to get commit count using git rev-list --all --count
# def get_commit_count(repo_path):
#     result = subprocess.run(['git', 'rev-list', '--all', '--count'], cwd=repo_path, capture_output=True, text=True, check=True)
#     return int(result.stdout.strip())

# # Main function to compare commit counts
# def compare_commit_counts():
#     commit_comparison = {}
    
#     for repo, details in comparision.items():
#         if details['matched'] in [True, False]:
#             gh_repo = f'{prefix}{repo}'
#             repo = repo.replace(' ', '%20')
#             ado_repo_url = f'https://{ado_pat}@dev.azure.com/{organization}/{project.replace(' ', '%20')}/_git/{repo}'
#             gh_repo_url = f'https://{gh_pat}@github.com/{ghorg}/{gh_repo}.git'

#             # Clone the repositories
#             ado_clone_path = f'./ado_{repo}'
#             gh_clone_path = f'./gh_{gh_repo}'
#             clone_repo(ado_repo_url, ado_clone_path)
#             clone_repo(gh_repo_url, gh_clone_path)

#             # Get commit counts
#             ado_commits = get_commit_count(ado_clone_path)
#             gh_commits = get_commit_count(gh_clone_path)

#             # Store the results in the dictionary
#             commit_comparison[repo] = {
#                 'ado_commits': ado_commits,
#                 'gh_commits': gh_commits,
#                 'matched': ado_commits == gh_commits
#             }

#     return commit_comparison

# # Run the comparison and print the results
# commit_comparison = compare_commit_counts()
# df = pd.DataFrame.from_dict(commit_comparison, orient='index')
# df.index.name = 'Repository'
# print(tabulate(df, headers='keys', tablefmt='grid'))

# # print("script execution completed")

# print("commit comparison script execution completed")
# print("+++++++++++++++++++++++++++++++++++++++")

# print("comparing repo size")


# matching_keys = [key for key, value in comparision.items() if value['matched'] is True]


# size = []
# for repo in matching_keys:
#     repo = repo.replace(' ', '%20')
#     # print(repo)
#     project = project.replace(' ', '%20')
#     # print(project)
#     azure_repo_url = f"https://dev.azure.com/{organization}/{project}/_git/{repo}"
#     github_repo_url = f"https://github.com/{ghorg}/{prefix}{repo}.git"
#     azure_pat = ado_pat
#     github_pat = gh_pat

#     def clone_repo(repo_url, clone_path, pat):
#         # if os.path.exists(clone_path):
#         #    shutil.rmtree(clone_path)  

#         repo_url_with_pat = repo_url.replace('https://', f'https://{pat}@')
#         result = subprocess.run(['git', 'clone', repo_url_with_pat, clone_path], capture_output=True, text=True)
#         if result.returncode == 0:
#             # print(f'Successfully cloned {repo_url}')
#             pass
#             # contents = os.listdir(clone_path)
#             # for item in contents:
#             #     print(item)
#         else:
#             # print(f'Error cloning {repo_url}: {result.stderr}')
#             pass

#     def get_repo_size(repo_path):
#         os.chdir(repo_path)
#         result = subprocess.run(['git', 'count-objects', '-vH'], capture_output=True, text=True)
#         # print(result)
#         size_line = [line for line in result.stdout.split('\n') if 'size-pack' in line]
#         if size_line:
#             size = size_line[0].split(':')[1].strip()
#             return size
#         return None

#     # Local paths.......
#     azure_clone_path = f'/tmp/azure{repo}'
#     github_clone_path = f'/tmp/github{repo}'

#     # Clone repo..........
#     clone_repo(azure_repo_url, azure_clone_path, azure_pat)
#     clone_repo(github_repo_url, github_clone_path, github_pat)

#     # Repo sizes.............
#     azure_repo_size = get_repo_size(azure_clone_path)
#     github_repo_size = get_repo_size(github_clone_path)

#     # print(f'Azure Repo Size of {repo} : {azure_repo_size}')
#     # print(f'GitHub Repo Size of {prefix}{repo}: {github_repo_size}')
#     size.append({repo: {"azure_repo": azure_repo_size, "github_repo_size": github_repo_size}})

# data = []
# for item in size:
#     for key, value in item.items():
#         data.append([key, value['azure_repo'], value['github_repo_size']])

# # Define the headers
# headers = ["Script Name", "Azure Repo Size", "GitHub Repo Size"]

# # Print the table with a box around it
# print(tabulate(data, headers, tablefmt="grid"))


# # Convert dictionaries to DataFrames
# comparison_df = pd.DataFrame.from_dict(comparision, orient='index')
# prs_df = pd.DataFrame.from_dict(prs, orient='index')
# commit_comparison_df = pd.DataFrame.from_dict(commit_comparison, orient='index')

# # Convert list of dictionaries to DataFrame
# size_data = []
# for item in size:
#     for repo, sizes in item.items():
#         sizes['Repository'] = repo
#         size_data.append(sizes)

# size_df = pd.DataFrame(size_data)

# # Define the absolute file path
# absolute_file_path = "D:/a/1/s/validate/comparison_data.xlsx"  # Change this to your desired path

# # Create a Pandas Excel writer using openpyxl as the engine
# with pd.ExcelWriter(absolute_file_path, engine='openpyxl') as writer:
#     # Write each DataFrame to a different sheet
#     comparison_df.to_excel(writer, sheet_name='Comparison')
#     prs_df.to_excel(writer, sheet_name='PRs')
#     commit_comparison_df.to_excel(writer, sheet_name='Commit Comparison')
#     size_df.to_excel(writer, sheet_name='Size')

# print(f"Excel file 'comparison_data.xlsx' has been created successfully at {absolute_file_path}.")


# Convert dictionaries to DataFrames
comparison_df = pd.DataFrame.from_dict(comparision, orient='index')
prs_df = pd.DataFrame.from_dict(prs, orient='index')
commit_comparison_df = pd.DataFrame.from_dict(commit_comparision, orient='index')

# Define the absolute file path
absolute_file_path = "D:/a/1/s/validate/comparison_data.xlsx"  # Change this to your desired path

# Create a Pandas Excel writer using openpyxl as the engine
with pd.ExcelWriter(absolute_file_path, engine='openpyxl') as writer:
    # Write each DataFrame to a different sheet
    comparison_df.to_excel(writer, sheet_name='Comparison')
    prs_df.to_excel(writer, sheet_name='PRs')
    commit_comparison_df.to_excel(writer, sheet_name='Commit Comparison')

print(f"Excel file 'comparison_data.xlsx' has been created successfully at {absolute_file_path}.")