"""Read frames and export clips.

All times in this module are seconds from the first video frame (0 = start of video),
regardless of the timestamp the container starts with.
"""

import re
import shutil
import subprocess
import threading
from dataclasses import dataclass

import av

# Tolerance for rounding errors when comparing frame timestamps
EPS = 1e-6
# Margin around frame timestamps when exporting. Well below one frame (8 ms at 120 fps).
EXPORT_MARGIN = 0.001


@dataclass
class Frame:
    time: float
    image: object  # PIL.Image.Image


class VideoReader:
    """Frame-accurate access to the first video stream of a file. Not thread-safe."""

    def __init__(self, path):
        self.path = path
        self.container = av.open(path)
        self.stream = self.container.streams.video[0]
        self.stream.thread_type = 'AUTO'
        tb = self.stream.time_base
        self.offset = float(self.stream.start_time * tb) if self.stream.start_time is not None else 0.0
        if self.stream.duration is not None:
            self.duration = float(self.stream.duration * tb)
        elif self.container.duration is not None:
            self.duration = self.container.duration / av.time_base - self.offset
        else:
            raise ValueError('Cannot determine the video duration.')
        self.width = self.stream.codec_context.width
        self.height = self.stream.codec_context.height

    def close(self):
        self.container.close()

    def time_of(self, frame):
        return float(frame.time) - self.offset

    def frames_from(self, t):
        """Yield frames in presentation order, starting at the last frame with time <= t (if any)."""
        back = 0.0
        while True:
            target = max(t - back, 0.0)
            pts = int((target + self.offset) / self.stream.time_base)
            self.container.seek(pts, stream=self.stream, backward=True)
            frames = (f for f in self.container.decode(self.stream) if f.time is not None)
            first = next(frames, None)
            if first is None:
                return
            # Some containers seek past the target. In that case retry further back.
            if self.time_of(first) <= t + EPS or target == 0.0:
                yield first
                yield from frames
                return
            back = back * 2 or 0.5

    def first_frame_at(self, t):
        """First frame with time >= t, or the last frame of the video."""
        last = None
        for f in self.frames_from(t):
            last = f
            if self.time_of(f) >= t - EPS:
                break
        return last

    def last_frame_before(self, t):
        """Last frame with time < t."""
        last = None
        for f in self.frames_from(t - EXPORT_MARGIN):
            if self.time_of(f) >= t - EPS:
                break
            last = f
        return last

    def to_frame(self, av_frame, max_size=None):
        """Convert a PyAV frame to an image, optionally scaled down to max_size (width, height)."""
        kwargs = {}
        if max_size:
            scale = min(max_size[0] / av_frame.width, max_size[1] / av_frame.height)
            if scale < 1:
                kwargs = {'width': max(2, round(av_frame.width * scale)), 'height': max(2, round(av_frame.height * scale))}
        return Frame(self.time_of(av_frame), av_frame.to_image(**kwargs))

    def resolve_range(self, start, end):
        """Times of the first and last frame in the range [start, end)."""
        first = self.first_frame_at(start)
        last = self.last_frame_before(end)
        if first is None or last is None or self.time_of(last) < self.time_of(first):
            raise ValueError('There is no frame in the selected range.')
        return self.time_of(first), self.time_of(last)


def frame_times(path):
    """Sorted times of all video frames. Only reads packets, does not decode."""
    with av.open(path) as container:
        stream = container.streams.video[0]
        tb = stream.time_base
        offset = stream.start_time if stream.start_time is not None else 0
        times = [float((p.pts - offset) * tb) for p in container.demux(stream) if p.pts is not None and p.size]
    # Drop frames before the start of the video that the decoder discards (edit lists)
    return sorted(t for t in times if t >= -EPS)


def ffmpeg_exe():
    path = shutil.which('ffmpeg')
    if path:
        return path
    import imageio_ffmpeg

    return imageio_ffmpeg.get_ffmpeg_exe()


def export_clip(path, output, start, end, on_progress=None):
    """Export the frames in the range [start, end) as MP4 (H.264/AAC).

    The video is re-encoded so the cut is frame-accurate instead of snapping to keyframes.
    Returns the times of the first and last exported frame.
    """
    reader = VideoReader(path)
    try:
        first, last = reader.resolve_range(start, end)
        offset = reader.offset
    finally:
        reader.close()

    # Cut just before the first and just after the last frame so rounding never drops a frame
    ss = max(first + offset - EXPORT_MARGIN, 0.0)
    duration = last + offset + EXPORT_MARGIN - ss
    cmd = [
        ffmpeg_exe(), '-y', '-hide_banner', '-nostats',
        '-ss', f'{ss:.6f}',
        '-i', path,
        '-t', f'{duration:.6f}',
        '-map', '0:v:0',
        '-map', '0:a:0?',
        '-c:v', 'libx264',
        '-preset', 'veryfast',
        '-crf', '18',
        '-pix_fmt', 'yuv420p',
        '-c:a', 'aac',
        '-b:a', '192k',
        '-movflags', '+faststart',
        '-progress', 'pipe:1',
        output,
    ]
    proc = subprocess.Popen(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, errors='replace',
        creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0),
    )
    stderr_lines = []
    drain = threading.Thread(target=lambda: stderr_lines.extend(proc.stderr), daemon=True)
    drain.start()
    for line in proc.stdout:
        m = re.match(r'out_time_us=(\d+)', line)
        if m and on_progress:
            on_progress(min(int(m.group(1)) / 1e6 / duration, 1.0))
    drain.join()
    stderr = ''.join(stderr_lines[-30:])
    if proc.wait() != 0:
        raise RuntimeError(f'ffmpeg failed:\n{stderr.strip()}')
    return first, last
