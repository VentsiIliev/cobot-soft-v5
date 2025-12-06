#!/usr/bin/env python3
"""
Camera Information Script
Executes terminal commands to get detailed camera information
"""

import subprocess
import sys

def run_command(command, description):
    """Run a shell command and return the output"""
    print("\n" + "="*70)
    print(f"📷 {description}")
    print("="*70)
    print(f"Command: {command}")
    print("-"*70)
    
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode == 0:
            output = result.stdout.strip()
            if output:
                print(output)
            else:
                print("(No output)")
        else:
            print(f"Error (return code {result.returncode}):")
            if result.stderr:
                print(result.stderr.strip())
            else:
                print("(No error message)")
        
        return result.stdout, result.stderr, result.returncode
    
    except subprocess.TimeoutExpired:
        print("⚠️  Command timed out after 5 seconds")
        return "", "Timeout", -1
    except Exception as e:
        print(f"⚠️  Exception: {e}")
        return "", str(e), -1


def main():
    print("\n" + "🎥"*35)
    print("CAMERA INFORMATION TOOL")
    print("🎥"*35)
    
    # 1. List all video devices
    run_command(
        "v4l2-ctl --list-devices",
        "List all video devices"
    )
    
    # 2. List video devices in /dev
    run_command(
        "ls -la /dev/video*",
        "Video device files in /dev"
    )
    
    # 3. Get detailed info for each video device
    for video_num in [0, 1, 2]:
        device = f"/dev/video{video_num}"
        
        # Check if device exists
        stdout, _, returncode = run_command(
            f"test -e {device} && echo 'exists' || echo 'not found'",
            f"Check if {device} exists"
        )
        
        if "not found" in stdout:
            print(f"Skipping {device} - does not exist")
            continue
        
        # Get all capabilities
        run_command(
            f"v4l2-ctl -d {device} --all",
            f"All capabilities for {device}"
        )
        
        # List supported formats
        run_command(
            f"v4l2-ctl -d {device} --list-formats-ext",
            f"Supported formats and frame rates for {device}"
        )
        
        # List controls
        run_command(
            f"v4l2-ctl -d {device} --list-ctrls",
            f"Available controls for {device}"
        )
    
    # 4. Check USB devices for cameras
    run_command(
        "lsusb | grep -i camera",
        "USB camera devices (lsusb)"
    )
    
    # 5. Alternative: list all USB devices
    run_command(
        "lsusb",
        "All USB devices"
    )
    
    # 6. Check for camera info in dmesg
    run_command(
        "dmesg | grep -i 'video\\|camera\\|uvc' | tail -20",
        "Recent kernel messages about cameras (dmesg)"
    )
    
    # 7. OpenCV camera test
    print("\n" + "="*70)
    print("📷 OpenCV Camera Detection")
    print("="*70)
    
    try:
        import cv2
        print(f"OpenCV Version: {cv2.__version__}")
        print("\nTesting camera indices 0-5:")
        
        for i in range(6):
            cap = cv2.VideoCapture(i)
            if cap.isOpened():
                width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                fps = cap.get(cv2.CAP_PROP_FPS)
                backend = cap.getBackendName()
                fourcc = int(cap.get(cv2.CAP_PROP_FOURCC))
                
                # Convert FOURCC to readable format
                fourcc_str = "".join([chr((fourcc >> 8 * i) & 0xFF) for i in range(4)])
                
                print(f"\n  Camera {i}: ✅ AVAILABLE")
                print(f"    Backend: {backend}")
                print(f"    Resolution: {width}x{height}")
                print(f"    FPS: {fps}")
                print(f"    Format: {fourcc_str} ({fourcc})")
                
                cap.release()
            else:
                print(f"  Camera {i}: ❌ Not available")
    
    except ImportError:
        print("⚠️  OpenCV not installed (pip install opencv-python)")
    except Exception as e:
        print(f"⚠️  Error testing OpenCV: {e}")
    
    # 8. Summary
    print("\n" + "="*70)
    print("📊 SUMMARY")
    print("="*70)
    print("""
To change camera settings, use commands like:
  v4l2-ctl -d /dev/video1 --set-ctrl=exposure_auto=1
  v4l2-ctl -d /dev/video1 --set-ctrl=exposure_absolute=100
  v4l2-ctl -d /dev/video1 --set-ctrl=brightness=128

To use MJPG format in Python/OpenCV for better FPS:
  cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('M', 'J', 'P', 'G'))
    """)
    
    print("\n" + "🎥"*35)
    print("DONE!")
    print("🎥"*35 + "\n")


if __name__ == "__main__":
    main()

