import cv2 as cv
import click
import numpy as np
import os
import secrets

DEFAULT_TIMEOUT = 100
PICTURE_EXTENSIONS = ('.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.webp')


class Video:
    FRAME_RATE = 30

    def __init__(self, mp4_path, play_frames):
        self.play_frames = play_frames
        self.capture = cv.VideoCapture(mp4_path)
        self.frame_count = self.capture.get(cv.CAP_PROP_FRAME_COUNT)
        self.reset()

    def should_stop(self):
        timed_out = self.counter == self.play_frames
        eof = self.counter == self.frame_count
        return timed_out or eof

    def reset(self):
        self.counter = 0
        if self.frame_count < self.play_frames:
            self.capture.set(cv.CAP_PROP_POS_FRAMES, 0)
        else:
            pos = secrets.randbelow(int(self.frame_count - self.play_frames))
            self.capture.set(cv.CAP_PROP_POS_FRAMES, pos)

    def grab(self):
        self.counter += 1
        return self.capture.read()

    def release(self):
        self.capture.release()


class Picture:
    def __init__(self, image_path, play_frames):
        self.play_frames = play_frames
        self.frame = cv.imread(image_path)
        if self.frame is None:
            raise ValueError(f"Could not load image: {image_path}")
        self.counter = 0

    def should_stop(self):
        return self.counter >= self.play_frames

    def reset(self):
        self.counter = 0

    def grab(self):
        self.counter += 1
        return (True, self.frame)

    def release(self):
        pass


def load_videos(timeout):
    videos = []
    videos_dir = os.path.join(os.getcwd(), 'videos')
    for file in os.listdir(videos_dir):
        if file.endswith('.mp4'):
            videos.append(Video(os.path.join('videos', file), timeout))
    return videos


def load_pictures(timeout):
    pictures = []
    pictures_dir = os.path.join(os.getcwd(), 'pictures')
    for file in os.listdir(pictures_dir):
        if file.lower().endswith(PICTURE_EXTENSIONS):
            pictures.append(Picture(os.path.join('pictures', file), timeout))
    return pictures


def fit_frame(frame, win_w, win_h):
    h, w = frame.shape[:2]
    scale = min(win_w / w, win_h / h)
    new_w = int(w * scale)
    new_h = int(h * scale)
    resized = cv.resize(frame, dsize=(new_w, new_h))
    canvas = np.zeros((win_h, win_w, 3), dtype=np.uint8)
    x_offset = (win_w - new_w) // 2
    y_offset = (win_h - new_h) // 2
    canvas[y_offset:y_offset + new_h, x_offset:x_offset + new_w] = resized
    return canvas


@click.command()
@click.option("--timeout", default=DEFAULT_TIMEOUT, type=int, help="Number of frames to play per clip before switching (default: 100).")
@click.option("--video-timeout", default=None, type=int, help="Number of frames to play per video clip before switching (defaults to --timeout).")
@click.option("--picture-timeout", default=None, type=int, help="Number of frames to display per picture before switching (defaults to --timeout).")
@click.option("--pictures/--no-pictures", default=None, help="Enable or disable pictures (auto-detects pictures/ directory by default).")
@click.option("--videos/--no-videos", default=None, help="Enable or disable videos (auto-detects videos/ directory by default).")
def main(timeout, video_timeout, picture_timeout, pictures, videos):
    if video_timeout is None:
        video_timeout = timeout
    if picture_timeout is None:
        picture_timeout = timeout

    if pictures is None:
        pictures = os.path.isdir(os.path.join(os.getcwd(), 'pictures'))
    if videos is None:
        videos = os.path.isdir(os.path.join(os.getcwd(), 'videos'))

    video_list = load_videos(video_timeout) if videos else []
    picture_list = load_pictures(picture_timeout) if pictures else []
    media = video_list + picture_list

    if len(media) == 0:
        print('no media found.')
        exit(1)

    def get_random_media_index(pool, current=-1):
        if len(pool) == 1:
            return 0
        new_index = -1
        while new_index == current:
            new_index = secrets.randbelow(len(pool))
        return new_index

    def pick_next(current_index, current_pool):
        if video_list and picture_list:
            if secrets.randbelow(2) == 0:
                pool = video_list
            else:
                pool = picture_list
        elif video_list:
            pool = video_list
        else:
            pool = picture_list

        if pool is current_pool:
            idx = get_random_media_index(pool, current_index)
        else:
            idx = get_random_media_index(pool)
        return idx, pool

    current_index, current_pool = pick_next(-1, None)
    current_media = current_pool[current_index]

    while True:
        ret, frame = current_media.grab()
        if not ret:
            print("Can't recieve frame. Exiting")
            break

        display = fit_frame(frame, 1777, 1000)
        cv.imshow('stream', display)

        if cv.waitKey(1000 // Video.FRAME_RATE) == ord('q'):
            break

        if current_media.should_stop():
            current_media.reset()
            current_index, current_pool = pick_next(current_index, current_pool)
            current_media = current_pool[current_index]

    for m in media:
        m.release()
    cv.destroyAllWindows()
