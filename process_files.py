import os
import csv
import openai
from openai import OpenAI
import os
import time
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()  # This will automatically look for an .env file and load the variables

load_dotenv()
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
if not OPENAI_API_KEY:
    raise ValueError("OpenAI API key not found in the environment variables.")
openai.api_key = OPENAI_API_KEY

# # Load OpenAI API Key
client = OpenAI()

# Read the contents of a file at a specified file path and return it as a string
def read_file(file_path):
    with file_path.open('r') as f:
        return f.read()

# Read the contents of a file at a specified file path and splits them into a list using '---' as the delimiter
# def load_file_into_list(file_path):
#     content = read_file(file_path)
#     return content.split('---')

# Get the total number of tokens used from an API response
def calculate_tokens_used(response):
    return response.usage.total_tokens

# Gets the file extension from a file name and returns the corresponding file type
def get_file_type(file_name):
    ext = file_name.suffix
    return {
        '.py': 'Python',
    }.get(ext, 'Unknown')

def get_python_files(path, base_dir="client_projects"):
    all_files_list = []
    for path, subdirs, files in os.walk(os.path.join(base_dir, path)):
        all_files_list = all_files_list + [os.path.join(path, name) for name in files if ".git" not in path]

    py_files = [file for file in all_files_list if file[-3:] == ".py"]

    return py_files


def process_file(path_to_file_to_modify, model="gpt-4o", max_tokens=1024, delay_between_requests=5, temperature=1):

    path_to_file_to_modify = Path(path_to_file_to_modify)

    # Script contents
    content_of_interest = read_file(path_to_file_to_modify)
    file_type = get_file_type(path_to_file_to_modify)

    # Prompt the model to generate a list of suggestions
    if file_type == 'Unknown':
        print(f"Unsupported file type for {path_to_file_to_modify}.")
        return

    # Construct instructions prompt
    instructions = f"### INSTRUCTIONS ###\nGiven the following Python script, are there any issues with the code that would impact the quality/viability of its outputs? Consider things like overwriting filenames, duplicating work unintentionally, including entries that should be excluded, or other possibilities. Please do not include potential improvements that could be made, only actual problems that would occur regardless of external files or inputs. Do not include any Python code in the output. If there are no problems, say \"there are no problems\"."

    print(f"Submitting to API")
    # Prompt is instructions plus content of file
    instructions_prompt = f"{instructions.strip()}\n\n\`\`\`python\n{content_of_interest}\n\`\`\`"

    # all_instructions_responses = []
    total_instructions_tokens_used = 0

    try:
        instructions_response = client.chat.completions.create(model=model,
        messages=[{"role": "user", "content": instructions_prompt}],
        temperature=temperature,
        max_tokens=max_tokens,
        n=3)

        print(f"Token count of the prompt: {len(instructions_prompt)}")

        print(f"API Response: {instructions_response}")

        tokens_used = calculate_tokens_used(instructions_response)
        total_instructions_tokens_used += tokens_used

        print(f"Processing instructions prompt, Tokens used: {tokens_used}")

        return [instructions_response.choices[i].message.content for i in range(len(instructions_response.choices))]

    except openai.OpenAIError as e:
        print(f"API Error: {str(e)}")

if __name__ == "__main__":

    base_dir = "client_projects"
    path = "times_to_hospitals_AU"
    py_files = get_python_files(path)

    # Test
    issue_summary = process_file(py_files[0])
