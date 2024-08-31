#!/usr/bin/env python3

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
        output_directory (str): The directory to save the downloaded video or audio.

    Returns:
        None
    """
    try:
        os.makedirs(output_directory, exist_ok=True)
    except OSError as e:
        print(f"Error creating output directory: {e}")
        sys.exit(1)

def download_youtube_video(url, output_directory, audio_only=False):
    """
    Download a YouTube video or audio given its URL.

    Args:
        url (str): The URL of the YouTube video.
        output_directory (str): The directory to save the downloaded video or audio.
        audio_only (bool): If True, only download the audio.

    Returns:
        None
    """
    try:
        logging.info(f"Downloading started for URL: {url}")

        # Create output directory
        create_output_directory(output_directory)

        # Create a YouTube object
        yt = YouTube(url)

        if audio_only:
            # Get the best audio stream
            audio_stream = yt.streams.filter(only_audio=True).order_by('abr').desc().first()
            if audio_stream is None:
                print("Error: No suitable audio stream found.")
                sys.exit(1)

            # Extract video title and sanitize for filename
            audio_title = re.sub(r"[^\w\s.-]", "", yt.title)
            audio_title = re.sub(r"\s+", " ", audio_title)  # Replace consecutive spaces with a single space
            audio_filename = f"{audio_title}.mp3"
            audio_filepath = os.path.join(output_directory, audio_filename)

            # Check if the file already exists
            if os.path.exists(audio_filepath):
                # Append an incremental identifier to the filename
                increment = 1
                while os.path.exists(os.path.join(output_directory, f"{audio_title}_{increment}.mp3")):
                    increment += 1
                audio_filename = f"{audio_title}_{increment}.mp3"
                audio_filepath = os.path.join(output_directory, audio_filename)
                logging.info(f"Filename already exists. Appending identifier: {audio_filename}")

            # Download the audio to a temporary file
            temp_audio_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")

            logging.info(f"Downloading audio: {audio_title} (URL: {url})")
            audio_stream.download(filename=temp_audio_file.name)

            # Convert audio to MP3
            convert_audio_to_mp3(temp_audio_file.name, audio_filepath)

            logging.info(f"Audio downloaded successfully to {audio_filepath}")

            # Print success completion message to the console
            print(f"Audio downloaded successfully to {audio_filepath}")

        else:
            # Get the highest resolution video stream and the best audio stream
            video_stream = yt.streams.filter(adaptive=True, file_extension="mp4").order_by('resolution').desc().first()
            audio_stream = yt.streams.filter(only_audio=True, file_extension="mp4").first()

            if video_stream is None or audio_stream is None:
                print("Error: No suitable video or audio stream found.")
                sys.exit(1)

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

            # Download the video and audio to temporary files
            temp_video_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
            temp_audio_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")

            logging.info(f"Downloading video: {video_title} (URL: {url})")
            video_stream.download(filename=temp_video_file.name)
            audio_stream.download(filename=temp_audio_file.name)

            # Merge video and audio using FFmpeg
            merge_video_audio(temp_video_file.name, temp_audio_file.name, video_filepath)

            logging.info(f"Video downloaded successfully to {video_filepath}")

            # Print success completion message to the console
            print(f"Video downloaded successfully to {video_filepath}")

    except Exception as e:
        logging.error(f"An error occurred: {e}")
        print("Error: An unexpected error occurred. Please check the log for details.")
        sys.exit(1)

def merge_video_audio(video_filepath, audio_filepath, output_filepath):
    """
    Merge video and audio files into one using FFmpeg.

    Args:
        video_filepath (str): Path to the video file.
        audio_filepath (str): Path to the audio file.
        output_filepath (str): Path to the output file.

    Returns:
        None
    """
    try:
        # FFmpeg command to merge video and audio
        cmd = [
            "ffmpeg",
            "-hide_banner",
            "-i", video_filepath,
            "-i", audio_filepath,
            "-c:v", "copy",
            "-c:a", "aac",
            "-strict", "experimental",
            output_filepath,
        ]

        # Run the command and capture output
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True, text=True)

        # Log the output
        logging.info(f"FFmpeg stdout output: {result.stdout}")
        logging.info(f"FFmpeg stderr error output: {result.stderr}") 
        logging.info(f"Video and audio merged successfully into {output_filepath}")
    except subprocess.CalledProcessError as e:
        logging.error(f"Error merging video and audio: {e}")
    finally:
        os.remove(video_filepath)  # Remove the temporary video file
        os.remove(audio_filepath)  # Remove the temporary audio file

def convert_audio_to_mp3(input_filepath, output_filepath):
    """
    Convert audio file to MP3 using FFmpeg.

    Args:
        input_filepath (str): Path to the input audio file.
        output_filepath (str): Path to the output MP3 file.

    Returns:
        None
    """
    try:
        # FFmpeg command to convert audio to MP3
        cmd = [
            "ffmpeg",
            "-hide_banner",
            "-i", input_filepath,
            "-vn",  # no video
            "-ab", "192k",  # audio bitrate
            "-ar", "44100",  # audio sampling rate
            "-y",  # overwrite output file if exists
            output_filepath,
        ]

        # Run the command and capture output
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True, text=True)

        # Log the output
        logging.info(f"FFmpeg stdout output: {result.stdout}")
        logging.info(f"FFmpeg stderr error output: {result.stderr}")

        logging.info(f"Audio converted successfully to MP3: {output_filepath}")
    except subprocess.CalledProcessError as e:
        logging.error(f"Error converting audio to MP3: {e}")
    finally:
        os.remove(input_filepath)  # Remove the temporary audio file

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
    # Check if FFmpeg is installed
    if not check_ffmpeg():
        print("Error: FFmpeg not installed.")
        sys.exit(1)

    # Prompt for YouTube video URL or path to a .txt file
    print("YouTube Video Downloader")
    print("Provide a single URL, or a .txt file containing a list of URLs. Example: `url_list.txt`")
    print("Enter the video URL or path to a .txt file:")
    user_input = sys.stdin.readline().strip()

    # Process the input to get a list of URLs
    urls_to_process = process_input(user_input)

    # Ask the user if they want to download only the audio
    print("Do you want to download only the audio? (y/n):")
    audio_only_input = sys.stdin.readline().strip().lower()
    audio_only = audio_only_input == 'y'

    # Set the output directory in the same directory as the script
    output_directory = os.path.join(script_directory, 'YouTube_downloads')

    # Download the videos or audio
    for url in urls_to_process:
        download_youtube_video(url, output_directory, audio_only=audio_only)
