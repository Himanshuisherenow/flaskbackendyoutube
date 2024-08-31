import os
import time
from flask import Flask, request, jsonify
from flask_cors import CORS
from yt_dlp import YoutubeDL
from pytube import YouTube, Playlist

app = Flask(__name__)
CORS(app)

DEFAULT_DOWNLOAD_FOLDER = os.path.join(os.path.expanduser("~"), "Downloads", "YouTubeDownloads")


def sanitize_path(path):
    """Ensure the path is within the user's home directory or set to the default."""
    base_directory = os.path.expanduser("~")
    abs_path = os.path.abspath(path)
    if not abs_path.startswith(base_directory):
        return DEFAULT_DOWNLOAD_FOLDER
    return abs_path


def ensure_download_path(download_path):
    """Ensure the download directory exists."""
    if not os.path.exists(download_path):
        os.makedirs(download_path)


def download_video_with_ytdlp(video_url, download_path, video_quality='best'):
    """Download a single video using yt-dlp."""
    video_output = os.path.join(download_path, '%(title)s.%(ext)s')
    ydl_opts = {
        'format': f'bestvideo[height<={video_quality}]+bestaudio/best/best',
        'outtmpl': video_output,
        'postprocessors': [{
            'key': 'FFmpegVideoConvertor',
            'preferedformat': 'mp4',
        }],
        'noplaylist': True,
        'merge_output_format': 'mp4',
    }

    for attempt in range(3):
        try:
            with YoutubeDL(ydl_opts) as ydl:
                ydl.download([video_url])
            print(f"Downloaded video: {video_url}")
            return True
        except Exception as e:
            print(f"yt-dlp attempt {attempt + 1} failed for video: {video_url}. Error: {str(e)}")
            time.sleep(5)

    return False


def download_video_with_pytube(video_url, download_path, video_quality='720p'):
    """Download a single video using pytube."""
    try:
        yt = YouTube(video_url)
        video_stream = yt.streams.filter(progressive=True, file_extension='mp4', res=video_quality).first()
        if not video_stream:
            video_stream = yt.streams.get_highest_resolution()
        video_stream.download(output_path=download_path)
        print(f"Downloaded video with pytube: {video_url}")
        return True
    except Exception as e:
        print(f"pytube failed for video: {video_url}. Error: {str(e)}")
        return False


def download_video(video_url, download_path, video_quality='best'):
    """Download video using yt-dlp, fallback to pytube."""
    success = download_video_with_ytdlp(video_url, download_path, video_quality)
    if not success:
        # Fallback to pytube if yt-dlp fails
        pytube_quality = '720p' if video_quality == 'best' else video_quality
        success = download_video_with_pytube(video_url, download_path, pytube_quality)
    return success


def download_playlist_sequentially(url, download_path, video_quality='best'):
    """Download a playlist sequentially, one video at a time."""
    download_path = sanitize_path(download_path)
    ensure_download_path(download_path)

    try:
        # Attempt to extract playlist info with yt-dlp
        with YoutubeDL({'extract_flat': True, 'quiet': True}) as ydl:
            info_dict = ydl.extract_info(url, download=False)
            playlist_title = info_dict.get('title', 'Unknown Playlist')
            playlist_path = os.path.join(download_path, playlist_title)
            ensure_download_path(playlist_path)

            for entry in info_dict['entries']:
                video_url = entry['url']
                success = download_video(video_url, playlist_path, video_quality)
                if not success:
                    print(f"Failed to download video: {video_url}")

        print(f"Finished downloading playlist: {playlist_title}")
        return True

    except Exception as e:
        print(f"yt-dlp failed to process playlist: {url}. Error: {str(e)}")
        print("Falling back to pytube...")

        # Fallback to pytube for playlist download
        try:
            playlist = Playlist(url)
            for video_url in playlist.video_urls:
                success = download_video(video_url, download_path, video_quality)
                if not success:
                    print(f"Failed to download video: {video_url}")
            return True
        except Exception as e:
            print(f"pytube also failed for playlist: {url}. Error: {str(e)}")
            return False


@app.route('/download_video', methods=['POST'])
def download_single_video():
    """Endpoint to download a single video."""
    data = request.json
    url = data.get('url')
    download_path = data.get('downloadPath', DEFAULT_DOWNLOAD_FOLDER)
    video_quality = data.get('videoQuality', 'best')  # Default to 'best'

    try:
        download_video(url, download_path, video_quality)
        return jsonify({"message": "Video downloaded successfully."}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/download_playlist', methods=['POST'])
def download_playlist_route():
    """Endpoint to download a playlist."""
    data = request.json
    url = data.get('url')
    download_path = data.get('downloadPath', DEFAULT_DOWNLOAD_FOLDER)
    video_quality = data.get('videoQuality', 'best')  # Default to 'best'

    try:
        download_playlist_sequentially(url, download_path, video_quality)
        return jsonify({"message": "Playlist downloaded successfully."}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True)
