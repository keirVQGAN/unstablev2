import requests
import logging
import json
import os
from datetime import datetime, timedelta
from utils import ensure_dir_exists, write_json_data, load_json_data, download_image

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def process_response(response_data, json_path):
    ensure_dir_exists(json_path)
    filename = f"{json_path}/{response_data['status']}_responses.json"

    responses_data = load_json_data(filename, [])
    if response_data not in responses_data:
        responses_data.append(response_data)
        write_json_data(filename, responses_data)
    else:
        logging.info("Duplicate entry detected, not adding to file.")

def download_images_and_metadata(json_path):
    responses_filename = f"{json_path}/success_responses.json"
    images_folder = f"{json_path}/images"
    ensure_dir_exists(images_folder)
    for entry in load_json_data(responses_filename, []):
        for index, image_url in enumerate(entry.get("output", []), start=1):
            image_path = f"{images_folder}/image_{entry['id']}_{index}.png"
            if not os.path.exists(image_path):
                download_image(image_url, image_path)
        metadata_filename = f"{images_folder}/metadata_{entry['id']}.json"
        write_json_data(metadata_filename, entry)

def process_pending_images(json_path, api_key):
    processing_filename = f"{json_path}/processing_responses.json"
    success_filename = f"{json_path}/success_responses.json"

    # Ensure the data structures loaded are lists.
    processing_data = load_json_data(processing_filename, [])
    success_data = load_json_data(success_filename, [])

    updated_processing_data = []

    for entry in processing_data:
        fetch_result_url = entry.get('fetch_result')
        if fetch_result_url:
            payload = json.dumps({"key": api_key})
            headers = {'Content-Type': 'application/json'}
            response = requests.post(fetch_result_url, headers=headers, data=payload)

            if response.status_code == 200:
                fetch_response = response.json()
                if fetch_response.get('status') == 'success':
                    logging.info(f"Successfully fetched processed image for entry ID: {entry['id']}")
                    # Ensure the combined entry excludes specified keys and add a timestamp.
                    combined_entry = {**entry, **fetch_response, 'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
                    combined_entry = {k: v for k, v in combined_entry.items() if k not in {"tip", "eta", "message", "future_links"}}
                    success_data.append(combined_entry)  # Correctly append the new data as an entry in the list.
                else:
                    updated_processing_data.append(entry)  # Retain in processing if not successful.
            else:
                logging.error(f"Error fetching processed image for entry ID: {entry['id']}: {response.text}")
                updated_processing_data.append(entry)  # Retain in processing due to error.
        else:
            logging.info("Missing 'fetch_result' URL, skipping entry.")
            updated_processing_data.append(entry)  # No URL, keep in processing list.

    # Correctly write the updated list back to the JSON files.
    write_json_data(processing_filename, updated_processing_data)
    write_json_data(success_filename, success_data)

