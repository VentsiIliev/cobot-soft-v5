import requests
import cv2
import numpy as np
from io import BytesIO

class RemoteCamera:
    """
    A camera wrapper that mimics the interface of the local Camera class,
    but fetches frames from a remote server via HTTP.
    """

    def __init__(self, server_url: str, width=1280, height=720, fps=30):
        """
        Args:
            server_url (str): Base URL of the server, e.g. "http://192.168.1.100:5000"
            width (int): desired width (optional, for compatibility)
            height (int): desired height (optional, for compatibility)
            fps (float): desired FPS (optional, for compatibility)
        """
        self.server_url = server_url.rstrip("/")
        self.video_feed_url = f"{self.server_url}/video_feed"
        self.width = width
        self.height = height
        self.fps = fps
        self.frame = None

        # MJPEG parsing state
        self.boundary = b"--frame"
        self.buffer = b""

    def _fetch_mjpeg(self):
        """
        Generator to fetch MJPEG frames from the server
        """
        try:
            r = requests.get(self.video_feed_url, stream=True, timeout=5.0)
            r.raise_for_status()
            for chunk in r.iter_content(chunk_size=1024):
                if chunk:
                    self.buffer += chunk
                    while True:
                        start = self.buffer.find(b'\xff\xd8')
                        end = self.buffer.find(b'\xff\xd9')
                        if start != -1 and end != -1 and end > start:
                            jpg = self.buffer[start:end + 2]
                            self.buffer = self.buffer[end + 2:]
                            frame = cv2.imdecode(np.frombuffer(jpg, dtype=np.uint8), cv2.IMREAD_COLOR)
                            if frame is not None:
                                yield frame
                        else:
                            break
        except Exception as e:
            print(f"[ERROR] RemoteCamera MJPEG fetch failed: {e}")
            return

    def capture(self, grab_only=False, timeout=1.0):
        """
        Fetch a single frame from the remote server
        """
        try:
            gen = self._fetch_mjpeg()
            frame = next(gen)
            return frame
        except StopIteration:
            return None
        except Exception:
            return None

    def isOpened(self):
        # Assume always true if server URL is reachable
        try:
            r = requests.get(self.server_url, timeout=2.0)
            return r.status_code == 200
        except:
            return False

    def close(self):
        # Nothing to close for HTTP
        pass

    # Compatibility methods
    def stopCapture(self):
        self.close()

    def get_properties(self):
        return {'width': self.width, 'height': self.height, 'fps': self.fps}

    def set_resolution(self, width, height):
        self.width = width
        self.height = height

    def set_fps(self, fps):
        self.fps = fps

    def set_fourcc(self, fourcc_str):
        pass

    def set_auto_exposure(self, enabled: bool):
        pass

    def get_auto_exposure(self):
        return None

    def set_exposure(self, exposure_value: float):
        pass

    def stop_stream(self):
        pass

    def start_stream(self):
        pass


