import os, uuid
from pytubefix import YouTube
from pytubefix.cli import on_progress
from datetime import datetime


class DownloadYoutubeVideo:
    def __init__(self, url, whisper_size):
        self.video_path = "data/video"

        self.url = url
        self.whisper_size = whisper_size
        self.filename = str(uuid.uuid4()) + f"_{self.whisper_size}"

    def download(self):
        yt = YouTube(self.url, on_progress_callback=on_progress)
        ys = yt.streams.get_highest_resolution()
        video = ys.download(self.video_path)
        os.rename(video, f"{self.video_path}/{self.filename}.mp4")
        print(
            f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | downloading video finished"
        )
        return self.filename
