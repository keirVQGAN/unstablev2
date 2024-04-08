#@markdown `stable_diffusion_api.py`
from rich.console import Console
from IPython.display import Image, display
import requests
import logging
from datetime import datetime, timedelta
from itertools import product
import time
from response_processing import *

class StableDiffusionAPI:
    def __init__(self, api_key, json_path, base_url="https://modelslab.com/api/v6/realtime"):
        self.api_key = api_key
        self.base_url = base_url
        self.json_path = json_path
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    def generate_image(self, **kwargs):
        # Find parameters that are lists and those that are not
        list_params = {key: value for key, value in kwargs.items() if isinstance(value, list)}
        single_params = {key: value for key, value in kwargs.items() if not isinstance(value, list)}

        # Generate combinations of list parameters
        if list_params:
            keys, values = zip(*list_params.items())
            combinations = [dict(zip(keys, v)) for v in product(*values)]
        else:
            combinations = [{}]

        for combo in combinations:
            # Merge single_params and current combo of list_params
            params = {**single_params, **combo}
            # Actual API call
            self._generate_image_call(**params)
            # Wait for 2 seconds before the next call
            time.sleep(1)
            self.handle_pending_images()
            time.sleep(1)


    def _generate_image_call(self, prompt, **kwargs):
        endpoint = self._determine_endpoint(**kwargs)
        payload = self._prepare_payload(prompt, **kwargs)
        response = requests.post(f"{self.base_url}{endpoint}", json=payload, headers={'Content-Type': 'application/json'})

        if response.ok:
            response_data = response.json()
            response_data['processed_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            process_response(response_data, self.json_path)
        else:
            logging.error(f"Error generating image: {response.text}")


        self.display_response_info(response_data)

    def _determine_endpoint(self, **kwargs):
        """
        Determines the API endpoint based on the provided parameters, considering
        non-empty string values for init_image and mask_image.
        """
        has_init_image = 'init_image' in kwargs and kwargs['init_image']
        has_mask_image = 'mask_image' in kwargs and kwargs['mask_image']

        if has_init_image:
            return "/inpaint" if has_mask_image else "/img2img"
        return "/text2img"

    def _prepare_payload(self, prompt, **kwargs):
        """
        Prepares the API payload, excluding keys with None values or empty strings.
        """
        # Filter out keys with None values or empty strings
        filtered_kwargs = {k: v for k, v in kwargs.items() if v is not None and v != ''}
        return {"key": self.api_key, "prompt": prompt, **filtered_kwargs}

    def download_images_with_metadata(self):
        """
        Initiates the download of images and their metadata.
        """
        download_images_and_metadata(self.json_path)

    def handle_pending_images(self):
        """
        Processes any pending images.
        """
        process_pending_images(self.json_path, self.api_key)

    def display_response_info(self, response_data):
        """
        Displays information based on the response status.

        :param response_data: Dictionary containing the response data.
        """
        # Extract common data
        status = response_data.get("status")
        meta = response_data.get("meta")

        # Handle success status
        if status == "success":
            print("Status: Success")
            if "output" in response_data:
                for url in response_data["output"]:
                    print(f"Output URL: {url}")

        # Handle processing status
        elif status == "processing":
            eta_seconds = response_data.get("eta", 0)  # Default to 0 if not present
            future_time = datetime.now() + timedelta(seconds=eta_seconds)
            print(f"Status: Processing. Check back at {future_time.strftime('%Y-%m-%d %H:%M:%S')}")

        # Handle other statuses (failure, error, etc.)
        else:
            print("Response:")
            print(response_data)

        # Print meta data for all cases
        print("Meta Data:", meta)