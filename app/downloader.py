import os
import requests
import logging
import subprocess
from urllib.parse import urlparse

MEDIA_FOLDER = os.path.abspath("static/media")
os.makedirs(MEDIA_FOLDER, exist_ok=True)

def download_media(video_url, audio_url=None):
    """
    Downloads video, and if audio is available merges them using FFmpeg.
    GIFs are downloaded, and don't require any extra processing.
    """
    try:
        headers = {"User-Agent": "Mozilla/5.0"}

        # Extract filename from video URL
        parsed_video_url = urlparse(video_url)
        video_filename = os.path.basename(parsed_video_url.path).split("?")[0]
        video_path = os.path.join(MEDIA_FOLDER, video_filename)

        # Handle GIFs without merging
        if video_filename.endswith(".gif"):
            return download_file(video_url, video_path)

        if not video_filename.endswith(".mp4"):
            video_filename += ".mp4"
            video_path += ".mp4"

        #if os.path.exists(video_path):
        #    logging.info(f"File already exists: {video_path}")
        #    return video_filename

        logging.info(f"Downloading video: {video_url} -> {video_path}")
        download_file(video_url, video_path)

        if not audio_url:
            return video_filename

        # Extract filename from audio URL
        parsed_audio_url = urlparse(audio_url)
        audio_filename = os.path.basename(parsed_audio_url.path).split("?")[0]
        audio_path = os.path.join(MEDIA_FOLDER, audio_filename)

        logging.info(f"Downloading audio: {audio_url} -> {audio_path}")
        download_file(audio_url, audio_path)

        # Set filename and path for merged file (video + audio)
        merged_filename = "merged_" + video_filename
        merged_path = os.path.join(MEDIA_FOLDER, merged_filename)

        logging.info(f"Merging video and audio: {video_path} + {audio_path} -> {merged_path}")

        ffmpeg_cmd = [
            "ffmpeg", "-y",
            "-i", video_path,
            "-i", audio_path,
            "-c:v", "copy", "-c:a", "aac",
            merged_path
        ]
        subprocess.run(ffmpeg_cmd, check=True)

        # Delete prep files after merging
        os.remove(video_path)
        os.remove(audio_path)

        return merged_filename


    except requests.RequestException as e:
        logging.error(f"Failed to download media: {e}")
        return None
    except subprocess.CalledProcessError as e:
        logging.error(f"FFmpeg merging failed: {e}")
        return None

def download_file(url, file_path):
    """
    Downloads a file in chunks (avoids excess memeory usage).
    """
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers, stream=True)
        response.raise_for_status()

        with open(file_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        logging.info(f"Download complete: {file_path}")
        return os.path.basename(file_path)

    except requests.RequestException as e:
        logging.error(f"Failed to download media: {e}")
        return None
