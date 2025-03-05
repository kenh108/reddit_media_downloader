import requests
import re
import logging
from urllib.parse import urlparse, urlunparse
import xml.etree.ElementTree as ET

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
            logging.debug(f"Expanded short link to: {expanded_url}")
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
    currently supports reddit hosted videos, reddit hosted gifs, and redgifs videos
    """
    logging.info(f"Processing Reddit URL: {url}")

    # expand mobile links
    url = expand_mobile_url(url) 
    if not url:
        logging.error("Failed to expand mobile link.")
        return None
    
    # validate reddit url
    if not re.match(r"https?://(www\.)?reddit\.com/(r|user)/.+/comments/.+", url):
        logging.error(f"Invalid Reddit URL format: {url}")
        return None

    # convert reddit url to json api endpoint
    api_url = clean_reddit_url(url)
    logging.debug(f"Fetching Reddit API: {api_url}")

    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(api_url, headers=headers)
        response.raise_for_status()
        data = response.json()

        # extract post data
        post_data = data[0]["data"]["children"][0]["data"]
        logging.debug(f"Extracted post info - Title: {post_data.get('title')}")

        # extract reddit hosted video
        if "media" in post_data and post_data["media"] and "reddit_video" in post_data["media"]:
            video_url = post_data["media"]["reddit_video"]["fallback_url"].split("?")[0] # Remove query params
            logging.info(f"Extracted Reddit video URL: {video_url}")

            dash_url = post_data["media"]["reddit_video"].get("dash_url") # DASH playlist url
            audio_url = extract_audio_from_dash(dash_url) if dash_url else None

            return {"type": "video", "video_url": video_url, "audio_url": audio_url}

        # extract reddit hosted gifs
        if "preview" in post_data and "images" in post_data["preview"]:
            variants = post_data["preview"]["images"][0].get("variants", {})
            if "gif" in variants:
                gif_url = variants["gif"]["source"]["url"]
                if ".gif" in gif_url:
                    logging.info(f"Extracted Reddit GIF URL: {gif_url}")
                    return {"type": "gif", "gif_url": gif_url}

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

def extract_redgifs_media(redgifs_url):
    """
    extracts highest quality video from redgifs with sound
    """
    logging.info(f"Extracting video from Redgifs: {redgifs_url}")

    # extract the redgif video id
    match = re.search(r"redgifs\.com/([\w-]+)/([\w-]+)", redgifs_url)
    if not match:
        logging.error(f"Invalid Redgifs URL format: {redgifs_url}")
        return None

    video_id = match.group(2)
    api_url = f"https://api.redgifs.com/v2/gifs/{video_id}"
    logging.debug(f"Fetching Redgifs API: {api_url}")

    # get redgifs authentication token
    token = get_redgifs_token()
    if not token:
        logging.error("Failed to obtain Redgifs authentication token.")
        return None

    try:
        headers = {
            "User-Agent": "Mozilla/5.0",
            "Authorization": f"Bearer {token}"
        }
        response = requests.get(api_url, headers=headers)
        response.raise_for_status()
        data = response.json()
        logging.debug(f"Redgifs API response: {str(data)}")

        # extract the highest quality video with sound
        if "gif" in data and "urls" in data["gif"]:
            video_url = data["gif"]["urls"].get("hd", data["gif"]["urls"].get("sd"))
            if video_url:
                logging.info(f"Extracted Redgifs video URL: {video_url}")
                return {"type": "video", "video_url": video_url, "audio_url": None} # Redgifs audio is included in mp4

    except requests.RequestException as e:
        logging.error(f"Redgifs API request failed: {e}")
    except (KeyError, IndexError) as e:
        logging.error(f"Parsing error in Redgifs API response: {e}")        

    return None

def get_redgifs_token():
    """
    fetches a temporary authentication token from redgifs
    """
    auth_url = "https://api.redgifs.com/v2/auth/temporary"

    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(auth_url, headers=headers)
        response.raise_for_status()
        token = response.json().get("token")

        if token:
            logging.info(f"Obtained Redgifs authentication token.")
            return token

    except requests.RequestException as e:
        logging.error(f"Redgifs authentication request failed: {e}")

    return None

def extract_audio_from_dash(dash_url):
    """
    Fetches the DASH manifest and extracts the highest quality audio file URL.
    """
    logging.info(f"Examining DASH manifest for Reddit video: {dash_url}")

    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(dash_url, headers=headers)
        response.raise_for_status()

        # Parse XML into ElementTree object and detect namespace dynamically
        root = ET.fromstring(response.text)
        namespace = root.tag.split("}")[0].strip("{") # Extract namespace from root element
        ns = {"mpd": namespace} if namespace else {}

        highest_bandwidth = 0
        best_audio_url = None

        # Find all <AdaptationSet> elements (which contain media tracks)
        for adaptation_set in root.findall(".//mpd:AdaptationSet", ns):
            content_type = adaptation_set.get("contentType", "")

            if "audio" in content_type:
                # Each <Representation> contains different quality of same audio
                for representation in adaptation_set.findall(".//mpd:Representation", ns):
                    bandwidth = int(representation.get("bandwidth", "0"))
                    base_url = representation.find("mpd:BaseURL", ns).text

                    if bandwidth > highest_bandwidth:
                        highest_bandwidth = bandwidth
                        best_audio_url = f"{dash_url.rsplit('/', 1)[0]}/{base_url}"

        if best_audio_url:
            logging.info(f"Extracted highest-bandwidth audio URL for Reddit video: {best_audio_url} ({highest_bandwidth} bps)")
            return best_audio_url
        else:
            logging.warning("No valid audio stream found in DASH manifest for Reddit video.")
            return None

    except requests.RequestException as e:
        logging.error(f"Failed to fetch DASH manifest: {e}")
    except ET.ParseError as e:
        logging.error(f"Failed to parse DASH XML: {e}")

    return None
