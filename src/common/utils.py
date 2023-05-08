import json
import requests
import subprocess


def save_json(json_obj, output_path):

    with open(output_path, "w") as file:
        json.dump(json_obj, file)


def save_text(text_obj, output_file_path):

    with open(output_file_path, "w") as file:
        file.write(text_obj)


def save_binary(data, output_path):

    with open(output_path, "wb") as file:
        file.write(data)


def read_json(input_file_path):

    with open(input_file_path, "r") as file:
        json_obj = json.load(file)

    return json_obj


def read_text(input_path):

    with open(input_path, "r") as file:
        text_obj = file.read()

    return text_obj


def download_binary(url, output_path, retries=5, **keys):

    while retries > 0:
        # try
        response = requests.get(url, **keys)
        retries -= 1

        if response.status_code == 200:
            break

    if response.status_code != 200:
        raise Exception()

    save_binary(response.content, output_path)

def create_directory_structure(directories) -> None:
    for directory in directories:
        if not directory.exists():
            directory.mkdir(parents=True)