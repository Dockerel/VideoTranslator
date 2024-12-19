import os, ffmpeg, math, urllib, json
from dotenv import load_dotenv
from faster_whisper import WhisperModel
from datetime import datetime


class TranslateVideo:
    def __init__(self, filename, whisper_size, target_language, use_gpu):
        self.audio_path = "data/audio"
        self.video_path = "data/video"
        self.subtitle_path = "data/subtitle"

        self.filename = filename
        self.whisper_size = whisper_size
        self.target_language = target_language
        self.use_gpu = use_gpu

        load_dotenv()
        self.client_id = os.getenv("X-NCP-APIGW-API-KEY-ID")
        self.client_secret = os.getenv("X-NCP-APIGW-API-KEY")

    def translate(self, source_text, source_language):
        """
        Translate text by papago api.

        Args:
            source_text (str): original text to translate.
            source_language (str, optional): source language to translate.
            target_language (str, optional): target language to translate. Defaults to "ko".

        Returns:
            str: translated text.
        """
        try:
            url = "https://naveropenapi.apigw.ntruss.com/nmt/v1/translation"

            encText = urllib.parse.quote(source_text)

            data = "source=%s&target=%s&text=%s" % (
                source_language,
                self.target_language,
                encText,
            )
            request = urllib.request.Request(url)
            request.add_header("X-NCP-APIGW-API-KEY-ID", self.client_id)
            request.add_header("X-NCP-APIGW-API-KEY", self.client_secret)
            response = urllib.request.urlopen(request, data=data.encode("utf-8"))

            response_body = response.read()
            result_json = json.loads(response_body.decode("utf-8"))
            translated_text = result_json["message"]["result"]["translatedText"]
            return translated_text
        except Exception as e:
            print(str(e))
            return

    def extract_audio(self):
        extracted_audio = f"{self.filename}.wav"
        stream = ffmpeg.input(f"{self.video_path}/{self.filename}.mp4")
        stream = ffmpeg.output(stream, f"{self.audio_path}/{extracted_audio}")
        ffmpeg.run(stream, overwrite_output=True)

    def transcribe(self):
        model = WhisperModel(
            self.whisper_size, device="cuda" if self.use_gpu else "cpu"
        )
        segments, data = model.transcribe(f"{self.audio_path}/{self.filename}.wav")
        segments = list(segments)
        return segments, data

    def format_time_for_srt(self, seconds):
        hours = math.floor(seconds / 3600)
        seconds %= 3600
        minutes = math.floor(seconds / 60)
        seconds %= 60
        miliseconds = round((seconds - math.floor(seconds)) * 1000)
        seconds = math.floor(seconds)
        formatted_time = (
            f"{hours :02d}:{minutes :02d}:{seconds :02d},{miliseconds :03d}"
        )
        return formatted_time

    def generate_subtitle_file(self, segments, data):
        subtitle_file = f"{self.filename}.srt"
        text = ""
        for index, segment in enumerate(segments):
            segment_start = self.format_time_for_srt(segment.start)
            segment_end = self.format_time_for_srt(segment.end)

            translated_text = self.translate(segment.text, data.language)

            text += f"{str(index + 1)}\n"
            text += f"{segment_start} --> {segment_end}\n"
            text += f"{translated_text}\n\n"

        with open(f"{self.subtitle_path}/{subtitle_file}", "w", encoding="utf-8") as f:
            f.write(text)

    def add_subtitle_to_video(self):
        video_input_stream = ffmpeg.input(f"{self.video_path}/{self.filename}.mp4")
        temp_output_video = f"{self.video_path}/temp_{self.filename}.mp4"
        result = f"{self.video_path}/{self.filename}.mp4"
        stream = None
        if self.use_gpu:
            stream = ffmpeg.output(
                video_input_stream,
                temp_output_video,
                vf=f"subtitles='{self.subtitle_path}/{self.filename}.srt'",
                vcodec="h264_nvenc",
                acodec="copy",
                preset="slow",
                cq=0,
            ).global_args("-hwaccel", "cuda")
        else:
            stream = ffmpeg.output(
                video_input_stream,
                temp_output_video,
                vf=f"subtitles='{self.subtitle_path}/{self.filename}.srt'",
                vcodec="libx264",
                acodec="copy",
                preset="slow",
                crf=23,
            )
        ffmpeg.run(stream, overwrite_output=True)
        os.replace(temp_output_video, result)

    def run(self):
        self.extract_audio()
        print(
            f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | extracting audio finished"
        )
        segments, data = self.transcribe()
        print(
            f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | extracting script finished"
        )
        self.generate_subtitle_file(segments, data)
        print(
            f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | generating subtitle finished"
        )
        self.add_subtitle_to_video()
        print(
            f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | adding subtitle finished"
        )

        os.remove(f"{self.subtitle_path}/{self.filename}.srt")
        os.remove(f"{self.audio_path}/{self.filename}.wav")
        print(
            f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | video translation finished"
        )
