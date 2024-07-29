import pandas as pd
import os
import numpy as np
from tqdm import tqdm
import time
from ast import literal_eval

# Identify if py
from fork_and_clone import identify_filetypes, extract_owner_and_repo

articles = pd.read_csv(os.path.join("data", "nature_articles.csv"))

# Conditions 1
# Needs to have a github link
# Needs to have only one github link maybe
# articles = articles[(articles['codeLink'].str.contains("github.com", na=False)) & (~articles['codeLink'].str.contains(";", na=False))].reset_index()

# Add column indicating if there's a GitHub
articles['hasGithub'] = np.where(articles['codeLink'].str.contains("github", na=False), True, False)

# Conditions 2
# Needs to have some link text
# `codeLink` needs to be iterable with each entry as a URL
# Published in 2023
articles["codeLink"] = articles["codeLink"].str.split("; ")
articles = articles[(articles['pubYear']==2023)]

# Add column identifying if there is a code link
articles['hasCodeLink'] = np.where(articles['codeLink'].isna(), False, True)

# What are the top journals in the results?
# Top journals with code links are: Nature Communications, Scientific Reports, Scientific Data, and Communications Biology (same top 4 for GitHub specifically)
articles.value_counts(["journalName", "journalId", 'hasGithub']).head(10)

# Restrict to just ones with GitHub links
github_articles = articles[articles['hasGithub']==True].reset_index(drop=True)

# Read in existing df that has some filetype classifications
github_articles = pd.read_csv(os.path.join("data", "articles_with_github_filetypes.csv"))
github_articles.codeLink = github_articles.codeLink.apply(literal_eval)

todo_index = github_articles[github_articles['containsR'].isna()].index

scientific_reports_df = articles[(articles['journalId']==41598) & (articles['hasGithub']==True)].reset_index(drop=True)

# TEMP
# todo_index = github_articles.index

for i in tqdm(todo_index):
    # initialize flags
    contains_py = False
    contains_r = False

    # Loop through each provided code link
    for url in github_articles.loc[i]['codeLink']:

        # Modify URL for weird structuring
        url = url.replace("http:", "https:").replace("//www.", "//").replace(".git", "")

        # Identify if the repo contains Py files, or skip entirely if not properly formatted
        try:
            original_owner, repo_name = extract_owner_and_repo(url)
        except:
            print(f"Invalid URL or does not contain .py file: {url}")
            continue

        try:
            this_one_py, this_one_r = identify_filetypes(original_owner, repo_name)
        except:
            print(f"Issue with fetching repo info: {original_owner}/{repo_name}")
            this_one_py, this_one_r = False, False

        # update outer variable
        if this_one_py:
            contains_py  = True
        if this_one_r:
            contains_r = True

    # Add flags for Python and R contents
    github_articles.loc[i, "containsPy"] = contains_py
    github_articles.loc[i, "containsR"] = contains_r

    # Save every 50 entries
    if i % 50 == 0:
        github_articles.to_csv(os.path.join("data", "articles_with_github_filetypes.csv"))
        print(f"Saved up to {i}")

    # Sleep to make processing take longer
    time.sleep(3)

# Save files
github_articles.to_csv(os.path.join("data", "articles_with_github_filetypes.csv"))

