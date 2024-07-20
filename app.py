from flask import Flask, request, jsonify
from flask_cors import CORS
from tasks import process_video, load_result_from_file
from celery_config import make_celery
from dotenv import load_dotenv
import os

load_dotenv()
api_key = os.environ.get('API_KEY')

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})

app.config.update(
    CELERY_BROKER_URL='redis://localhost:6379/0',
    CELERY_RESULT_BACKEND='redis://localhost:6379/0'
)

celery = make_celery(app)

@app.route('/api/process_video', methods=['GET'])
def process_video_api():
    video_id = request.args.get('videoId')
    if not video_id:
        return jsonify({'error': 'Invalid input'}), 400

    # # 이미 처리된 결과가 있는지 확인
    # existing_result = load_result_from_file(video_id)
    # if existing_result:
    #     return jsonify({'taskId': None, 'result': existing_result}), 200

    task = process_video.delay(video_id)
    # return jsonify({'task_id': task.id, 'result': None}), 202
    return jsonify({'task_id': task.id}), 202

@app.route('/api/task_status', methods=['GET'])
def get_task_status():
    task_id = request.args.get('taskId')
    if not task_id:
        return jsonify({'error': 'Invalid input'}), 400

    # PENDING: 작업이 큐에 추가되었지만 아직 실행되지 않았음을 나타냅니다.
    # STARTED: 작업이 실행 중임을 나타냅니다.
    # RETRY: 작업이 실패하여 다시 시도 중임을 나타냅니다.
    # FAILURE: 작업이 실패했음을 나타냅니다.실패 이유를 error 필드에 포함합니다.
    # SUCCESS: 작업이 성공적으로 완료되었음을 나타냅니다.성공적인 작업 결과를 result 필드에 포함합니다.
    # REVOKED: 작업이 취소되었음을 나타냅니다.
    task = process_video.AsyncResult(task_id)

    if not task.ready() or task.status == 'FAILURE':
        result = None

    else:
        result = task.result

    response = {
        'taskId': task_id,
        'status': task.status,
        'result': result
    }

    return jsonify(response)

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=50001)
