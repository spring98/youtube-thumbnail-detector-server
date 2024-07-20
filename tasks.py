from celery import Celery
from celery.schedules import crontab
from utils import downloader, analyzer
from dotenv import load_dotenv
import tensorflow as tf
import requests
import os
import json
import logging

# 로깅 설정
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Eager Execution 모드 활성화
tf.config.experimental_run_functions_eagerly(True)
# tf.data 함수에 대한 즉시 실행 모드 활성화
tf.data.experimental.enable_debug_mode()

app = Celery('tasks', broker='redis://localhost:6379/0', backend='redis://localhost:6379/0')

def save_result_to_file(video_id, result):
    result_path = f'assets/{video_id}/result.txt'
    os.makedirs(os.path.dirname(result_path), exist_ok=True)
    with open(result_path, 'w') as file:
        for key, value in result.items():
            file.write(f'{key}: {value}\n')

def load_result_from_file(video_id):
    result_path = f'assets/{video_id}/result.txt'
    if os.path.exists(result_path):
        with open(result_path, 'r') as file:
            result = {}
            for line in file:
                key, value = line.strip().split(': ', 1)
                if key == 'best_frame_time':
                    result[key] = float(value)
                else:
                    result[key] = value
            return result
    return None

def delete_video_and_thumbnail(video_id):
    video_path = f'assets/{video_id}/video.mp4'
    thumbnail_path = f'assets/{video_id}/thumbnail.jpg'
    if os.path.exists(video_path):
        os.remove(video_path)
    if os.path.exists(thumbnail_path):
        os.remove(thumbnail_path)

def load_processed_video_ids():
    if os.path.exists('.videos.json'):
        with open('.videos.json', 'r') as file:
            return json.load(file)
    return []

def save_processed_video_ids(video_ids):
    with open('.videos.json', 'w') as file:
        json.dump(video_ids, file)

@app.task
def process_video(video_id):
    existing_result = load_result_from_file(video_id)
    if existing_result:
        return existing_result

    try:
        downloader.Downloader().execute(videoId=video_id)
        video_path = f'assets/{video_id}/video.mp4'
        target_image_path = f'assets/{video_id}/thumbnail.jpg'

        analyzer_obj = analyzer.ImageAnalyzer(video_path=video_path, target_image_path=target_image_path)
        best_frame, best_frame_time = analyzer_obj.find_most_similar_frame()

        result = {
            'videoId': video_id,
            'best_frame_time': best_frame_time,
            'message': 'Best frame found successfully' if best_frame is not None else 'Could not find the best frame'
        }
        save_result_to_file(video_id, result)
        delete_video_and_thumbnail(video_id)
        return result
    except Exception as e:
        result = {'error': str(e)}
        return result

@app.task
def fetch_and_download_videos():
    load_dotenv()
    api_key = os.environ.get('API_KEY')
    base_url = "https://www.googleapis.com/youtube/v3/videos"
    processed_video_ids = load_processed_video_ids()
    params = {
        "part": "snippet",
        "chart": "mostPopular",
        "regionCode": "KR",
        "maxResults": 10,
        "key": api_key
    }

    response = requests.get(base_url, params=params)
    data = response.json()

    logger.debug(f"items:: {data}")

    video_ids = [item['id'] for item in data['items']]
    new_video_ids = [vid for vid in video_ids if vid not in processed_video_ids]

    for video_id in new_video_ids:
        process_video.delay(video_id)

    next_page_token = data.get('nextPageToken')
    while next_page_token:
        params['pageToken'] = next_page_token
        response = requests.get(base_url, params=params)
        data = response.json()

        video_ids = [item['id'] for item in data['items']]
        new_video_ids = [vid for vid in video_ids if vid not in processed_video_ids]

        for video_id in new_video_ids:
            process_video.delay(video_id)

        next_page_token = data.get('nextPageToken')

app.conf.beat_schedule = {
    'fetch-and-download-videos-every-hour': {
        'task': 'tasks.fetch_and_download_videos',
        'schedule': crontab(minute=0, hour='*'),
        # 'schedule': crontab(minute='*'),
    },
}
