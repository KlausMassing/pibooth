# -*- coding: utf-8 -*-

from io import BytesIO
import time
import subprocess
from PIL import Image

try:
    from picamera2 import Picamera2, Preview
except ImportError:
    Picamera2 = None  # picamera2 is optional

from pibooth.language import get_translated_text
from pibooth.camera.base import BaseCamera


def get_rpi_camera_proxy(port=None):
    """Return camera proxy if a Raspberry Pi compatible camera is found."""
    if not Picamera2:
        return None
    try:
        process = subprocess.Popen(['vcgencmd', 'get_camera'],
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, _ = process.communicate()
        if stdout and 'detected=1' in stdout.decode('utf-8'):
            return Picamera2()
    except OSError:
        pass
    return None


class RpiCamera(BaseCamera):
    IMAGE_EFFECTS = []  # picamera2 supports different controls, not named effects

    def _specific_initialization(self):
        self._cam.configure(self._cam.create_still_configuration(
            main={"size": self.resolution},
            transform={"vflip": False, "hflip": self.capture_flip}
        ))
        self._cam.set_controls({
            "AnalogueGain": 1.0,
            "AwbMode": "auto",
            "ExposureTime": 10000,
        })
        self._cam.start()

    def _show_overlay(self, text, alpha):
        # Overlay support must be implemented via OpenCV or GUI lib if needed
        pass

    def _hide_overlay(self):
        pass

    def _post_process_capture(self, capture_data):
        capture_data.seek(0)
        return Image.open(capture_data)

    def preview(self, window, flip=True):
        # picamera2 uses Preview class, or can be displayed via OpenCV
        self._cam.start_preview(Preview.QT)

    def preview_countdown(self, timeout, alpha=60):
        if timeout < 1:
            raise ValueError("Start time shall be greater than 0")
        for t in range(timeout, 0, -1):
            self._show_overlay(t, alpha)
            time.sleep(1)
            self._hide_overlay()
        self._show_overlay(get_translated_text('smile'), alpha)

    def preview_wait(self, timeout, alpha=60):
        time.sleep(timeout)
        self._show_overlay(get_translated_text('smile'), alpha)

    def stop_preview(self):
        self._cam.stop_preview()
        self._window = None

    def capture(self, effect=None):
        # picamera2 does not support traditional image effects
        stream = BytesIO()
        array = self._cam.capture_array()
        Image.fromarray(array).save(stream, format='jpeg')
        self._captures.append(stream)
        self._hide_overlay()

    def quit(self):
        self._cam.stop()
        self._cam.close()
