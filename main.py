from util.downloadYoutuveVideo import DownloadYoutubeVideo
from util.translateVideo import TranslateVideo

# download youtube video
url = "paste youtube video url here"
whisper_size = "large"

downloader = DownloadYoutubeVideo(url, whisper_size)
filename = downloader.download()

# translate
use_gpu = True
target_language = "ko"
translator = TranslateVideo(filename, whisper_size, target_language, use_gpu)
translator.run()
