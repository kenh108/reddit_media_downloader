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
        if not media:
            return render_template("index.html", error="No media found.")

        media_url = media.get("url")
        media_type = media.get("type")

        logging.info(f"Media found: {media_type} - {media_url}")

        # redirect to proxy route based on media type
        if media_type == "video":
            return redirect(f"proxy?video_url={media_url}")
        elif media_type == "gif":
            return redirect(f"proxy?gif_url={media_url}")

        return render_template("index.html", error="Invalid type of media found.")

    return render_template("index.html")

@main.route("/proxy")
def proxy_video():
    """
    fetches the redgifs video and streams it to the user, bypassing
    mobile restrictions that prevent .mp4 access
    """
    video_url = request.args.get("video_url")
    gif_url = request.args.get("gif_url")

    if not video_url and not gif_url:
        return "No media URL provided", 400

    media_url = video_url or gif_url
    logging.info(f"Fetching media for proxying: {media_url}")

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36"
    }

    response = requests.get(media_url, headers=headers, stream=True)
    if response.status_code != 200:
        return f"Failed to fetch media: {response.status_code}", response.status_code

    # determine type of content
    content_type = "image/gif" if gif_url else "video/mp4"

    content_length = response.headers.get("Content-Length")

    # stream the video in chunks to reduce server memory usage
    def generate():
        for chunk in response.iter_content(chunk_size=8192):
            yield chunk

    flask_response = Response(generate(), content_type=content_type)
    if content_length:
        flask_response.headers["Content-Length"] = content_length

    return flask_response
