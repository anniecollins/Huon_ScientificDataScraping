import pandas as pd
import os

articles = pd.read_csv(os.path.join("data", "scientific_data_articles.csv"))

# Conditions
# Needs to have a github link
# Needs to have only one github link maybe

github_articles = articles[(articles['codeLink'].str.contains("github.com", na=False)) & (~articles['codeLink'].str.contains(";", na=False))].reset_index()

