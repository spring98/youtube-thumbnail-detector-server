from utils import downloader, analyzer

if __name__ == '__main__':
    videoId = 'tJGunpmi2wo'

    downloader.Downloader().execute(videoId=videoId)
    video_path = f'assets/{videoId}/video.mp4'
    target_image_path = f'assets/{videoId}/thumbnail.jpg'

    analyzer = analyzer.ImageAnalyzer(video_path=video_path, target_image_path=target_image_path)
    best_frame, best_frame_time = analyzer.find_most_similar_frame()

    if best_frame is not None and best_frame_time is not None:
        print(f"Best frame time: {best_frame_time} seconds")
        analyzer.display_comparison(best_frame)
    else:
        print("Could not find the best frame.")
