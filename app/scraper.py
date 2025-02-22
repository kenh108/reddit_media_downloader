import requests
import re
import sys
from urllib.parse import urlparse, urlunparse

def expand_mobile_url(url):
    """
    if the url is a mobile reddit short link ("/s/"), follow redirect to
    retrieve the full reddit post url
    """
    if "/s/" in url:
        try:
            headers = {"User-Agent": "Mozilla/5.0"}
            response = requests.head(url, headers=headers, allow_redirects=True)
            expanded_url = response.url
            return expanded_url
        except requests.RequestException as e:
            return None

    return url # return original if its not a short link

def clean_reddit_url(url):
    """
    removes query parameters from reddit post url before appending '.json'
    """
    parsed_url = urlparse(url)
    clean_path = parsed_url.path # extract the path without query parameters
    clean_url = urlunparse((parsed_url.scheme, parsed_url.netloc, clean_path, "", "", ""))

    return clean_url + ".json"

def fetch_reddit_media(url):
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

    try:
        # fetch reddit post data
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(api_url, headers=headers)
        response.raise_for_status()
        data = response.json()

        # extract media url
        post_data = data[0]["data"]["children"][0]["data"]

        # check for reddit hosted video
        if "media" in post_data and post_data["media"] is not None and "reddit_video" in post_data["media"]:
            print("yes")
            video_url = post_data["media"]["reddit_video"]["fallback_url"]
            return {"type": "video", "url": video_url}

        # check for reddit gallery (multiple images)
        if "gallery_data" in post_data:
            images = []
            metadata = post_data["media_metadata"]
            for key in metadata.keys():
                if "s" in metadata[key]:
                    images.append(metadata[key]["s"]["u"].replace("&amp;", "&"))

            if images:
                return {"type": "gallery", "urls": images}

        # check for single image (reddit hosted or external)
        #if "preview" in post_data and post_data["preview"] is not None and "images" in post_data["preview"]:
        #    image = post_data["preview"]["images"][0]["source"]["url"].replace("&amp;", "&")
        #    print(image)
        #    return {"type": "image", "url": image}

        # check for external links
        if "url_overridden_by_dest" in post_data:
            media_url = post_data["url_overridden_by_dest"]
    
            # handle redgif links separately
            if "redgifs.com" in media_url:
                return extract_redgif_media(media_url)

            if media_url.endswith(('.jpg', '.png', '.gif')):
                return {"type": "image", "url": media_url}

            return {"type": "external", "url": media_url}

    except requests.RequestException as e:
        print(f"request error: {e}")
    except (KeyError, IndexError) as e:
        print(f"parsing error: {e}")

    return None

def extract_redgif_media(redgif_url):
    """
    extracts highest quality video from redgifs with sound
    """
    match = re.search(r"redgifs\.com/watch/([\w-]+)", redgif_url)
    if not match:
        return None

    video_id = match.group(1)
    api_url = f"https://api.redgifs.com/v2/gifs/{video_id}"
    print("yes")
    print(api_url)

    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(api_url, headers=headers)
        print(f"Response Status Code: {response.status_code}", file=sys.stderr, flush=True)
        response.raise_for_status()
        data = response.json()

        if "gif" in data and "urls" in data["gif"]:
            video_url = data["gif"]["urls"].get("hd", data["gif"]["urls"].get("sd"))
            if video_url:
                return {"type": "video", "url": video_url}

    except requests.RequestException as e:
        print(f"request error: {e}")
    except (KeyError, IndexError) as e:
        print(f"parsing error: {e}")

    return None
