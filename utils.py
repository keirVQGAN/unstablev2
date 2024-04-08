import json
import os
import logging
import requests

def ensure_dir_exists(path):
    os.makedirs(path, exist_ok=True)

def write_json_data(filename, data):
    with open(filename, 'w') as file:
        json.dump(data, file, indent=4)

def load_json_data(filename, default):
    try:
        with open(filename, 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        return default

def download_image(image_url, image_path):
    try:
        with requests.get(image_url) as response:
            response.raise_for_status()
            with open(image_path, 'wb') as file:
                file.write(response.content)
            logging.info(f"Downloaded image saved as {image_path}")
    except requests.RequestException as e:
        logging.error(f"Failed to download {image_url}: {e}")
