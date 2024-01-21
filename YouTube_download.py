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
from logging.handlers import TimedRotatingFileHandler

# Get the directory of the script
script_directory = os.path.dirname(os.path.abspath(__file__))

# Configure logging with a rotating log file
log_file_path = os.path.join(script_directory, 'download_log.log')
log_handler = TimedRotatingFileHandler(log_file_path, when="W0", interval=1, backupCount=8, encoding="utf-8")
log_handler.suffix = "%Y-%m-%d.log"  # Include the date in the log file name
log_handler.maxBytes = 2 * 1024 * 1024  # Set max log file size to 2 megabytes

logging.basicConfig(handlers=[log_handler], level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def check_ffmpeg():
    """
    Check if FFmpeg is installed on the machine.

    Returns:
        bool: True if FFmpeg is installed, False otherwise.
    """
    try:
        subprocess.run(['ffmpeg', '-version'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True, text=True)
        return True
    except subprocess.CalledProcessError:
        return False

def create_output_directory(output_directory):
    """
    Create the output directory if it doesn't exist.

    Args:
        output_directory (str): The directory to save the downloaded video.

    Returns:
        None
    """
    try:
        os.makedirs(output_directory, exist_ok=True)
    except OSError as e:
        print(f"Error creating output directory: {e}")
        sys.exit(1)

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
        # Check if FFmpeg is installed
        if not check_ffmpeg():
            print("Error: FFmpeg not installed.")
            sys.exit(1)

        logging.info(f"Downloading started for URL: {url}")

        # Create output directory
        create_output_directory(output_directory)

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
        print("Error: An unexpected error occurred. Please check the log for details.")
        sys.exit(1)

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

def process_input(input_str):
    """
    Determine whether the input is a URL or a path to a .txt file.

    Args:
        input_str (str): User input.

    Returns:
        list: List of URLs to process.
    """
    if input_str.startswith("http"):
        # If input starts with "http", treat it as a single URL
        return [input_str]
    elif input_str.lower().endswith(".txt"):
        # If input ends with ".txt", treat it as a path to a text file
        with open(input_str, 'r') as file:
            urls = [line.strip() for line in file if line.strip()]
            if not urls:
                print("Error: The .txt file does not contain valid URLs.")
                sys.exit(1)
            return urls
    else:
        # Otherwise, treat it as an unknown input
        print("Error: Unknown input format.")
        sys.exit(1)

if __name__ == "__main__":
    # Prompt for YouTube video URL or path to a .txt file
    print("YouTube Video Downloader")
    print("Provide a single URL, or a .txt file containing a list of URLs. Example: `url_list.txt`")
    print("Enter the video URL or path to a .txt file:")
    user_input = sys.stdin.readline().strip()

    # Process the input to get a list of URLs
    urls_to_process = process_input(user_input)

    # Set the output directory in the same directory as the script
    output_directory = os.path.join(script_directory, 'YouTube_downloads')

    # Download the videos
    for url in urls_to_process:
        download_youtube_video(url, output_directory)


