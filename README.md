# Identification of Errors in Python Code using LLMs

This repository contains a set of scripts and tools to automate the process of scraping metadata for articles from academic journals (currently *Nature Scientific Data*), checking if the articles are associated with GitHub repositories that contain Python scripts, and checking these scripts for errors using a Large Language Model (LLM).

## Requirements/Set Up
Create a `.env` file that contains the following variables:
- `NATURE_API_KEY`: API key for the [Springer Nature API](https://dev.springernature.com/).
- `GITHUB_PAT`: A Personal Access Token (PAT) associated with your personal or organization GitHub account. PAT must have `repo` and `delete_repo` scopes selected.
- `OPENAI_API_KEY`: API key for the [OpenAI API](https://platform.openai.com/docs/overview).

## Usage

### `scrape_nature.py`: Scrape metadata and code links

This script uses the Springer Nature API to extract metadata and article text from all open access *Nature Scientific Data* articles containing the term "python" (in any searchable field, case-insensitive) using the open access API endpoint. It outputs the file `data/scientific_data_articles.csv` which contains the following fields:

| Column Name      | Data Type | Description                                                                                                                                                                             | Example Value   |
|------------------|-----------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-----------------|
| `journalName`       | `STRING`  | Name of specific Nature journal.                                                                                                                                                        | "Scientific Data" | 
| `journalId`       | `INT`     | Numeric journal ID. Journal IDs can be found at https://metadata.springernature.com/metadata/kbart (see Complete Nature.com and Complete Springer Journals to get lists of JournalIDs). | 41597           |        
| `doi`       | `STRING`  | Article DOI. DOIs are used as unique row IDs for this dataset.                                                                                                                          | 10.1038/s41597-024-03158-7     |           
| `title`       | `STRING`  | Journal article title.                                                                                                                                                                  | "Mapping Road Surface Type of Kenya Using OpenStreetMap and High-resolution Google Satellite Imagery"     |                     
| `pubDay`       | `INT`     | Day of publication.                                                                                                                                                                     | 3               |                     
| `pubMonth`       | `INT`     | Month number of publication.                                                                                                                                                            | 4               |                     
| `pubYear`       | `INT`     | Year of publication.                                                                                                                                                                    | 2024            |                     
| `codeLink`       | `STR`     | URLs extracted from the code availability section of the article. In the case of multiple URLs, distinct URLs are separated by "; ".                                                    | https://github.com/Dsayddd/RoadSurface     |                     
| `codeText`       | `STRING`  | Text included in the article's code availability statement with the URLs removed.                                                                                                       | "The data files and the python scripts used for model training are available online through GitHub repository: "     |                     
| `pubDate`       | `DATE`    | Full online publication date (created from `pubDay`, `pubMonth`, and `pubYear`.                                                                                                         | 2024-04-03      |                     

### `data_cleaning.py`: Set up data for assessment

This script imports the saved *Scientific Data* metadata and applies minor filtering a cleaning steps to set it up for the remainder of the pipeline.

### `fork_and_clone.py`: Assess validity of repo and get contents locally

This script contains functions for assessing whether an article's code link(s) is/are valid and whether the repository contains scripts that should be submitted to the LLM. An article's link is valid if it is of the structure "https://github.com/USER/REPO_NAME" and does not return a 404 error (i.e. refers to a specific, entire, and publicly accessible GitHub repo). The content is valid if it contains at least one .py file and the entire repository size is under 500 MB. 

### `process_files.py`: Submit scripts to LLM for assessment

This script contains functions for identifying all Python files in the local clone of a repository and submitting them to the LLM for error identification. Only prompts totally under 128,000 tokens are submitted, since this is the context window for GPT-4o. The model temperature is set to 1 and three responses are returned for each prompt.

The LLM prompt is:

>  ### INSTRUCTIONS ###
> 
> Given the following Python script, are there any issues with the code that would impact the quality/viability of its outputs? Consider things like overwriting filenames, duplicating work unintentionally, including entries that should be excluded, or other possibilities. Please do not include potential improvements that could be made, only actual problems that would occur regardless of external files or inputs. Do not include any Python code in the output. If there are no problems, say "there are no problems".
>
> \`\`\`python
> 
> SCRIPT CONTENTS
> 
> \`\`\`

### `main.py`: Run the full pipeline

This script imports functions from all other scripts, loops through each article, link, and file, and submits each valid file to the LLM. It then structures the LLM responses and joins them into the original metadata dataframe via article DOI. This process is set up to be cumulative, such that articles that have already been processed are not processed again. 

In the resulting dataset, `data/annotated_scientific_data_articles.csv`, each row represents one file in one repo associated with one article. The table has the following *additional* fields:

| Column Name | Data Type | Description                                                                                                                                               | Example Value                                        |
|-------------|-----------|-----------------------------------------------------------------------------------------------------------------------------------------------------------|------------------------------------------------------|
| `fileName`  | `STRING`  | Path to specific file within repository. All paths start with `client_projects` since this is the local folder where article repositories were cloned to. | "client_projects/AffectiveStimuliScraper/run_GUI.py" |
| `issues_1`  | `STRING`  | LLM output outlining errors identified in the script, or "There are no problems" if no problems were identified.                                          | *Too long to include*                                |
| `issues_2`  | `STRING`  | Same as above                                                                                                                                             |                                                      |
| `issues_3`  | `STRING`  | Same as above                                          |                                                      |

Also, in `annotated_scientific_data_articles.csv`, the column `codeLink` is formatted as a list where each entry is a unique link associated with the article in question.

## Contributing

For the time being, please push any edits to your own branch.

# Error Classification

The goals of this manual error classifications exercise are:
1. To identify scripts in published *Scientific Data* articles that contain errors.
2. To identify discrepancies between LLM error identification and human error identification related to Python code.

## Types of errors
- **(0)** - No errors

- **(1)** - Legitimate error

  - Off-by-one errors
  - Duplicate filenames causing overwriting
  - Indexing errors (i.e. missing last entry in a dataframe or list)
  - Incorrect join/merge behaviours, causing missing or duplicate data
  - Unintended in-place modification
  - Unaccessed portions of code
  - Flawed `if` or `while` statement logic

- **(2)** - Potential improvement

  - Lack of error handling
  - Lack of checking for file existence
  - Hardcoded filepaths
  - Assumption that files exist at a path, or that columns/indices exist in a file
  - Computational inefficiency
  - Typos that are consistent throughout, and therefore don't impact performance

## Error classification
There are two stages to manual error classification:

1. What type of error did the LLM identify?
   1. If all of `issues_1`, `issues_2`, and `issues_3` are "There are no problems", this counts as a no error classification (0). If there is at least one LLM reponse that indicates an issue, this counts as either a legitimate error (1) or potential improvement (2). 
   2. If there are any legitimate errors identified in any of the three responses, classify the LLM output as (1). If all the issues identified are potential improvements, classify the LLM output as (2).
2. What type of error is actually in the script?
   1. Identify if the error outlined in the LLM response(s) actually occur in the script or if they are incorrect assumptions, hallucinations, etc. If the LLM has identified a legitimate error, then assess if this error does exist in the script. If the LLM has identified an area of improvement, assess if this is something that would potentially improve the script, *and* if there are any legitimate errors that exists that were not identified.
   2. For the time being, **please focus only on scripts where an issue has been identified and skip scripts with the (0) no error LLM classification**.
3. To the best of your knowledge, would this error impact the data/conclusions as presented in the article?
   1. If there is a legitimate error in the script but it appears in a function that is not used or in a file that is not part of a core analysis pipeline, then it is possible that it does not impact the actual analysis.

