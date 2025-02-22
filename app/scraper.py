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
        logging.debug(f"Detected mobile short link: {url}")
        try:
            headers = {"User-Agent": "Mozilla/5.0"}
            response = requests.head(url, headers=headers, allow_redirects=True)
            expanded_url = response.url
            logging.info(f"Expanded short link to: {expanded_url}")
            return expanded_url
        except requests.RequestException as e:
            logging.error(f"Failed to expand short link {url}: {e}")
            return None

    logging.debug(f"URL is not a short link: {url}")
    return url # return original if its not a short link

def clean_reddit_url(url):
    """
    removes query parameters from reddit post url before appending '.json'
    """
    parsed_url = urlparse(url)
    clean_path = parsed_url.path # extract the path without query parameters
    clean_url = urlunparse((parsed_url.scheme, parsed_url.netloc, clean_path, "", "", ""))

    clean_json_url = clean_url + ".json"
    logging.debug(f"Cleaned Reddit URL: {clean_json_url}")

    return clean_url + ".json"

def fetch_reddit_media(url):
    """
    extracts media from reddit post url
    currently only supports videos
    """
    logging.info(f"Processing Reddit URL: {url}")

    # expand mobile links
    url = expand_mobile_url(url) 
    if not url:
        logging.error("Failed to expand mobile link.")
        return None
    
    # validate reddit url
    if not re.match(r"https?://(www\.)?reddit\.com/r/.+/comments/.+", url):
        logging.error(f"Invalid Reddit URL format: {url}")
        return None

    # convert reddit url to json api endpoint
    api_url = clean_reddit_url(url)
    logging.debug(f"Fetching Reddit API: {api_url}")

    try:
        # make request to reddit api
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(api_url, headers=headers)
        response.raise_for_status()
        data = response.json()

        # extract post data
        post_data = data[0]["data"]["children"][0]["data"]
        logging.debug(f"Extracted post info - Title: {post_data.get('title')}, Video: {post_data.get('media', {}).get('reddit_video', {}).get('fallback_url')}")

        if "media" in post_data and post_data["media"] is not None and "reddit_video" in post_data["media"]:
            video_url = post_data["media"]["reddit_video"]["fallback_url"]
            logging.info(f"Extracted Reddit video URL: {video_url}")

            # strip query parameters for a clean link
            parsed_video_url = urlparse(video_url)
            clean_video_url = f"{parsed_video_url.scheme}://{parsed_video_url.netloc}{parsed_video_url.path}"
            return {"type": "video", "url": clean_video_url}

        # check for redgif links in the post
        if "url_overridden_by_dest" in post_data:
            media_url = post_data["url_overridden_by_dest"]
            if "redgifs.com" in media_url:
                return extract_redgifs_media(media_url)

    except requests.RequestException as e:
        logging.error(f"Reddit API request failed: {e}")
    except (KeyError, IndexError) as e:
        logging.error(f"Parsing error in Reddit API response: {e}")        

    return None

def extract_redgif_media(redgif_url):
    """
    extracts highest quality video from redgifs with sound
    """

    return redgif_url
