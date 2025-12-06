#!/usr/bin/env python3
"""
Robust camera open tester.
- Tries indexes 0..5 and /dev/video* paths
- Tests OpenCV backends (CAP_V4L2, CAP_ANY)
- Sets MJPG, resolution and fps, measures capture FPS
- Retries if device busy
Usage: python3 camera_open_test.py
"""
import cv2, time, glob

BACKENDS = []
for name, val in [('CAP_V4L2', getattr(cv2, 'CAP_V4L2', None)),
                  ('CAP_ANY', getattr(cv2, 'CAP_ANY', None))]:
    if val is not None:
        BACKENDS.append((name, val))

DEVICE_PATHS = sorted(glob.glob('/dev/video*'))
INDEXES = list(range(0, 6))

def try_open(source, api=None, width=1280, height=720, fps=30, retries=3, delay=0.5):
    last_err = None
    for attempt in range(1, retries+1):
        try:
            cap = cv2.VideoCapture(source) if api is None else cv2.VideoCapture(source, api)
        except Exception as e:
            last_err = f'Exception on VideoCapture: {e}'
            time.sleep(delay)
            continue
        if not cap.isOpened():
            last_err = 'not opened'
            try: cap.release()
            except: pass
            time.sleep(delay)
            continue

        # report reported properties
        w = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
        h = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
        f = cap.get(cv2.CAP_PROP_FPS)
        fourcc = int(cap.get(cv2.CAP_PROP_FOURCC) or 0)

        # try to set MJPG and dims
        try:
            cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('M','J','P','G'))
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
            cap.set(cv2.CAP_PROP_FPS, fps)
            time.sleep(0.05)
        except Exception as e:
            pass

        # capture a few frames
        t0 = time.time(); n = 0
        for _ in range(30):
            ret, frm = cap.read()
            if not ret:
                break
            n += 1
        dt = time.time() - t0
        cap.release()
        measured = (n/dt) if dt>0 and n>0 else 0.0
        return True, {
            'attempt': attempt,
            'reported_w': w, 'reported_h': h, 'reported_fps': f, 'reported_fourcc': fourcc,
            'captured_frames': n, 'measured_fps': measured
        }
    return False, {'error': last_err}

if __name__ == '__main__':
    print('OpenCV version:', cv2.__version__)
    print('Backends to test:', BACKENDS)
    print('\n== Try indexes ==')
    for idx in INDEXES:
        for name, api in BACKENDS:
            ok, info = try_open(idx, api=api, width=1280, height=720, fps=30, retries=2)
            print(f'Index {idx} via {name}:', 'OK' if ok else 'FAILED', info)
    print('\n== Try device paths ==')
    for d in DEVICE_PATHS:
        for name, api in BACKENDS:
            ok, info = try_open(d, api=api, width=1280, height=720, fps=30, retries=2)
            print(f'{d} via {name}:', 'OK' if ok else 'FAILED', info)
    print('\nDone')

