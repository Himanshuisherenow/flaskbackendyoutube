from pytube import YouTube, Playlist
import os
import concurrent.futures
import re
import time
import subprocess
import random

MAX_RETRIES = 5
RETRY_DELAY = 5  # seconds


def is_valid_youtube_url(url):
    youtube_regex = re.compile(r'(https?://)?(www\.)?(youtube|youtu|youtube-nocookie)\.(com|be)/.+')
    return youtube_regex.match(url) is not None


def get_resolutions(yt):
    try:
        streams = yt.streams.filter(progressive=True, file_extension='mp4').order_by('resolution').desc()
        resolutions = [stream.resolution for stream in streams if stream.resolution is not None]
        if not resolutions:
            streams = yt.streams.filter(adaptive=True, file_extension='mp4').order_by('resolution').desc()
            resolutions = [stream.resolution for stream in streams if stream.resolution is not None]
        unique_resolutions = sorted(set(resolutions), key=lambda x: int(x[:-1]), reverse=True)
        return unique_resolutions
    except Exception as e:
        print(f"Error retrieving resolutions: {e}")
        return ["720p", "480p", "360p", "240p", "144p"]  # Fallback resolutions


def select_resolution(resolutions):
    print("Available resolutions:")
    for index, resolution in enumerate(resolutions, start=1):
        print(f"{index}: {resolution}")
    while True:
        try:
            choice = int(input("Select the resolution by number: ")) - 1
            if 0 <= choice < len(resolutions):
                return resolutions[choice]
            else:
                print("Invalid choice. Please select a valid number.")
        except ValueError:
            print("Invalid input. Please enter a number.")

import yt_dlp
import os

def download_video(url, download_path=None, resolution='best'):
    ydl_opts = {
        'format': resolution,  # 'best' for highest quality, or set resolution like '720p'
        'outtmpl': os.path.join(download_path, '%(title)s.%(ext)s'),
        'postprocessors': [{
            'key': 'FFmpegVideoConvertor',
            'preferedformat': 'mp4',  # Convert to mp4 format
        }],
        'noplaylist': True,  # To make sure it's a single video, not a playlist
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

def download_videos(urls, download_path=None, resolution='best'):
    ydl_opts = {
        'format': resolution,
        'outtmpl': os.path.join(download_path, '%(title)s.%(ext)s'),
        'postprocessors': [{
            'key': 'FFmpegVideoConvertor',
            'preferedformat': 'mp4',
        }],
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download(urls)

def download_playlist(url, download_path=None, resolution='best'):
    ydl_opts = {
        'format': resolution,
        'outtmpl': os.path.join(download_path, '%(playlist)s/%(playlist_index)s - %(title)s.%(ext)s'),
        'postprocessors': [{
            'key': 'FFmpegVideoConvertor',
            'preferedformat': 'mp4',
        }],
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

if __name__ == "__main__":
    try:
        while True:
            option = input("Select option (1: single video, 2: multiple videos, 3: playlist, 4: quit): ").strip()

            if option == "1":
                video_url = input("Enter the YouTube video URL: ").strip()
                download_path = input("Enter the download path (leave empty for default 'Downloads' folder): ").strip()
                download_path = download_path if download_path else os.path.join(os.path.expanduser("~"), "Downloads", "YouTubeDownloads")
                download_video(video_url, download_path=download_path)
                print("Video downloaded successfully.")

            elif option == "2":
                video_urls = input("Enter the YouTube video URLs separated by commas: ").strip().split(',')
                download_path = input("Enter the download path (leave empty for default 'Downloads' folder): ").strip()
                download_path = download_path if download_path else os.path.join(os.path.expanduser("~"), "Downloads", "YouTubeDownloads")
                download_videos(video_urls, download_path=download_path)
                print("Videos downloaded successfully.")

            elif option == "3":
                playlist_url = input("Enter the YouTube playlist URL: ").strip()
                download_path = input("Enter the download path (leave empty for default 'Downloads' folder): ").strip()
                download_path = download_path if download_path else os.path.join(os.path.expanduser("~"), "Downloads", "YouTubeDownloads")
                download_playlist(playlist_url, download_path=download_path)
                print("Playlist downloaded successfully.")

            elif option == "4":
                print("Exiting the program...")
                break

            else:
                print("Invalid option. Please enter '1', '2', '3', or '4'.")

    except KeyboardInterrupt:
        print("\nOperation interrupted by user.")
    except Exception as e:
        print(f"An unexpected error occurred: {str(e)}")


if __name__ == "__main__":
    try:
        while True:
            option = input("Select option (1: single video, 2: multiple videos, 3: playlist, 4: quit): ").strip()

            if option == "1":
                video_url = input("Enter the YouTube video URL: ").strip()
                if is_valid_youtube_url(video_url):
                    download_path = input("Enter the download path (leave empty for default 'Downloads' folder): ").strip()
                    download_path = download_path if download_path else None
                    success = download_video(video_url, download_path=download_path)
                    if success:
                        print("Video downloaded successfully.")
                    else:
                        print("Failed to download video.")
                else:
                    print("Invalid YouTube URL. Please try again.")

            elif option == "2":
                video_urls = input("Enter the YouTube video URLs separated by commas: ").strip().split(',')
                valid_urls = [url for url in video_urls if is_valid_youtube_url(url)]
                if valid_urls:
                    download_path = input("Enter the download path (leave empty for default 'Downloads' folder): ").strip()
                    download_path = download_path if download_path else None
                    download_videos(valid_urls, download_path=download_path)
                else:
                    print("No valid YouTube URLs provided. Please try again.")

            elif option == "3":
                playlist_url = input("Enter the YouTube playlist URL: ").strip()
                if is_valid_youtube_url(playlist_url):
                    download_path = input("Enter the download path (leave empty for default 'Downloads' folder): ").strip()
                    download_path = download_path if download_path else None
                    download_playlist(playlist_url, download_path=download_path)
                else:
                    print("Invalid YouTube URL. Please try again.")

            elif option == "4":
                print("Exiting the program...")
                break

            else:
                print("Invalid option. Please enter '1', '2', '3', or '4'.")

    except KeyboardInterrupt:
        print("\nOperation interrupted by user.")
    except Exception as e:
        print(f"An unexpected error occurred: {str(e)}")
