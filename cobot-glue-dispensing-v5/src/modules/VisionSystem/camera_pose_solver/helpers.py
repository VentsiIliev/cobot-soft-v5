import numpy as np

def print_pose_explained(pose_matrix):
    R = pose_matrix[:3, :3]
    t = pose_matrix[:3, 3]

    tx, ty, tz = t

    print("\n=== CAMERA POSE MATRIX EXPLAINED ===\n")
    print("4×4 Homogeneous Transformation Matrix (Camera → Chessboard):")
    print(pose_matrix)

    print("\n--- Translation (Camera origin relative to chessboard) ---")
    print(f"tx = {tx:.2f} mm   → Camera shift along chessboard X-axis")
    print(f"ty = {ty:.2f} mm   → Camera shift along chessboard Y-axis")
    print(f"tz = {tz:.2f} mm   → Camera height above chessboard")

    # Convert rotation matrix to Euler angles
    sy = (R[0, 0] ** 2 + R[1, 0] ** 2) ** 0.5
    singular = sy < 1e-6

    if not singular:
        roll = np.degrees(np.arctan2(R[2, 1], R[2, 2]))
        pitch = np.degrees(np.arctan2(-R[2, 0], sy))
        yaw = np.degrees(np.arctan2(R[1, 0], R[0, 0]))
    else:
        roll = np.degrees(np.arctan2(-R[1, 2], R[1, 1]))
        pitch = np.degrees(np.arctan2(-R[2, 0], sy))
        yaw = 0

    print("\n--- Rotation Matrix (Camera orientation) ---")
    print(R)

    print("\n--- Orientation (Euler angles in degrees) ---")
    print(f"Roll  (rotation around X) = {roll:.2f}°")
    print(f"Pitch (rotation around Y) = {pitch:.2f}°")
    print(f"Yaw   (rotation around Z) = {yaw:.2f}°")

    print("\nCamera looks DOWN the -Z axis of its coordinate system.")
    print("Positive tz means chessboard is in front of the camera.\n")
    print("=====================================================\n")
