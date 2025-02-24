from flask import Blueprint, render_template, request, redirect, send_from_directory
import logging
import os
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

        media_url = media.get("url")
        media_type = media.get("type")

        logging.info(f"Media found: {media_type} - {media_url}")

        local_filename = download_media(media_url)

        if not local_filename:
            return render_template("index.html", error="Failed to download media.")

        return redirect(f"/serve_media/{local_filename}")

    return render_template("index.html")

@main.route("/serve_media/<filename>")
def serve_media(filename):
    """
    Serve a previously downloaded media file.
    """
    file_path = os.path.join(MEDIA_FOLDER, filename)
    
    if not os.path.exists(file_path):
        logging.error(f"File note found: {file_path}")
        return abort(404)

    logging.info(f"Serving file: {file_path}")

    return send_from_directory(MEDIA_FOLDER, filename)
