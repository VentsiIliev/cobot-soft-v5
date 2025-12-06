#!/usr/bin/env python3
"""
Camera/OpenCV inspector: tries to open video devices with multiple backends,
prints OpenCV build info, v4l2 capabilities and attempts to capture frames.
Usage: python3 inspect_camera_opencv.py
"""
import cv2
import sys
import time
import glob
import subprocess

print('\n==== OpenCV build info (short) ====')
try:
    info = cv2.getBuildInformation()
    for line in info.splitlines():
        if 'Video I/O:' in line or 'V4L' in line or 'FFMPEG' in line or 'GStreamer' in line:
            print(line)
    # print a trimmed excerpt
    print('\n(Full build info can be inspected by setting VERBOSE)
')
except Exception as e:
    print('Failed to get OpenCV build info:', e)

# helper to run a shell command and return output
def run(cmd):
    try:
        res = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
        return res.returncode, res.stdout + res.stderr
    except Exception as e:
        return -1, str(e)

print('\n==== System helpers ===')
rc, out = run('ls -la /dev/video* 2>/dev/null || true')
print(out.strip())
rc, out = run('ps aux | grep -E "(python|cheese|guvcview|mjpg|ffplay|vlc)" | grep -v grep || true')
print('Possible video-using processes:')
print(out.strip())
rc, out = run('lsof /dev/video* 2>/dev/null || true')
print('\nlsof on /dev/video*:')
print(out.strip())

# v4l2-ctl quick
rc, out = run('v4l2-ctl --list-devices 2>/dev/null || true')
print('\n=== v4l2-ctl --list-devices ===')
print(out.strip())

# Candidate device indexes and paths
device_paths = sorted(glob.glob('/dev/video*'))
indexes = list(range(0, 6))

backends = []
# map common cv2 backend constants if present
for name, val in [('CAP_V4L2', getattr(cv2, 'CAP_V4L2', None)),
                  ('CAP_GSTREAMER', getattr(cv2, 'CAP_GSTREAMER', None)),
                  ('CAP_FFMPEG', getattr(cv2, 'CAP_FFMPEG', None)),
                  ('CAP_ANY', getattr(cv2, 'CAP_ANY', None)),
                  ('CAP_V4L', getattr(cv2, 'CAP_V4L', None))]:
    if val is not None:
        backends.append((name, val))

print('\nAvailable OpenCV backends to test:')
for n,v in backends:
    print(f' - {n} = {v}')

# Test opening by index using different backends
results = []

def test_open(source, api=None, set_mjpg=False, width=1280, height=720, fps=30):
    descr = f"src={source} api={'None' if api is None else api} mjpg={'yes' if set_mjpg else 'no'} {width}x{height}@{fps}"
    try:
        if api is None:
            cap = cv2.VideoCapture(source)
        else:
            cap = cv2.VideoCapture(source, api)
    except Exception as e:
        print(descr, '-> exception on VideoCapture()', e)
        return descr, False, str(e)
    opened = cap.isOpened()
    if not opened:
        # ensure release
        try: cap.release()
        except: pass
        return descr, False, 'not opened'

    # print some reported properties
    w = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
    h = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
    f = cap.get(cv2.CAP_PROP_FPS)
    fourcc = int(cap.get(cv2.CAP_PROP_FOURCC) or 0)

    # try to set MJPG
    if set_mjpg:
        try:
            cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('M','J','P','G'))
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
            cap.set(cv2.CAP_PROP_FPS, fps)
            time.sleep(0.05)
        except Exception as e:
            print('failed to set props', e)

    # attempt to capture a few frames
    t0 = time.time()
    n = 0
    for i in range(20):
        ret, frm = cap.read()
        if not ret:
            break
        n += 1
    dt = time.time() - t0
    if n>0 and dt>0:
        measured_fps = n/dt
    else:
        measured_fps = 0.0

    info = {
        'w': w, 'h': h, 'fps_reported': f, 'fourcc': fourcc,
        'captured': n, 'measured_fps': measured_fps
    }
    cap.release()
    return descr, True, info

print('\n==== Trying device indexes (0..5) with backends ===')
for idx in indexes:
    for name, api in backends:
        desc, ok, info = test_open(idx, api=api, set_mjpg=True, width=1280, height=720, fps=30)
        print(desc, '->', 'OK' if ok else 'FAILED', info)

print('\n==== Trying device paths (/dev/video*) with CAP_V4L2 and CAP_ANY ===')
for d in device_paths:
    for name, api in [('CAP_V4L2', getattr(cv2, 'CAP_V4L2', None)), ('CAP_ANY', getattr(cv2, 'CAP_ANY', None))]:
        if api is None:
            continue
        desc, ok, info = test_open(d, api=api, set_mjpg=True, width=1280, height=720, fps=30)
        print(desc, '->', 'OK' if ok else 'FAILED', info)

print('\n==== Done ===')

