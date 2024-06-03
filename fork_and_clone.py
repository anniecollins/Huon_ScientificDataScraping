import requests
import os
import time
import git
from git import GitCommandError
import re
from dotenv import load_dotenv

load_dotenv()

# Retrieve the GitHub PAT from environment variables
GITHUB_PAT = os.getenv('GITHUB_PAT')
# Check if the token is loaded correctly
if not GITHUB_PAT:
    raise ValueError("GitHub Personal Access Token (GITHUB_PAT) not found. Make sure it is set in the .env file.")


def extract_owner_and_repo(url, valid_extensions=[".py"]):
    """
    Extract the owner and repo name from a GitHub URL.

    Args:
        url (str): The URL of the file on GitHub.
        valid_extensions (list): List of valid file extensions.

    Returns:
        tuple: A tuple containing the original owner and repo name.
    """

    # Create a regular expression pattern to match the URL of the repo on GitHub
    pattern = re.compile(fr'https://github\.com/([^/]+)/([^/]+)')

    # Match the URL with the regular expression pattern
    match = pattern.match(url)
    if not match:
        raise ValueError(f"Invalid URL or not one of the following file types: {', '.join(valid_extensions)}")

    # Extract the owner and repository name from the matched URL
    original_owner, repo_name = match.groups()

    return original_owner, repo_name

def identify_if_py(original_owner, repo_name):

    headers = {
        "Authorization": f"token {GITHUB_PAT}",
        "Accept": "application/vnd.github.v3+json"
    }

    master = requests.get('https://api.github.com/repos/' + original_owner + '/' + repo_name + '/branches/master', headers = headers)
    master = master.json()
    head_tree_sha = master['commit']['commit']['tree']['sha']

    tree = requests.get('https://api.github.com/repos/' + original_owner + '/' + repo_name + '/git/trees/' + head_tree_sha + "?recursive=1", headers = headers)
    tree = tree.json()

    for file in tree['tree']:
        if file['path'][-3:] == ".py":
            return True

    return False

def fork_repo(original_owner, repo_name):
    url = f"https://api.github.com/repos/{original_owner}/{repo_name}/forks"
    headers = {
        "Authorization": f"token {GITHUB_PAT}",
        "Accept": "application/vnd.github.v3+json"
    }
    response = requests.post(url, headers=headers, json={"user": "anniecollins"})

    if response.status_code == 202:
        print(f"Forked {original_owner}/{repo_name} successfully!")
        time.sleep(10)  # Wait for the fork to be created
        return response.json().get('clone_url')
    else:
        print(f"Failed to fork the repository. Status Code: {response.status_code}. Message: {response.text}")
        return None


def clone_repo(clone_url):
    print(f"Attempting to clone")
    print(f"Using PAT: {GITHUB_PAT[:4]}...")
    if clone_url:
        repo_folder_name = clone_url.split("/")[-1].replace(".git", "")
        target_directory = f'./client_projects/{repo_folder_name}'
        print(f"Checking directory: {target_directory}")
        if os.path.isdir(target_directory):
            print(f"Directory '{target_directory}' already exists. Skipping clone.")
        else:
            os.makedirs(target_directory, exist_ok=True)
            # Include PAT in the clone URL
            pat_clone_url = clone_url.replace("https://", f"https://{os.getenv('GITHUB_PAT')}@")
            try:
                git.Repo.clone_from(pat_clone_url, target_directory)
                print(f"Cloned repository from {clone_url} to {target_directory} successfully!")
            except GitCommandError as e:
                print(f"Failed to clone the repository. Error: {e}")
    else:
        print("Failed to clone the repository.")


if __name__ == "__main__":
    url = 'https://github.com/sebbarb/times_to_hospitals_AU'

    original_owner, repo_name = extract_owner_and_repo(url)

    if identify_if_py(original_owner, repo_name):
        clone_url = fork_repo(original_owner, repo_name)
        print(clone_url)
        clone_repo(clone_url)
        print(clone_url)
    else:
        print(f"{original_owner}/{repo_name} does not contain a .py file")
