from flask import Blueprint, render_template, request, redirect, url_for
from .scraper import fetch_reddit_media

main = Blueprint('main', __name__)

@main.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        reddit_url = request.form.get("reddit_url")
        media_url = fetch_reddit_media(reddit_url)
        return render_template("result.html", media=media_url)
    return render_template("index.html")
