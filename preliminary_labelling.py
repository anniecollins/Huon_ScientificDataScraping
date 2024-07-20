import pandas as pd
import numpy as np
import os

annotated_df = pd.read_csv(os.path.join("data", "annotated_scientific_data_articles.csv"))

# Filter out rows where issues are NA
print(f"Number of NA rows: {sum(annotated_df['issues_1'].isna())}")
annotated_df = annotated_df[~annotated_df['issues_1'].isna()]

# Add `llm_error_classification`
print(f"Number of rows with no issues: {sum(((annotated_df['issues_1'] == 'There are no problems.') | (annotated_df['issues_1'] == 'There are no problems')) & ((annotated_df['issues_2'] == 'There are no problems.') | (annotated_df['issues_2'] == 'There are no problems')) & ((annotated_df['issues_3'] == 'There are no problems.') | (annotated_df['issues_3'] == 'There are no problems')))}")
annotated_df["llm_error_classification"] = np.where(((annotated_df['issues_1'] == "There are no problems.") | (annotated_df['issues_1'] == "There are no problems")) &
             ((annotated_df['issues_2'] == "There are no problems.") | (annotated_df['issues_2'] == "There are no problems")) &
             ((annotated_df['issues_3'] == "There are no problems.") | (annotated_df['issues_3'] == "There are no problems")), 0, np.nan)

# Add `human_error_classification` (empty)
annotated_df["human_error_classification"] = np.nan

# Add `annotator` random sample
labellers = ["Annie", "Allyson", "Sarah"]
np.random.seed(10)
annotated_df['labeller'] = np.random.choice(labellers, size=len(annotated_df))

print(annotated_df['labeller'].value_counts())

# Save
annotated_df.drop(['Unnamed: 0', 'Unnamed: 0.1'], axis=1).to_csv(os.path.join("data", "annotated_labelled_scientific_data_articles.csv"), index=False)
