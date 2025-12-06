"""
Camera wrapper with backend selection, device path/index support and
explicit configuration for FOURCC, resolution and fps.

Backwards compatible constructor: Camera(cameraIndex, width, height)
New optional keyword params (use by name):
  - device: int or str (index or path). If provided it overrides cameraIndex.
  - backend: cv2 backend constant (e.g. cv2.CAP_V4L2) or name string ('V4L2','ANY')
  - fourcc: 4-char string like 'MJPG' to force pixel format
  - fps: desired capture fps (float)
  - open_timeout: seconds to keep trying to open the device
  - retries: number of retries when reading frames

Public methods:
  - capture(grab_only=False): return frame (or None)
  - isOpened(), close(), get_properties(), set_resolution(), set_fps(), set_fourcc()
"""
import time
import platform

import cv2


class Camera:
    def __init__(self, cameraIndex=0, width=1280, height=720, *,
                 device=None, backend=None, fourcc=None, fps=None,
                 open_timeout=5.0, retries=3, mjpg_preferred=True, verbose_ae=False):
        # Backwards-compatible behavior
        if device is None:
            self.device = cameraIndex
        else:
            self.device = device

        self.width = int(width)
        self.height = int(height)
        self.requested_fps = float(fps) if fps is not None else None
        self.requested_fourcc = (fourcc if isinstance(fourcc, str) else None)
        self.open_timeout = float(open_timeout)
        self.retries = int(retries)
        self.mjpg_preferred = bool(mjpg_preferred)
        # If true, set_auto_exposure will print each candidate tried
        self.verbose_ae = bool(verbose_ae)

        # Resolve backend constant if provided as name
        self.backend = None
        if backend is not None:
            if isinstance(backend, str):
                name = backend.upper()
                if hasattr(cv2, f'CAP_{name}'):
                    self.backend = getattr(cv2, f'CAP_{name}')
            elif isinstance(backend, int):
                self.backend = backend

        self.cap = None
        self.open_start_time = None
        self._init_capture()

    def _resolve_backend_for_platform(self):
        if self.backend is not None:
            return self.backend
        if platform.system() == 'Windows' and hasattr(cv2, 'CAP_DSHOW'):
            return cv2.CAP_DSHOW
        if platform.system() == 'Linux' and hasattr(cv2, 'CAP_V4L2'):
            return cv2.CAP_V4L2
        return getattr(cv2, 'CAP_ANY', 0)

    def _attempt_open(self, device, api):
        try:
            cap = cv2.VideoCapture(device, api) if api is not None else cv2.VideoCapture(device)
            if cap is None:
                return None
            if cap.isOpened():
                return cap
            try:
                cap.release()
            except Exception:
                pass
            return None
        except Exception:
            return None

    def _init_capture(self):
        api = self._resolve_backend_for_platform()
        self.open_start_time = time.time()
        deadline = self.open_start_time + self.open_timeout

        tries = []
        if isinstance(self.device, int) or (isinstance(self.device, str) and str(self.device).isdigit()):
            tries.append(int(self.device))
        elif isinstance(self.device, str):
            tries.append(self.device)
        else:
            tries.extend(list(range(0, 4)))

        apis_to_try = [api]
        any_api = getattr(cv2, 'CAP_ANY', 0)
        if api != any_api:
            apis_to_try.append(any_api)

        for attempt_target in tries:
            for a in apis_to_try:
                while time.time() <= deadline:
                    cap = self._attempt_open(attempt_target, a)
                    if cap is not None:
                        self.cap = cap
                        self._configure_capture()
                        return
                    time.sleep(0.1)
                    if time.time() > deadline:
                        break
        # failed to open within timeout

    def _configure_capture(self):
        # Set FOURCC first if requested
        if self.requested_fourcc is not None:
            try:
                fourcc_int = cv2.VideoWriter_fourcc(*self.requested_fourcc)
                self.cap.set(cv2.CAP_PROP_FOURCC, fourcc_int)
            except Exception:
                pass
        else:
            if self.mjpg_preferred:
                try:
                    self.cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('M', 'J', 'P', 'G'))
                except Exception:
                    pass

        # Set resolution
        try:
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, int(self.width))
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, int(self.height))
        except Exception:
            pass

        # Set fps if requested
        if self.requested_fps is not None:
            try:
                self.cap.set(cv2.CAP_PROP_FPS, float(self.requested_fps))
            except Exception:
                pass

        time.sleep(0.05)

    # Public API
    def isOpened(self):
        return (self.cap is not None) and self.cap.isOpened()

    def get_properties(self):
        if not self.isOpened():
            return {}
        return {
            'width': int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
            'height': int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
            'fps': float(self.cap.get(cv2.CAP_PROP_FPS)),
            'fourcc': int(self.cap.get(cv2.CAP_PROP_FOURCC)),
            'backend_name': (self.cap.getBackendName() if hasattr(self.cap, 'getBackendName') else None)
        }

    def set_resolution(self, width, height):
        if not self.isOpened():
            raise RuntimeError('Camera not opened')
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, int(width))
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, int(height))
        time.sleep(0.02)

    def set_fps(self, fps):
        if not self.isOpened():
            raise RuntimeError('Camera not opened')
        self.cap.set(cv2.CAP_PROP_FPS, float(fps))
        time.sleep(0.02)

    def set_fourcc(self, fourcc_str):
        if not self.isOpened():
            raise RuntimeError('Camera not opened')
        fourcc_int = cv2.VideoWriter_fourcc(*fourcc_str)
        self.cap.set(cv2.CAP_PROP_FOURCC, fourcc_int)
        time.sleep(0.02)

    def set_auto_exposure(self, enabled: bool):
        """
        Enable or disable camera auto exposure.

        Note: different backends/drivers expect different values for
        cv2.CAP_PROP_AUTO_EXPOSURE; for V4L2 the menu values are typically
        1 = Manual Mode, 3 = Aperture Priority (auto). This method tries
        a sequence of likely values to flip the mode and returns the
        resulting property value (or None if not available).
        """
        if not self.isOpened():
            raise RuntimeError('Camera not opened')

        # Candidate values to try (ordered by most likely for common drivers)
        if enabled:
            candidates = (3.0, 1.0, 0.75, 0.25)
        else:
            candidates = (1.0, 0.25, 0.0, 0.75)

        last_ok = None
        for v in candidates:
            try:
                if self.verbose_ae:
                    print(f"[AE] trying value: {v}")
                ok = self.cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, float(v))
                if ok:
                    last_ok = v
                    # small pause to let driver apply
                    time.sleep(0.02)
                    if self.verbose_ae:
                        print(f"[AE] accepted value: {v}")
                    break
                else:
                    if self.verbose_ae:
                        print(f"[AE] driver rejected value: {v}")
            except Exception:
                if self.verbose_ae:
                    print(f"[AE] exception trying value: {v}")
                continue

        # Return current readback if available
        try:
            return self.cap.get(cv2.CAP_PROP_AUTO_EXPOSURE)
        except Exception:
            return last_ok

    def get_auto_exposure(self):
        """Return the current AUTO_EXPOSURE property value (or None)."""
        if not self.isOpened():
            return None
        try:
            return self.cap.get(cv2.CAP_PROP_AUTO_EXPOSURE)
        except Exception:
            return None

    def set_exposure(self, exposure_value: float):
        """Set an absolute exposure value (driver-dependent units)."""
        if not self.isOpened():
            raise RuntimeError('Camera not opened')
        try:
            self.cap.set(cv2.CAP_PROP_EXPOSURE, float(exposure_value))
            time.sleep(0.02)
        except Exception:
            pass

    def capture(self, grab_only=False, timeout=1.0):
        if not self.isOpened():
            return None

        start = time.time()
        while True:
            if grab_only:
                try:
                    ok = self.cap.grab()
                    if not ok and (time.time() - start) > timeout:
                        return None
                    if not ok:
                        continue
                    ok, frame = self.cap.retrieve()
                except Exception:
                    return None
            else:
                try:
                    ok, frame = self.cap.read()
                except Exception:
                    return None

            if ok:
                return frame
            if (time.time() - start) > timeout:
                return None

    def close(self):
        if self.cap is not None:
            try:
                self.cap.release()
            except Exception:
                pass
        self.cap = None

    # Backward-compatible aliases
    def stopCapture(self):
        self.close()


if __name__ == '__main__':
    """Minimal runnable demo (no argparse).
    Usage: python3 src/libs/plvision/PLVision/Camera.py
    Optional env var CAM_DEMO_DURATION (seconds) to auto-stop the demo.
    Keys: q=quit, t=toggle AE, +/-, r=cycle res, f=cycle fps, m=toggle MJPG, p=print props, h=help
    """
    import os
    import sys

    # Demo configuration (change here or set CAM_DEMO_DURATION env var)
    default_index = 0
    default_width = 1280
    default_height = 720
    default_fps = 60
    mjpg_pref = True

    try:
        duration = float(os.getenv('CAM_DEMO_DURATION', '0'))
    except Exception:
        duration = 0.0

    cam = Camera(cameraIndex=default_index, width=default_width, height=default_height,
                 fps=default_fps, mjpg_preferred=mjpg_pref)

    print('Opened:', cam.isOpened())
    print('Properties:', cam.get_properties())
    if not cam.isOpened():
        print('Failed to open camera - run collect_camera_info.sh for diagnostics')
        sys.exit(2)

    def print_help():
        print('\nInteractive keys:')
        print('  q : quit')
        print('  t : toggle auto-exposure (on/off)')
        print('  + / = : increase exposure')
        print('  - / _ : decrease exposure')
        print('  r : cycle resolution (1920x1080,1280x720,640x480)')
        print('  f : cycle fps (60,30,15,5)')
        print('  m : toggle MJPG preference')
        print('  p : print properties')
        print('  h : print this help')

    print_help()

    start_time = time.time()
    frames = 0
    fps_sum = 0.0
    last_time = None
    last_key_time = 0.0

    try:
        while True:
            if duration > 0 and (time.time() - start_time) >= duration:
                break

            frame = cam.capture(grab_only=False, timeout=1.0)
            if frame is None:
                # failed to grab -- try again
                time.sleep(0.01)
                continue

            frames += 1
            now = time.time()
            if last_time is None:
                inst_fps = 0.0
            else:
                inst_fps = 1.0 / (now - last_time) if (now - last_time) > 0 else 0.0
            last_time = now
            fps_sum += inst_fps

            # overlay info
            props = cam.get_properties()
            try:
                cv2.putText(frame, f"FPS target: {props.get('fps')}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,255,0), 2)
                cv2.putText(frame, f"Inst: {inst_fps:.2f} Avg: {(fps_sum/frames if frames>0 else 0.0):.2f}", (10,70), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,255,255), 2)
            except Exception:
                pass

            cv2.imshow('Camera Demo', frame)

            key = cv2.waitKey(1) & 0xFF
            now_key = time.time()
            # debounce quick repeats (0.15s)
            if (now_key - last_key_time) < 0.15 and key != 255:
                continue
            if key != 255:
                last_key_time = now_key
                if key == ord('q'):
                    break
                if key == ord('p'):
                    print('Properties:', cam.get_properties())
                elif key == ord('h'):
                    print_help()
                elif key == ord('t'):
                    ae = cam.get_auto_exposure()
                    try:
                        ae_on = (float(ae) == 3.0)
                    except Exception:
                        ae_on = bool(ae)
                    cam.set_auto_exposure(not ae_on)
                    print('AE toggled ->', cam.get_auto_exposure())
                elif key in (ord('+'), ord('=')):
                    try:
                        cur = cam.cap.get(cv2.CAP_PROP_EXPOSURE)
                        cur = float(cur) if cur is not None else 0.0
                        cam.set_exposure(cur + 10)
                        print('Exposure ->', cam.cap.get(cv2.CAP_PROP_EXPOSURE))
                    except Exception:
                        pass
                elif key in (ord('-'), ord('_')):
                    try:
                        cur = cam.cap.get(cv2.CAP_PROP_EXPOSURE)
                        cur = float(cur) if cur is not None else 0.0
                        cam.set_exposure(max(0.0, cur - 10))
                        print('Exposure ->', cam.cap.get(cv2.CAP_PROP_EXPOSURE))
                    except Exception:
                        pass
                elif key == ord('r'):
                    presets = [(1920,1080),(1280,720),(640,480)]
                    curw = cam.get_properties().get('width')
                    curh = cam.get_properties().get('height')
                    try:
                        idx = presets.index((curw,curh))
                        idx = (idx + 1) % len(presets)
                    except Exception:
                        idx = 0
                    w,h = presets[idx]
                    cam.set_resolution(w,h)
                    print('Resolution ->', cam.get_properties())
                elif key == ord('f'):
                    fps_presets = [60,30,15,5]
                    curf = cam.get_properties().get('fps')
                    try:
                        idx = fps_presets.index(int(round(curf)))
                        idx = (idx + 1) % len(fps_presets)
                    except Exception:
                        idx = 0
                    cam.set_fps(fps_presets[idx])
                    print('FPS ->', cam.get_properties())
                elif key == ord('m'):
                    cam.mjpg_preferred = not cam.mjpg_preferred
                    if cam.mjpg_preferred:
                        try:
                            cam.set_fourcc('MJPG')
                        except Exception:
                            pass
                    print('MJPG preferred ->', cam.mjpg_preferred)

    except KeyboardInterrupt:
        print('\nInterrupted by user')
    finally:
        cam.close()
        try:
            cv2.destroyAllWindows()
        except Exception:
            pass

    avg_fps = (fps_sum / frames) if frames > 0 else 0.0
    print(f"Finished. Captured frames: {frames}, Avg FPS: {avg_fps:.2f}")
