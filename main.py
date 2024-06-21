# from utils import downloader, analyzer
#
# if __name__ == '__main__':
#     videoId = 'tJGunpmi2wo'
#
#     downloader.Downloader().execute(videoId=videoId)
#     video_path = f'assets/{videoId}/video.mp4'
#     target_image_path = f'assets/{videoId}/thumbnail.jpg'
#
#     analyzer = analyzer.ImageAnalyzer(video_path=video_path, target_image_path=target_image_path)
#     best_frame, best_frame_time = analyzer.find_most_similar_frame()
#
#     if best_frame is not None and best_frame_time is not None:
#         print(f"Best frame time: {best_frame_time} seconds")
#         analyzer.display_comparison(best_frame)
#     else:
#         print("Could not find the best frame.")

from flask import Flask, request, jsonify
from utils import downloader, analyzer

app = Flask(__name__)

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

        if best_frame is not None and best_frame_time is not None:
            result = {
                'videoId': videoId,
                'best_frame_time': best_frame_time,
                'message': 'Best frame found successfully'
            }
        else:
            result = {
                'videoId': videoId,
                'message': 'Could not find the best frame'
            }
        return jsonify(result), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=50001)
