import requests
import re
import logging
import sys
from urllib.parse import urlparse, urlunparse

logging.basicConfig(
    level=logging.DEBUG, # change to logging.INFO in production
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stderr) # logs to standard error
    ]
)

def expand_mobile_url(url):
    """
    if the url is a mobile reddit short link ("/s/"), follow redirect to
    retrieve the full reddit post url
    """
    if "/s/" in url:
        logging.debug(f"detected mobile short link: {url}")
        try:
            headers = {"User-Agent": "Mozilla/5.0"}
            response = requests.head(url, headers=headers, allow_redirects=True)
            expanded_url = response.url
            logging.info(f"expanded short link to: {expanded_url}")
            return expanded_url
        except requests.RequestException as e:
            logging.error(f"failed to expand short link {url}: {e}")
            return None

    logging.debug(f"url is not a short link: {url}")
    return url # return original if its not a short link

def clean_reddit_url(url):
    """
    removes query parameters from reddit post url before appending '.json'
    """
    parsed_url = urlparse(url)
    clean_path = parsed_url.path # extract the path without query parameters
    clean_url = urlunparse((parsed_url.scheme, parsed_url.netloc, clean_path, "", "", ""))

    clean_json_url = clean_url + ".json"
    logging.debug(f"cleaned reddit url: {clean_json_url}")

    return clean_url + ".json"

def fetch_reddit_media(url):
    """
    extracts video from reddit link
    """
    # expand mobile links
    url = expand_mobile_url(url) 
    if not url:
        return None
    
    # validate reddit url
    if not re.match(r"https?://(www\.)?reddit\.com/r/.+/comments/.+", url):
        print(url)
        return None

    # convert reddit url to json api endpoint
    api_url = clean_reddit_url(url)


    return None

def extract_redgif_media(redgif_url):
    """
    extracts highest quality video from redgifs with sound
    """

    return redgif_url
