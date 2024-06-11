from data_cleaning import articles
from fork_and_clone import *
from process_files import *
from tqdm import tqdm
import pandas as pd
import shutil

def main(github_df, base_dir="client_projects", start=0, end=None, annotated_file=os.path.join("data", "annotated_scientific_data_articles.csv"), invalid_file=os.path.join("data", "invalid_scientific_data_articles.csv")):

    # Read in existing annotated file
    annotated_df = pd.read_csv(annotated_file)

    # Separate articles that have already been assessed and those to be submitted
    done_articles = annotated_df[~annotated_df['issues_1'].isna()] # Where issue_1 is not empty
    todo_articles = annotated_df[annotated_df['issues_1'].isna()]["doi"] # Where issue_1 is empty

    # Remove articles that have been completed from `github_df`; reset index so index start and end parameters work as intended
    github_df = github_df[github_df['doi'].isin(todo_articles)].reset_index(drop=True)

    # Storage for LLM output
    error_comments_df = pd.DataFrame()

    invalid_urls = pd.read_csv(invalid_file)

    if end == None:
        end = len(github_df)

    # Loop through articles
    for i in tqdm(github_df.index[start:end]):

        # Store metadata about article
        doi = github_df['doi'].loc[i]

        # Initialize article df
        # article_df = pd.DataFrame()

        # Keep track of number of valid URLs
        valid = 0

        # Loop throught URLs associated with article
        for url in github_df.loc[i]['codeLink']:

            # Modify URL for weird structuring
            url = url.replace("http:", "https:").replace("//www.", "//").replace(".git", "")

            # Identify if the repo contains Py files, or skip entirely if not properly formatted
            try:
                original_owner, repo_name = extract_owner_and_repo(url)
            except:
                print(f"Invalid URL or does not contain .py file: {url}")
                invalid_urls = pd.concat([invalid_urls, github_df.loc[i]])
                continue

            if identify_if_py(original_owner, repo_name) and get_repo_size(original_owner, repo_name) < 500000:
                clone_url = fork_repo(original_owner, repo_name)
                clone_repo(clone_url)
                delete_fork(repo_name)

                valid += 1
            else:
                print(f"{original_owner}/{repo_name} does not contain a .py file OR is too large")
                continue

            py_files = get_python_files(repo_name, base_dir)

            repo_df = pd.DataFrame()
            for file in py_files:
                file_df = pd.DataFrame()

                # Submit to OpenAI and get response
                try:
                    issue_summary = process_file(file)
                except:
                    print("Could not process ", file)
                    continue

                file_df['doi'] = [doi]
                file_df['fileName'] = [file]
                file_df['issues_1'] = [issue_summary[0]]
                file_df['issues_2'] = [issue_summary[1]]
                file_df['issues_3'] = [issue_summary[2]]

                repo_df = pd.concat([repo_df, file_df], axis=0)

                # Remove cloned directory
            shutil.rmtree(f"client_projects/{repo_name}")
            print(f"Deleted client_projects/{repo_name}")
            # article_df = pd.concat([article_df, repo_df], axis=0) # TODO: Something wrong here

        # Only save if there has been a valid URL
        if valid > 0:
            error_comments_df = pd.concat([error_comments_df, repo_df], axis=0)
            print(error_comments_df)

            print("Saving")
            error_comments_df.set_index("doi", inplace=True)

            # Now join the original df with error comments and concat with done articles
            annotated_df = github_df.join(error_comments_df, on="doi", how="left")

            pd.concat([done_articles, annotated_df], axis=0).to_csv(annotated_file, index=False)

            print(f"Saved annotated file, length = {len(github_df.join(error_comments_df, on='doi', how='left'))} \n\n\n\n")

            invalid_urls.to_csv(invalid_file, index=False)
            print("Saved invalid URL file\n\n\n\n")

            error_comments_df.reset_index(drop=False, inplace=True)

            # Remove clone directory
            # shutil.rmtree(f"client_projects/{repo_name}")

    error_comments_df.set_index("doi", inplace=True)

    print(file_df)
    print(repo_df)
    # print(article_df)
    print(error_comments_df)
    # Now join the original df with error comments
    annotated_df = github_df.join(error_comments_df, on = "doi", how="left")
    full_annotated_df = pd.concat([done_articles, annotated_df], axis=0)

    return full_annotated_df, invalid_urls


if __name__=="__main__":
    annotated_df, invalid_urls = main(articles.sort_values("pubDate", ascending=False))
    print(f"Length final df = {len(annotated_df)}")
    # annotated_df.to_csv(os.path.join("data", "annotated_scientific_data_articles.csv"))
    # invalid_urls.to_csv(os.path.join("data", "invalid_scientific_data_articles.csv"))
