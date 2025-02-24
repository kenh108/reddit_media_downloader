import os
import requests
import logging
from urllib.parse import urlparse

MEDIA_FOLDER = os.path.abspath("static/media")
os.makedirs(MEDIA_FOLDER, exist_ok=True)

def download_media(media_url):
    """
    Downloads the media file and saves it locally.
    Returns the filename if successful, otherwise None.
    """
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(media_url, headers=headers, stream=True)
        response.raise_for_status()

        # Extract filename from URL
        parsed_url = urlparse(media_url)
        filename = os.path.basename(parsed_url.path).split("?")[0]

        local_path = os.path.join(MEDIA_FOLDER, filename)

        if os.path.exists(local_path):
            logging.info(f"File already exists: {local_path}")
            return filename

        logging.info(f"Downloading media: {media_url} -> {local_path}")

        # Write in chunks to reduce RAM used
        with open(local_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        return filename

    except requests.RequestException as e:
        logging.error(f"Failed to download media: {e}")
        return None
