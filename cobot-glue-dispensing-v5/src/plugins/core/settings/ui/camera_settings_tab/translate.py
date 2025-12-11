from frontend.core.utils.localization import TranslationKeys


def translate(camera_settings_tab_layout):
    """Update UI text based on current language"""
    print(f"Translating CameraSettingsTabLayout...")

    # Update styling to ensure responsive fonts are applied
    camera_settings_tab_layout.setup_styling()

    # Core settings group
    if hasattr(camera_settings_tab_layout, 'core_group'):
        camera_settings_tab_layout.core_group.setTitle(camera_settings_tab_layout.translator.get(TranslationKeys.CameraSettings.CAMERA_SETTINGS))
        # Update core settings labels by accessing the layout
        core_layout = camera_settings_tab_layout.core_group.layout()
        if core_layout:
            # Camera Index
            if core_layout.itemAtPosition(0, 0):
                core_layout.itemAtPosition(0, 0).widget().setText(
                    camera_settings_tab_layout.translator.get(TranslationKeys.CameraSettings.CAMERA_INDEX))
            # Width
            if core_layout.itemAtPosition(1, 0):
                core_layout.itemAtPosition(1, 0).widget().setText(
                    camera_settings_tab_layout.translator.get(TranslationKeys.CameraSettings.WIDTH))
            # Height
            if core_layout.itemAtPosition(2, 0):
                core_layout.itemAtPosition(2, 0).widget().setText(
                    camera_settings_tab_layout.translator.get(TranslationKeys.CameraSettings.HEIGHT))
            # Skip Frames
            if core_layout.itemAtPosition(3, 0):
                core_layout.itemAtPosition(3, 0).widget().setText(
                    camera_settings_tab_layout.translator.get(TranslationKeys.CameraSettings.SKIP_FRAMES))

    # Contour settings group  
    if hasattr(camera_settings_tab_layout, 'contour_group'):
        camera_settings_tab_layout.contour_group.setTitle(camera_settings_tab_layout.translator.get(TranslationKeys.CameraSettings.CONTOUR_DETECTION))
        # Update contour settings labels
        contour_layout = camera_settings_tab_layout.contour_group.layout()
        if contour_layout:
            # Enable Detection
            if contour_layout.itemAtPosition(0, 0):
                contour_layout.itemAtPosition(0, 0).widget().setText(
                    camera_settings_tab_layout.translator.get(TranslationKeys.CameraSettings.ENABLE_DETECTION))
            # Draw Contours
            if contour_layout.itemAtPosition(1, 0):
                contour_layout.itemAtPosition(1, 0).widget().setText(
                    camera_settings_tab_layout.translator.get(TranslationKeys.CameraSettings.DRAW_CONTOURS))
            # Threshold
            if contour_layout.itemAtPosition(2, 0):
                contour_layout.itemAtPosition(2, 0).widget().setText(
                    camera_settings_tab_layout.translator.get(TranslationKeys.CameraSettings.THRESHOLD))
            # Threshold Pickup Area
            if contour_layout.itemAtPosition(3, 0):
                contour_layout.itemAtPosition(3, 0).widget().setText(
                    f"{camera_settings_tab_layout.translator.get(TranslationKeys.CameraSettings.THRESHOLD)} 2")
            # Epsilon
            if contour_layout.itemAtPosition(4, 0):
                contour_layout.itemAtPosition(5, 0).widget().setText(
                    camera_settings_tab_layout.translator.get(TranslationKeys.CameraSettings.EPSILON))
            # Min Contour Area
            if contour_layout.itemAtPosition(5, 0):
                contour_layout.itemAtPosition(5, 0).widget().setText(
                    camera_settings_tab_layout.translator.get(TranslationKeys.CameraSettings.MIN_CONTOUR_AREA))
            # Max Contour Area
            if contour_layout.itemAtPosition(6, 0):
                contour_layout.itemAtPosition(6, 0).widget().setText(
                    camera_settings_tab_layout.translator.get(TranslationKeys.CameraSettings.MAX_CONTOUR_AREA))

    # Preprocessing settings group
    if hasattr(camera_settings_tab_layout, 'preprocessing_group'):
        camera_settings_tab_layout.preprocessing_group.setTitle(camera_settings_tab_layout.translator.get(TranslationKeys.CameraSettings.PREPROCESSING))
        # Update preprocessing settings labels
        preprocessing_layout = camera_settings_tab_layout.preprocessing_group.layout()
        if preprocessing_layout:
            # Gaussian Blur
            if preprocessing_layout.itemAtPosition(0, 0):
                preprocessing_layout.itemAtPosition(0, 0).widget().setText(
                    camera_settings_tab_layout.translator.get(TranslationKeys.CameraSettings.GAUSSIAN_BLUR))
            # Blur Kernel Size
            if preprocessing_layout.itemAtPosition(1, 0):
                preprocessing_layout.itemAtPosition(1, 0).widget().setText(
                    camera_settings_tab_layout.translator.get(TranslationKeys.CameraSettings.BLUR_KERNEL_SIZE))
            # Threshold Type
            if preprocessing_layout.itemAtPosition(2, 0):
                preprocessing_layout.itemAtPosition(2, 0).widget().setText(
                    camera_settings_tab_layout.translator.get(TranslationKeys.CameraSettings.THRESHOLD_TYPE))
            # Dilate
            if preprocessing_layout.itemAtPosition(3, 0):
                preprocessing_layout.itemAtPosition(3, 0).widget().setText(
                    camera_settings_tab_layout.translator.get(TranslationKeys.CameraSettings.DILATE))
            # Dilate Kernel
            if preprocessing_layout.itemAtPosition(4, 0):
                preprocessing_layout.itemAtPosition(4, 0).widget().setText(
                    camera_settings_tab_layout.translator.get(TranslationKeys.CameraSettings.DILATE_KERNEL))
            # Dilate Iterations
            if preprocessing_layout.itemAtPosition(5, 0):
                preprocessing_layout.itemAtPosition(5, 0).widget().setText(
                    camera_settings_tab_layout.translator.get(TranslationKeys.CameraSettings.DILATE_ITERATIONS))
            # Erode
            if preprocessing_layout.itemAtPosition(6, 0):
                preprocessing_layout.itemAtPosition(6, 0).widget().setText(
                    camera_settings_tab_layout.translator.get(TranslationKeys.CameraSettings.ERODE))
            # Erode Kernel
            if preprocessing_layout.itemAtPosition(7, 0):
                preprocessing_layout.itemAtPosition(7, 0).widget().setText(
                    camera_settings_tab_layout.translator.get(TranslationKeys.CameraSettings.ERODE_KERNEL))
            # Erode Iterations
            if preprocessing_layout.itemAtPosition(8, 0):
                preprocessing_layout.itemAtPosition(8, 0).widget().setText(
                    camera_settings_tab_layout.translator.get(TranslationKeys.CameraSettings.ERODE_ITERATIONS))

    # Calibration settings group
    if hasattr(camera_settings_tab_layout, 'calibration_group'):
        camera_settings_tab_layout.calibration_group.setTitle(camera_settings_tab_layout.translator.get(TranslationKeys.CameraSettings.CALIBRATION))
        # Update calibration settings labels
        calibration_layout = camera_settings_tab_layout.calibration_group.layout()
        if calibration_layout:
            # Chessboard Width
            if calibration_layout.itemAtPosition(0, 0):
                calibration_layout.itemAtPosition(0, 0).widget().setText(
                    camera_settings_tab_layout.translator.get(TranslationKeys.CameraSettings.CHESSBOARD_WIDTH))
            # Chessboard Height
            if calibration_layout.itemAtPosition(1, 0):
                calibration_layout.itemAtPosition(1, 0).widget().setText(
                    camera_settings_tab_layout.translator.get(TranslationKeys.CameraSettings.CHESSBOARD_HEIGHT))
            # Square Size
            if calibration_layout.itemAtPosition(2, 0):
                calibration_layout.itemAtPosition(2, 0).widget().setText(
                    camera_settings_tab_layout.translator.get(TranslationKeys.CameraSettings.SQUARE_SIZE))
            # Skip Frames (calibration)
            if calibration_layout.itemAtPosition(3, 0):
                calibration_layout.itemAtPosition(3, 0).widget().setText(
                    camera_settings_tab_layout.translator.get(TranslationKeys.CameraSettings.SKIP_FRAMES))

    # Brightness settings group
    if hasattr(camera_settings_tab_layout, 'brightness_group'):
        camera_settings_tab_layout.brightness_group.setTitle(camera_settings_tab_layout.translator.get(TranslationKeys.CameraSettings.BRIGHTNESS_CONTROL))
        # Update brightness settings labels
        brightness_layout = camera_settings_tab_layout.brightness_group.layout()
        if brightness_layout:
            # Auto Brightness
            if brightness_layout.itemAtPosition(0, 0):
                brightness_layout.itemAtPosition(0, 0).widget().setText(
                    camera_settings_tab_layout.translator.get(TranslationKeys.CameraSettings.AUTO_BRIGHTNESS))
            # Kp (keep as is, technical term)
            # Ki (keep as is, technical term)
            # Kd (keep as is, technical term)
            # Target Brightness
            if brightness_layout.itemAtPosition(4, 0):
                brightness_layout.itemAtPosition(4, 0).widget().setText(
                    camera_settings_tab_layout.translator.get(TranslationKeys.CameraSettings.TARGET_BRIGHTNESS))

    # ArUco settings group
    if hasattr(camera_settings_tab_layout, 'aruco_group'):
        camera_settings_tab_layout.aruco_group.setTitle(camera_settings_tab_layout.translator.get(TranslationKeys.CameraSettings.ARUCO_DETECTION))
        # Update ArUco settings labels
        aruco_layout = camera_settings_tab_layout.aruco_group.layout()
        if aruco_layout:
            # Enable ArUco
            if aruco_layout.itemAtPosition(0, 0):
                aruco_layout.itemAtPosition(0, 0).widget().setText(
                    camera_settings_tab_layout.translator.get(TranslationKeys.CameraSettings.ENABLE_ARUCO))
            # Dictionary
            if aruco_layout.itemAtPosition(1, 0):
                aruco_layout.itemAtPosition(1, 0).widget().setText(
                    camera_settings_tab_layout.translator.get(TranslationKeys.CameraSettings.DICTIONARY))
            # Flip Image
            if aruco_layout.itemAtPosition(2, 0):
                aruco_layout.itemAtPosition(2, 0).widget().setText(
                    camera_settings_tab_layout.translator.get(TranslationKeys.CameraSettings.FLIP_IMAGE))

    # Update camera status label (dynamic content)
    if hasattr(camera_settings_tab_layout, 'camera_status_label') and hasattr(camera_settings_tab_layout, 'current_camera_state'):
        camera_settings_tab_layout.camera_status_label.setText(
            f"{camera_settings_tab_layout.translator.get(TranslationKeys.CameraSettings.CAMERA_STATUS)}: {camera_settings_tab_layout.current_camera_state}")

    # Update camera preview label