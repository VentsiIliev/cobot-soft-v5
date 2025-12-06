#!/usr/bin/env bash
# Collect camera/device information useful for debugging V4L2/OpenCV issues
# Usage: ./collect_camera_info.sh
set -euo pipefail

echo "== System info =="
uname -a
lsb_release -a 2>/dev/null || true

echo "\n== Kernel messages (recent, filtered for video) =="
dmesg | tail -n 200 | grep -iE "video|uvc|usb|camera|v4l2" || true

echo "\n== /dev/video* devices =="
ls -la /dev/video* 2>/dev/null || echo "(no /dev/video devices found)"

echo "\n== Who can access video devices =="
getent group video || true
id -nG || true

# List processes that might be using a video device
echo "\n== Processes holding /dev/video* =="
if command -v lsof >/dev/null 2>&1; then
  lsof /dev/video* 2>/dev/null || echo "(no processes found or lsof not permitted)"
else
  echo "lsof not installed"
fi

# udev info for each device
echo "\n== udev info for /dev/video* =="
if command -v udevadm >/dev/null 2>&1; then
  for d in /dev/video*; do
    [ -e "$d" ] || continue
    echo "-- $d --"
    udevadm info -q all -n "$d" || true
    echo
  done
else
  echo "udevadm not installed"
fi

# v4l2-ctl info
echo "\n== v4l2-ctl devices/formats =="
if command -v v4l2-ctl >/dev/null 2>&1; then
  v4l2-ctl --list-devices || true
  for d in /dev/video*; do
    [ -e "$d" ] || continue
    echo "\n-- $d --"
    v4l2-ctl -d "$d" --all || true
    v4l2-ctl -d "$d" --list-formats-ext || true
  done
else
  echo "v4l2-ctl not found. On Debian/Ubuntu: sudo apt install v4l-utils"
fi

# ffmpeg probe
echo "\n== ffmpeg probe (formats) =="
if command -v ffmpeg >/dev/null 2>&1; then
  for d in /dev/video*; do
    [ -e "$d" ] || continue
    echo "\n-- $d --"
    # ffmpeg prints format info to stderr
    ffmpeg -f v4l2 -list_formats all -i "$d" 2>&1 | sed -n '1,120p' || true
  done
else
  echo "ffmpeg not installed"
fi

# Try to show permissions and major/minor
echo "\n== Device major/minor and owners =="
for d in /dev/video*; do
  [ -e "$d" ] || continue
  stat -c "%n: %F %a uid=%u gid=%g (%U:%G) dev=%t:%T" "$d" || true
done

# Python/OpenCV quick test (if python3 and OpenCV installed)
echo "\n== Quick OpenCV test (tries to open devices and grab a few frames) =="
if command -v python3 >/dev/null 2>&1; then
  python3 - <<'PY'
import sys,subprocess,glob,time
try:
    import cv2
except Exception as e:
    print('OpenCV not installed or failed to import:', e)
    sys.exit(0)

devs = sorted(glob.glob('/dev/video*'))
if not devs:
    print('No /dev/video* devices found')
    sys.exit(0)

for d in devs:
    print('\n--', d, '--')
    for api in (cv2.CAP_V4L2, cv2.CAP_ANY):
        try:
            cap = cv2.VideoCapture(d, api)
            ok = cap.isOpened()
            print('API', api, 'opened=', ok)
            if not ok:
                cap.release(); continue
            # read caps
            w = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
            h = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
            fps = cap.get(cv2.CAP_PROP_FPS)
            fourcc = int(cap.get(cv2.CAP_PROP_FOURCC))
            print(f'W,H={w}x{h} fps={fps} FOURCC={fourcc}')
            # attempt to set MJPG and read frames
            cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('M','J','P','G'))
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
            cap.set(cv2.CAP_PROP_FPS, 30)
            time.sleep(0.1)
            # grab a few frames and measure fps
            t0 = time.time()
            n = 0
            for _ in range(20):
                ret,frm = cap.read()
                if not ret: break
                n += 1
            dt = time.time()-t0
            if dt>0 and n>0:
                print('Captured', n, 'frames in', f'{dt:.2f}s -> approx FPS', f'{n/dt:.2f}')
            cap.release()
        except Exception as e:
            print('Error testing with api', api, e)
PY
else
  echo "python3 not found"
fi

echo "\n== End of report =="

