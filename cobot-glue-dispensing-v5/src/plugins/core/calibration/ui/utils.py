def convert_camera_coordinates_to_image_coordinates(image, camera_corners):
    """Convert coordinates from camera resolution (1280x720) to actual image scale for drawing"""
    if image is None:
        return [(int(x), int(y)) for x, y in camera_corners]

    # Get the actual image size
    img_height, img_width = image.shape[:2]

    # Camera resolution is fixed at 1280x720
    camera_width = 1280
    camera_height = 720

    # Calculate scaling factors from camera resolution to actual image size
    scale_x = img_width / camera_width
    scale_y = img_height / camera_height

    # Convert coordinates
    image_corners = []
    for x, y in camera_corners:
        image_x = x * scale_x
        image_y = y * scale_y

        # Ensure coordinates are within image bounds
        image_x = max(0, min(image_x, img_width - 1))
        image_y = max(0, min(image_y, img_height - 1))

        image_corners.append((int(image_x), int(image_y)))

    return image_corners
