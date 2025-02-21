import re

def fetch_reddit_media(url):
    if not re.match(r"https?://(www\.)?reddit\.com", url):
        return None
    return url
