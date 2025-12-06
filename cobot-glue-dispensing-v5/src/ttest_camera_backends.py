import cv2
import time

# Test different backends
backends = [
    (cv2.CAP_V4L2, "V4L2"),
    (cv2.CAP_ANY, "ANY"),
]

for backend_id, backend_name in backends:
    print(f"\n{'='*60}")
    print(f"Testing backend: {backend_name}")
    print('='*60)
    
    cap = cv2.VideoCapture(0, backend_id)
    if not cap.isOpened():
        print(f"Failed to open camera with {backend_name}")
        continue
    
    # Set resolution
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
    
    # Optimize settings
    cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 1)
    cap.set(cv2.CAP_PROP_EXPOSURE, -6)
    cap.set(cv2.CAP_PROP_AUTOFOCUS, 0)
    cap.set(cv2.CAP_PROP_FPS, 30)
    cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('M', 'J', 'P', 'G'))
    
    print(f"Resolution: {int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))}x{int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))}")
    print(f"FPS Setting: {cap.get(cv2.CAP_PROP_FPS)}")
    print(f"FOURCC: {int(cap.get(cv2.CAP_PROP_FOURCC))}")
    
    # Test FPS for 50 frames
    fps_list = []
    prev_time = time.time()
    
    for i in range(50):
        ret, frame = cap.read()
        if ret:
            current_time = time.time()
            fps = 1.0 / (current_time - prev_time)
            prev_time = current_time
            fps_list.append(fps)
            if i % 10 == 0:
                print(f"Frame {i}: {fps:.2f} FPS")
    
    if fps_list:
        avg_fps = sum(fps_list) / len(fps_list)
        print(f"\n{backend_name} Average FPS: {avg_fps:.2f}")
    
    cap.release()

print(f"\n{'='*60}")
print("Testing complete!")

