import os
from pytube import YouTube
import sys
import re
import subprocess
import tempfile


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
        # Create output directory if it doesn't exist
        os.makedirs(output_directory, exist_ok=True)

        # Create a YouTube object
        yt = YouTube(url)

        # Get the highest resolution stream
        video_stream = yt.streams.filter(file_extension='mp4').get_highest_resolution()

        # Extract video title and sanitize for filename
        video_title = re.sub(r'[^\w\s.-]', '', yt.title)
        video_title = re.sub(r'\s+', ' ', video_title)  # Replace consecutive spaces with a single space
        video_filename = f"{video_title}.mp4"
        video_filepath = os.path.join(output_directory, video_filename)

        # Download the video to a temporary file
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
        temp_filepath = temp_file.name

        print(f"Downloading: {video_title}")
        video_stream.download(output_directory, filename=temp_filepath)
        temp_file.close()

        # Strip metadata using FFmpeg
        strip_metadata(temp_filepath, video_filepath)

        print(f"\nVideo downloaded successfully to {video_filepath}")
    except Exception as e:
        print(f"An error occurred: {e}")

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
        subprocess.run(["ffmpeg", "-i", input_filepath, "-map_metadata", "-1", "-c", "copy", output_filepath],
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error stripping metadata: {e}")
    finally:
        os.remove(input_filepath)  # Remove the temporary file


if __name__ == "__main__":
    # Prompt for YouTube video URL
    print("Enter the YouTube video URL:")
    video_url = sys.stdin.readline().strip()

    # Specify the output directory using os.getenv('USER')
    output_directory = f"/home/{os.getenv('USER')}/Videos/YouTube_downloads"

    # Download the video
    download_youtube_video(video_url, output_directory)
