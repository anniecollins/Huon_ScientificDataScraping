import pandas as pd
import os

nature_comms = pd.read_csv(os.path.join("data", "annotated_nature_communications_articles.csv"))

nature_comms[(nature_comms['issues_1']=="There are no problems.") & (nature_comms['issues_2']=="There are no problems.") & (nature_comms['issues_3']=="There are no problems.")]

# How many articles and how many scripts?
print(f"Number of articles assessed: {len(nature_comms[~nature_comms['issues_1'].isna()]['doi'].unique())}")
print(f"Number of scripts assessed: {len(nature_comms[~nature_comms['issues_1'].isna()])}")
print(f"Number with NO problems: {len(nature_comms[(nature_comms['issues_1']=='There are no problems.') & (nature_comms['issues_2']=='There are no problems.') & (nature_comms['issues_3']=='There are no problems.')])}")
print(f"Number with problems: {len(nature_comms[~nature_comms['issues_1'].isna()]) - len(nature_comms[(nature_comms['issues_1']=='There are no problems.') & (nature_comms['issues_2']=='There are no problems.') & (nature_comms['issues_3']=='There are no problems.')])}")
