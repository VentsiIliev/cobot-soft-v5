import cv2
import time
import glob
import subprocess
import os

# Function to find working camera
def find_camera(max_index=9):
    """Find the first available camera index or device path using best backend.
    Tries numeric indexes first (most reliable with OpenCV builds), then /dev/video* paths.
    Returns (source, cap) where source is the path or index used.
    """
    backends_to_try = []
    if hasattr(cv2, 'CAP_V4L2'):
        backends_to_try.append(('CAP_V4L2', cv2.CAP_V4L2))
    if hasattr(cv2, 'CAP_ANY'):
        backends_to_try.append(('CAP_ANY', cv2.CAP_ANY))

    # try numeric indexes first (observed to work even when opening by path fails)
    for i in range(0, max_index+1):
        for name, api in backends_to_try:
            try:
                cap = cv2.VideoCapture(i, api)
            except Exception:
                continue
            if cap.isOpened():
                print(f"✅ Found working camera at index {i} using backend {name}")
                return i, cap
            try:
                cap.release()
            except:
                pass

    # try device paths as a fallback
    devs = sorted(glob.glob('/dev/video*'))
    for d in devs:
        for name, api in backends_to_try:
            try:
                cap = cv2.VideoCapture(d, api)
            except Exception:
                continue
            if cap.isOpened():
                print(f"✅ Found working camera at {d} using backend {name}")
                return d, cap
            try:
                cap.release()
            except:
                pass

    return None, None


def print_device_diagnostics():
    print('\n-- Device diagnostics --')
    try:
        subprocess.run('ls -la /dev/video*', shell=True)
    except Exception:
        pass
    try:
        subprocess.run('lsof /dev/video* 2>/dev/null || true', shell=True)
    except Exception:
        pass
    try:
        subprocess.run('v4l2-ctl --list-devices 2>/dev/null || true', shell=True)
    except Exception:
        pass

# Find available camera
camera_index, cap = find_camera()

if cap is None or not cap.isOpened():
    print("❌ ERROR: No camera found or cannot be opened by OpenCV.")
    print("Check if another process holds the device, and try running the collection script:")
    print("  src/scripts/collect_camera_info.sh")
    print_device_diagnostics()
    exit(1)

print(f"Using camera source: {camera_index}")

# Set resolution BEFORE setting FOURCC
# Prefer MJPG for high fps; try commonly supported sizes
preferred_sizes = [(1920,1080,60), (1280,720,30), (640,480,30)]
set_success = False
for w,h,fps_setting in preferred_sizes:
    # try setting FOURCC MJPG first
    try:
        cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('M', 'J', 'P', 'G'))
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, w)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, h)
        cap.set(cv2.CAP_PROP_FPS, fps_setting)
        cap.set(cv2.CAP_PROP_EXPOSURE,144)
        time.sleep(0.05)
        actual_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        actual_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        actual_fps = cap.get(cv2.CAP_PROP_FPS)
        if actual_w == w and actual_h == h:
            print(f"Configured camera to {w}x{h}@{fps_setting} (reported fps {actual_fps})")
            set_success = True
            break
    except Exception:
        pass
if not set_success:
    print("Could not configure preferred resolution/FPS; using camera defaults.")

# Try to disable auto-exposure and autofocus (may silently fail depending on driver)
try:
    if hasattr(cv2, 'CAP_PROP_AUTO_EXPOSURE'):
        cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 1)  # manual if supported
    if hasattr(cv2, 'CAP_PROP_AUTOFOCUS'):
        cap.set(cv2.CAP_PROP_AUTOFOCUS, 0)
except Exception:
    pass

# Print actual camera settings
print("="*60)
print("Camera Settings:")
print(f"Resolution: {int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))}x{int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))}")
print(f"FOURCC: {cap.get(cv2.CAP_PROP_FOURCC)} (MJPG={cv2.VideoWriter_fourcc('M', 'J', 'P', 'G')})")
print(f"FPS Setting: {cap.get(cv2.CAP_PROP_FPS)}")
print(f"Auto Exposure: {cap.get(cv2.CAP_PROP_AUTO_EXPOSURE) if hasattr(cv2, 'CAP_PROP_AUTO_EXPOSURE') else 'N/A'}")
print(f"Exposure: {cap.get(cv2.CAP_PROP_EXPOSURE)}")
print(f"Autofocus: {cap.get(cv2.CAP_PROP_AUTOFOCUS) if hasattr(cv2, 'CAP_PROP_AUTOFOCUS') else 'N/A'}")
print(f"Brightness: {cap.get(cv2.CAP_PROP_BRIGHTNESS)}")
try:
    backend_name = cap.getBackendName()
except Exception:
    backend_name = 'N/A'
print(f"Backend: {backend_name}")
print("="*60)

prev_time = time.time()
frame_count = 0
fps_sum = 0

while True:
    ret, frame = cap.read()
    if not ret:
        print("Failed to grab frame")
        time.sleep(1)
        continue

    # Calculate FPS
    current_time = time.time()
    fps = 1.0 / (current_time - prev_time) if (current_time - prev_time) > 0 else 0.0
    prev_time = current_time

    frame_count += 1
    fps_sum += fps

    # Display FPS on the frame
    cv2.putText(frame,
                f"FPS: {fps:.2f} (Avg: {fps_sum/frame_count:.2f})",
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (0, 255, 0),
                2)

    if frame_count % 10 == 0:  # Print every 10 frames instead of every frame
        print(f"Current FPS: {fps:.2f} | Avg FPS: {fps_sum/frame_count:.2f}")

    cv2.imshow("Camera Feed", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()

print(f"\nFinal Average FPS: {fps_sum/frame_count:.2f}")
