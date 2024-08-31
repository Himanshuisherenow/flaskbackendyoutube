def download_video(url, resolution=None, download_path=None):
    if not is_valid_youtube_url(url):
        print(f"Invalid YouTube URL: {url}")
        return False

    try:
        yt = YouTube(url)

        if resolution is None:
            resolutions = get_resolutions(yt)
            if not resolutions:
                print("No valid resolutions found. Skipping this video.")
                return False
            resolution = select_resolution(resolutions)

        # Try to get the selected resolution or higher
        video_stream = yt.streams.filter(res=resolution, file_extension='mp4').first()
        if not video_stream:
            print(f"Resolution {resolution} not available. Trying higher resolutions...")
            higher_resolutions = [res for res in get_resolutions(yt) if int(res[:-1]) > int(resolution[:-1])]
            for res in higher_resolutions:
                video_stream = yt.streams.filter(res=res, file_extension='mp4').first()
                if video_stream:
                    print(f"Using higher resolution: {res}")
                    break

        # If still no stream, get the highest available resolution
        if not video_stream:
            print("No higher resolution available. Using the highest available resolution.")
            video_stream = yt.streams.filter(progressive=False, file_extension='mp4').order_by('resolution').desc().first()

        # Get the best audio stream
        audio_stream = yt.streams.filter(only_audio=True).order_by('abr').desc().first()

        if not video_stream:
            print(f"No video stream available for {url}.")
            return False

        if not audio_stream:
            print(f"No separate audio stream available. Attempting to use audio from a lower quality video.")
            # Get a progressive stream (contains both video and audio) with the highest quality
            combined_stream = yt.streams.filter(progressive=True, file_extension='mp4').order_by('resolution').desc().first()
            if combined_stream:
                audio_stream = combined_stream
            else:
                print(f"No audio available for {url}. Downloading video without audio.")

        if not download_path:
            download_path = os.path.join(os.path.expanduser("~"), "Downloads", "YouTubeDownloads")

        if not os.path.exists(download_path):
            os.makedirs(download_path)

        print(f"Downloading '{yt.title}' video in {video_stream.resolution} resolution to '{download_path}'...")
        video_file = video_stream.download(output_path=download_path, filename_prefix="video_")
        print(f"Video download of '{yt.title}' complete!")

        if audio_stream:
            print(f"Downloading '{yt.title}' audio to '{download_path}'...")
            audio_file = audio_stream.download(output_path=download_path, filename_prefix="audio_")
            print(f"Audio download of '{yt.title}' complete!")

        combined_file = os.path.join(download_path, f"{yt.title}.mp4")

        if audio_stream:
            print(f"Combining video and audio into '{combined_file}'...")
            command = f'ffmpeg -i "{video_file}" -i "{audio_file}" -c:v copy -c:a aac -strict experimental "{combined_file}" -y'
        else:
            print(f"No audio available. Copying video to '{combined_file}'...")
            command = f'ffmpeg -i "{video_file}" -c copy "{combined_file}" -y'

        subprocess.run(command, shell=True, check=True)

        print(f"Processing of '{yt.title}' complete!")
        os.remove(video_file)
        if audio_stream and audio_stream != video_stream:
            os.remove(audio_file)
        return True

    except KeyboardInterrupt:
        print("Download interrupted.")
        return False
    except Exception as e:
        print(f"Failed to download {url}: {str(e)}")
        print(f"Retrying download for {url}...")
        if retry_download(url, resolution, download_path):
            print(f"Successfully downloaded '{yt.title}' after retries.")
            return True
        else:
            print(f"Failed to download '{yt.title}' after retries.")
            return False