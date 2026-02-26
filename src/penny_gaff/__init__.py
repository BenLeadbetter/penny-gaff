import cv2 as cv
import click
import os
import secrets

DEFAULT_TIMEOUT = 100


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


@click.command()
@click.option("--timeout", default=DEFAULT_TIMEOUT, type=int, help="Number of frames to play per clip before switching (default: 100).")
def main(timeout):
    videos = []
    for file in os.listdir(str(os.getcwd() + '/videos')):
        if file.endswith('.mp4'):
            videos.append(Video('videos/{}'.format(file), timeout))

    if len(videos) == 0:
        print('no mp4 videos found.')
        exit(1)

    def get_random_video_index(current=-1):
        if len(videos) == 1:
            return 0
        new_index = -1
        while new_index == current:
            new_index = secrets.randbelow(len(videos))
        return new_index

    video_index = get_random_video_index()
    video = videos[video_index]

    while True:
        ret, frame = video.grab()
        if not ret:
            print("Can't recieve frame. Exiting")
            break

        resized = cv.resize(frame, dsize=(1777, 1000))
        cv.imshow('stream', resized)

        if cv.waitKey(1000 // Video.FRAME_RATE) == ord('q'):
            break

        if video.should_stop():
            video.reset()
            video_index = get_random_video_index(video_index)
            video = videos[video_index]

    for v in videos:
        v.release()
    cv.destroyAllWindows()
