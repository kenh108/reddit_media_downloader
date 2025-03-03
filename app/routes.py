from flask import Blueprint, render_template, request, redirect, send_from_directory, url_for
import logging
import os
import sys
from .scraper import fetch_reddit_media
from .downloader import download_media, MEDIA_FOLDER

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

        media_type = media.get("type")

        if media_type == "video":
            video_url = media.get("video_url")
            audio_url = media.get("audio_url") # Will be None for Redgifs

            logging.debug(f"Media found: video - {video_url} | audio - {audio_url}")

            local_filename = download_media(video_url, audio_url)
            if not local_filename:
                return render_template("index.html", error="Failed to download video.")


        elif media_type == "gif":
            gif_url = media.get("gif_url")

            logging.debug(f"Media found: GIF - {gif_url}")

            local_filename = download_media(gif_url)
            if not local_filename:
                return render_template("index.html", error="Failed to download GIF.")

        return render_template("index.html", media_url=url_for('main.serve_media', filename=local_filename), media_type=media_type)

    return render_template("index.html")

@main.route("/serve_media/<filename>")
def serve_media(filename):
    """
    Serve a previously downloaded media file.
    """
    file_path = os.path.join(MEDIA_FOLDER, filename)
    
    if not os.path.exists(file_path):
        logging.warning(f"File not found: {file_path}")
        return abort(404)

    logging.debug(f"Serving file: {file_path}")

    return send_from_directory(MEDIA_FOLDER, filename)
