from flask import Flask, request, jsonify
from utils import downloader, analyzer
from threading import Thread
import time
import os
import requests
import json

from dotenv import load_dotenv

load_dotenv()
api_key = os.environ.get('API_KEY')

app = Flask(__name__)

base_url = "https://www.googleapis.com/youtube/v3/videos"


# 결과를 파일로 저장하는 함수
def save_result_to_file(video_id, result):
    result_path = f'assets/{video_id}/result.txt'
    os.makedirs(os.path.dirname(result_path), exist_ok=True)
    with open(result_path, 'w') as file:
        for key, value in result.items():
            file.write(f'{key}: {value}\n')


# 동영상과 썸네일을 삭제하는 함수
def delete_video_and_thumbnail(video_id):
    video_path = f'assets/{video_id}/video.mp4'
    thumbnail_path = f'assets/{video_id}/thumbnail.jpg'

    if os.path.exists(video_path):
        os.remove(video_path)
    if os.path.exists(thumbnail_path):
        os.remove(thumbnail_path)


# 마지막으로 처리한 동영상 ID 목록을 저장하는 함수
def save_processed_video_ids(video_ids):
    with open('processed_videos.json', 'w') as file:
        json.dump(video_ids, file)


# 마지막으로 처리한 동영상 ID 목록을 불러오는 함수
def load_processed_video_ids():
    if os.path.exists('processed_videos.json'):
        with open('processed_videos.json', 'r') as file:
            return json.load(file)
    return []


# 인기 동영상 ID를 주기적으로 가져와 다운로드하는 함수
def fetch_and_download_videos():
    processed_video_ids = load_processed_video_ids()

    while True:
        params = {
            "part": "snippet",
            "chart": "mostPopular",
            "regionCode": "KR",
            "maxResults": 10,
            "key": api_key
        }

        response = requests.get(base_url, params=params)
        data = response.json()

        video_ids = [item['id'] for item in data['items']]
        new_video_ids = [vid for vid in video_ids if vid not in processed_video_ids]

        for video_id in new_video_ids:
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

                # 동영상과 썸네일 삭제
                delete_video_and_thumbnail(video_id)

                # 처리한 동영상 ID 목록에 추가
                processed_video_ids.append(video_id)
                save_processed_video_ids(processed_video_ids)

            except Exception as e:
                print(f"Error processing video {video_id}: {e}")

        next_page_token = data.get('nextPageToken')
        while next_page_token:
            params['pageToken'] = next_page_token
            response = requests.get(base_url, params=params)
            data = response.json()

            video_ids = [item['id'] for item in data['items']]
            new_video_ids = [vid for vid in video_ids if vid not in processed_video_ids]

            for video_id in new_video_ids:
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

                    # 동영상과 썸네일 삭제
                    delete_video_and_thumbnail(video_id)

                    # 처리한 동영상 ID 목록에 추가
                    processed_video_ids.append(video_id)
                    save_processed_video_ids(processed_video_ids)

                except Exception as e:
                    print(f"Error processing video {video_id}: {e}")

            next_page_token = data.get('nextPageToken')

        # 주기적으로 실행 (예: 1시간마다)
        time.sleep(3600)


# 백그라운드에서 인기 동영상 다운로드 작업 시작
download_thread = Thread(target=fetch_and_download_videos)
download_thread.daemon = True
download_thread.start()


@app.route('/process_video', methods=['GET'])
def process_video():
    videoId = request.args.get('videoId')
    if not videoId:
        return jsonify({'error': 'Invalid input'}), 400

    try:
        downloader.Downloader().execute(videoId=videoId)
        video_path = f'assets/{videoId}/video.mp4'
        target_image_path = f'assets/{videoId}/thumbnail.jpg'

        analyzer_obj = analyzer.ImageAnalyzer(video_path=video_path, target_image_path=target_image_path)
        best_frame, best_frame_time = analyzer_obj.find_most_similar_frame()

        result = {
            'videoId': videoId,
            'best_frame_time': best_frame_time,
            'message': 'Best frame found successfully' if best_frame is not None else 'Could not find the best frame'
        }
        save_result_to_file(videoId, result)

        # 동영상과 썸네일 삭제
        delete_video_and_thumbnail(videoId)

        return jsonify(result), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=50001)