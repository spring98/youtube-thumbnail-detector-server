# from pytube import YouTube
from pytubefix import YouTube
import requests
import logging

# 로깅 설정
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class Downloader:
    def __init__(self):
        self.video_uri = 'https://www.youtube.com/watch?v='

    def execute(self, videoId):
        yt = YouTube(self.video_uri+videoId)
        stream = yt.streams.filter(res='720p', file_extension='mp4', progressive=True).first()

        if not stream:
            # 720p progressive 스트림이 없다면 다른 해상도로 대체합니다.
            stream = yt.streams.filter(file_extension='mp4', progressive=True).order_by('resolution').desc().first()
            logger.debug(f"No 720p progressive stream found. Using {stream.resolution} stream instead.")

        if stream:
            stream.download(output_path=f'assets/{videoId}', filename='video.mp4')
            logger.debug("Download complete")

            # 썸네일 다운로드
            self.download_thumbnail(yt.thumbnail_url, videoId)

    def download_thumbnail(self, thumbnail_url, videoId):
        response = requests.get(thumbnail_url)
        if response.status_code == 200:
            with open(f'assets/{videoId}/thumbnail.jpg', 'wb') as f:
                f.write(response.content)
            logger.debug("Thumbnail download complete")
        else:
            logger.debug("Failed to download thumbnail")


if __name__ == '__main__':
    # Downloader().execute('_-anr5vmXM8')
    # Downloader().execute('U8M8LNnWMzk')
    Downloader().execute(videoId='tJGunpmi2wo')
