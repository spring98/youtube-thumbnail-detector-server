#!/bin/zsh

# logs 폴더 생성
mkdir -p logs

# Gunicorn 서버 실행
echo "Starting Gunicorn..."
nohup gunicorn -w 16 -b 0.0.0.0:50001 app:app > logs/gunicorn.out 2>&1 &
GUNICORN_PID=$!

# Celery 워커 실행
echo "Starting Celery worker..."
#nohup celery -A tasks worker --loglevel=info --pool=gevent --concurrency=16 > logs/celery_worker.out 2>&1 &
nohup celery -A tasks worker --loglevel=info --pool=prefork --concurrency=4 > logs/celery_worker.out 2>&1 &
CELERY_WORKER_PID=$!

# Celery 비트 실행
echo "Starting Celery beat..."
nohup celery -A tasks beat --loglevel=info > logs/celery_beat.out 2>&1 &
CELERY_BEAT_PID=$!

# 모든 프로세스가 백그라운드에서 실행되고 있는지 확인
echo "Gunicorn PID: $GUNICORN_PID"
echo "Celery Worker PID: $CELERY_WORKER_PID"
echo "Celery Beat PID: $CELERY_BEAT_PID"

# 종료 처리
cleanup() {
    echo "Stopping Gunicorn..."
    kill $GUNICORN_PID
    echo "Stopping Celery worker..."
    kill $CELERY_WORKER_PID
    echo "Stopping Celery beat..."
    kill $CELERY_BEAT_PID
    exit 0
}

trap cleanup INT TERM

# 프로세스가 실행 중인지 확인
while true; do
    sleep 1
    if ! ps -p $GUNICORN_PID > /dev/null; then
        echo "Gunicorn has stopped."
        cleanup
    fi
    if ! ps -p $CELERY_WORKER_PID > /dev/null; then
        echo "Celery worker has stopped."
        cleanup
    fi
    if ! ps -p $CELERY_BEAT_PID > /dev/null; then
        echo "Celery beat has stopped."
        cleanup
    fi
done