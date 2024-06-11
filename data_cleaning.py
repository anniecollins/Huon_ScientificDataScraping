import pandas as pd
import os

articles = pd.read_csv(os.path.join("data", "scientific_data_articles.csv"))

# Conditions 1
# Needs to have a github link
# Needs to have only one github link maybe
# articles = articles[(articles['codeLink'].str.contains("github.com", na=False)) & (~articles['codeLink'].str.contains(";", na=False))].reset_index()

# Conditions 2
# Needs to have some link text
# `codeLink` needs to be iterable with each entry as a URL
# Published in 2023
articles["codeLink"] = articles["codeLink"].str.split("; ")
articles = articles[(~articles["codeLink"].isna()) & (articles['pubYear']==2023)]
