import json
import os
import yaml
from bs4 import BeautifulSoup

# function to save a file
def save_file(file_name, content):
    # Create a new directory if necessary
    directory = os.path.dirname(file_name)
    if not os.path.exists(directory):
        os.makedirs(directory)
    # Save the file
    with open(file_name, 'w') as f:
        f.write(content)

# function to load a file
def load_file(file_name):
    with open(file_name, 'r') as f:
        return f.read()
    
def load_html(url,content_only=False):
    html_text = load_file(url)
    html_soup = BeautifulSoup(html_text, 'html.parser')
    if content_only:
        html_soup = html_soup.find('div',{'id':'content'})
        html_text = html_soup.prettify()
    return html_text, html_soup

# Get all files within a directory
def get_all_files(directory, file_type=None):
    root, dirs, files = list(os.walk(directory))[0]
    if file_type:
        return sorted([file for file in files if file.endswith(file_type)])
    else:
        return sorted(files)
    
def get_all_files_recursive(directory, file_type = None):
    return sorted([os.path.join(root, file) for root, dirs, files in os.walk(directory) for file in files if not file_type or file.endswith(file_type)])

# Get all folders within a directory
def get_all_folders(directory):
    root, dirs, files = list(os.walk(directory))[0]
    return dirs

def get_all_folders_recursive(directory, folder_endswith=None):
    return sorted([os.path.join(root, dir_) for root, dirs, files in os.walk(directory) for dir_ in dirs if not folder_endswith or dir_.endswith(folder_endswith)])

    
# Check if a file exists
def file_exists(file_name):
    return os.path.isfile(file_name)

# Check if a folder exists
def folder_exists(folder_name):
    return os.path.isdir(folder_name)

# Get the file extension
def get_file_extension(file_name):
    return os.path.splitext(file_name)[1]

# Get the file name without the extension
def get_file_name(file_name):
    return os.path.splitext(file_name)[0]

# Make directory
def make_directory(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)


def load_yaml(file_path):
    with open(file_path, 'r') as file:
        config = yaml.safe_load(file)
    return config

def save_yaml(file_path, config):
    with open(file_path, 'w') as file:
        yaml.dump(config, file, default_flow_style=False)

def load_json(file_path):
    with open(file_path, 'r') as file:
        data = json.load(file)
    return data

def save_json(file_path, data):
    with open(file_path, 'w') as file:
        json.dump(data, file)
        
        