#!/usr/bin/env python3

# YouTube_download.py

import os
from pytube import YouTube
import sys
import re
import subprocess
import tempfile
import logging
from datetime import datetime

# Configure logging to append to the log file
logging.basicConfig(filename='download_log.txt', filemode='a', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def download_youtube_video(url, output_directory):
    """
    Download a YouTube video given its URL.

    Args:
        url (str): The URL of the YouTube video.
        output_directory (str): The directory to save the downloaded video.

    Returns:
        None
    """
    try:
        logging.info(f"Downloading started for URL: {url}")

        # Create output directory if it doesn't exist
        os.makedirs(output_directory, exist_ok=True)

        # Create a YouTube object
        yt = YouTube(url)

        # Get the highest resolution stream
        video_stream = yt.streams.filter(file_extension="mp4").get_highest_resolution()

        # Extract video title and sanitize for filename
        video_title = re.sub(r"[^\w\s.-]", "", yt.title)
        video_title = re.sub(r"\s+", " ", video_title)  # Replace consecutive spaces with a single space
        video_filename = f"{video_title}.mp4"
        video_filepath = os.path.join(output_directory, video_filename)

        # Check if the file already exists
        if os.path.exists(video_filepath):
            # Append an incremental identifier to the filename
            increment = 1
            while os.path.exists(os.path.join(output_directory, f"{video_title}_{increment}.mp4")):
                increment += 1
            video_filename = f"{video_title}_{increment}.mp4"
            video_filepath = os.path.join(output_directory, video_filename)
            logging.info(f"Filename already exists. Appending identifier: {video_filename}")

        # Download the video to a temporary file
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
        temp_filepath = temp_file.name

        logging.info(f"Downloading: {video_title} (URL: {url})")

        # Start download timer
        download_start_time = datetime.now()

        video_stream.download(output_directory, filename=temp_filepath)
        temp_file.close()

        # End download timer
        download_end_time = datetime.now()
        download_duration = download_end_time - download_start_time
        logging.info(f"Download completed in {download_duration}")

        # Strip metadata using FFmpeg
        strip_metadata(temp_filepath, video_filepath)

        logging.info(f"Video downloaded successfully to {video_filepath}")

        # Print success completion message to the console
        print(f"Video downloaded successfully to {video_filepath}")

    except Exception as e:
        logging.error(f"An error occurred: {e}")

def strip_metadata(input_filepath, output_filepath):
    """
    Strip metadata from a video file using FFmpeg.

    Args:
        input_filepath (str): Path to the input video file.
        output_filepath (str): Path to the output video file.

    Returns:
        None
    """
    try:
        # FFmpeg command to strip metadata
        cmd = [
            "ffmpeg",
            "-hide_banner",
            "-i",
            input_filepath,
            "-map_metadata",
            "-1",
            "-c",
            "copy",
            output_filepath,
        ]

        # Run the command and capture output
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True, text=True)

        # Log the output
        logging.info(f"FFmpeg stdout output: {result.stdout}")
        logging.info(f"FFmpeg stderr error output: {result.stderr}")

        logging.info(f"Metadata stripped successfully from {input_filepath}")
    except subprocess.CalledProcessError as e:
        logging.error(f"Error stripping metadata: {e}")
    finally:
        os.remove(input_filepath)  # Remove the temporary file

if __name__ == "__main__":
    # Prompt for YouTube video URL
    print("Enter the YouTube video URL:")
    video_url = sys.stdin.readline().strip()

    # Specify the output directory using the appropriate method for the current OS
    output_directory = os.path.join(os.path.expanduser('~'), 'Videos', 'YouTube_downloads')

    # Download the video
    download_youtube_video(video_url, output_directory)