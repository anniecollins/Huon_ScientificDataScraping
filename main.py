from data_cleaning import github_articles
from fork_and_clone import *
from process_files import *

import pandas as pd

github_df = github_articles
def main(github_df, base_dir="client_projects"):

    # Storage for LLM output
    error_comments_df = pd.DataFrame()

    # for i in github_df.index
    # TEST
    # Store metadata about article
    doi = github_df['doi'].iloc[-2]
    url = github_df['codeLink'].iloc[-2]

    # Identify if the repo contains Py files
    original_owner, repo_name = extract_owner_and_repo(url)

    if identify_if_py(original_owner, repo_name):
        clone_url = fork_repo(original_owner, repo_name)
        print(clone_url)
        clone_repo(clone_url)
        print(clone_url)
    else:
        print(f"{original_owner}/{repo_name} does not contain a .py file")

    py_files = get_python_files(repo_name, base_dir)

    this_repo_df = pd.DataFrame()
    for file in py_files:
        this_file_df = pd.DataFrame()

        # Submit to OpenAI and get response
        issue_summary = process_file(file)

        this_file_df['doi'] = [doi]
        this_file_df['issues_1'] = [issue_summary[0]]
        this_file_df['issues_2'] = [issue_summary[1]]
        this_file_df['issues_3'] = [issue_summary[2]]

        this_repo_df = pd.concat([this_repo_df, this_file_df], axis=0)

    error_comments_df = pd.concat([error_comments_df, this_repo_df], axis=1)

    error_comments_df.set_index("doi", inplace=True)

    # Now join the original df with error comments
    annotated_df = github_df.join(error_comments_df, on = "doi", how="left")

    return annotated_df

annotated_df.to_csv(os.path.join("data", "annotated_scientific_data_articles.csv"))
