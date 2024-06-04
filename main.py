from data_cleaning import github_articles
from fork_and_clone import *
from process_files import *
from tqdm import tqdm
import pandas as pd
import shutil

def main(github_df, base_dir="client_projects"):

    # Storage for LLM output
    error_comments_df = pd.DataFrame()

    # Loop through articles
    for i in tqdm(github_df.index[:10]):

        # Store metadata about article
        doi = github_df['doi'].loc[i]
        url = github_df['codeLink'].loc[i].replace("http:", "https:").replace("//www.", "//").replace(".git", "")

        # Identify if the repo contains Py files
        original_owner, repo_name = extract_owner_and_repo(url)

        if identify_if_py(original_owner, repo_name):
            clone_url = fork_repo(original_owner, repo_name)
            clone_repo(clone_url)
            delete_fork(repo_name)
        else:
            print(f"{original_owner}/{repo_name} does not contain a .py file")
            continue

        py_files = get_python_files(repo_name, base_dir)

        this_repo_df = pd.DataFrame()
        for file in py_files:
            this_file_df = pd.DataFrame()

            # Submit to OpenAI and get response
            try:
                issue_summary = process_file(file)
            except:
                print("Could not process ", file)
                continue

            this_file_df['doi'] = [doi]
            this_file_df['fileName'] = [file]
            this_file_df['issues_1'] = [issue_summary[0]]
            this_file_df['issues_2'] = [issue_summary[1]]
            this_file_df['issues_3'] = [issue_summary[2]]

            this_repo_df = pd.concat([this_repo_df, this_file_df], axis=0)


        error_comments_df = pd.concat([error_comments_df, this_repo_df], axis=0)

        error_comments_df.set_index("doi", inplace=True)

        # Now join the original df with error comments
        github_df.join(error_comments_df, on="doi", how="left").to_csv(os.path.join("data", "annotated_scientific_data_articles.csv"))
        print("Saved annotated file\n\n\n\n")

        error_comments_df['doi'] = doi

        # Remove clone directory
        shutil.rmtree(f"client_projects/{repo_name}")

    error_comments_df.set_index("doi", inplace=True)

    # Now join the original df with error comments
    annotated_df = github_df.join(error_comments_df, on = "doi", how="left")

    return annotated_df


if __name__=="__main__":
    annotated_df = main(github_articles.sort_values("pubDate", ascending=False))
    annotated_df.to_csv(os.path.join("data", "annotated_scientific_data_articles.csv"))
