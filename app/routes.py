from flask import Blueprint, render_template, request, redirect, Response
import requests
import logging
from .scraper import fetch_reddit_media

main = Blueprint('main', __name__)

@main.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        reddit_url = request.form.get("reddit_url")
        if not reddit_url:
            return render_template("index.html", error="Please enter a Reddit link.")

        media = fetch_reddit_media(reddit_url)
        if media and media.get("type") == "video":
            video_url = media.get("url")
            logging.info(f"Serving video through proxy: {video_url}")

            # instead of redirecting, serve video ourselves
            return redirect(f"/proxy?video_url={video_url}")

        return render_template("index.html", error="No video found.")

    return render_template("index.html")

@main.route("/proxy")
def proxy_video():
    """
    fetches the redgifs video and streams it to the user, bypassing
    mobile restrictions that prevent .mp4 access
    """
    video_url = request.args.get("video_url")
    if not video_url:
        return "No video url provided", 400

    logging.info(f"Fetching video for proxying: {video_url}")

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36",
        "Referer": "https://www.redgifs.com/"
    }

    response = requests.get(video_url, headers=headers, stream=True)
    if response.status_code != 200:
        return f"Failed to fetch video: {response.status_code}", response.status_code

    # stream the video in chunks to reduce server memory usage
    def generate():
        for chunk in response.iter_content(chunk_size=1024):
            yield chunk

    return Response(generate(), content_type="video/mp4")
