import numpy as np

from libs.plvision.PLVision.PID.BrightnessController import BrightnessController


class BrightnessManager:
    def __init__(self, vision_system):
        self.brightnessAdjustment = 0
        self.adjustment = None
        self.vision_system = vision_system
        self.brightnessController = BrightnessController(
            Kp=self.vision_system.camera_settings.get_brightness_kp(),
            Ki=self.vision_system.camera_settings.get_brightness_ki(),
            Kd=self.vision_system.camera_settings.get_brightness_kd(),
            setPoint=self.vision_system.camera_settings.get_target_brightness()
        )


    def auto_brightness_control_off(self):
        self.vision_system.camera_settings.set_brightness_auto(False)


    def auto_brightness_control_on(self):
        self.vision_system.camera_settings.set_brightness_auto(True)


    def on_brighteness_toggle(self, mode):
        if mode == "start":
            self.vision_system.camera_settings.set_brightness_auto(True)
        elif mode == "stop":
            self.vision_system.camera_settings.set_brightness_auto(False)
        else:
            print(f"on_brightness_toggle Invalid mode {mode}")

    def get_area_by_threshold(self):
        if self.vision_system.threshold_by_area == "pickup":
            print(
                f"Using pickup area for brightness adjustment with thresh = {self.vision_system.camera_settings.get_threshold_pickup_area()}")
            return self.vision_system.getPickupAreaPoints()
        elif self.vision_system.threshold_by_area == "spray":
            print(f"Using spray area for brightness adjustment with thresh = {self.vision_system.camera_settings.get_threshold()}")
            return self.vision_system.getSprayAreaPoints()
        else:
            raise ValueError(f"Invalid threshold_by_area: {self.vision_system.threshold_by_area} Valid options are 'pickup' or 'spray'.")

    def adjust_brightness(self):
        # Get area points from camera settings, with fallback to hardcoded values
        try:
            area_points = self.vision_system.camera_settings.get_brightness_area_points()
            if area_points and len(area_points) == 4:
                # Convert from [x, y] list format to tuple format
                area_p1 = tuple(area_points[0])
                area_p2 = tuple(area_points[1])
                area_p3 = tuple(area_points[2])
                area_p4 = tuple(area_points[3])
            else:
                # Fallback to hardcoded values if settings not available
                area_p1, area_p2, area_p3, area_p4 = (940, 612), (1004, 614), (1004, 662), (940, 660)
                print("Using fallback default brightness area points")
        except Exception as e:
            # Fallback to hardcoded values on any error
            area_p1, area_p2, area_p3, area_p4 = (940, 612), (1004, 614), (1004, 662), (940, 660)
            print(f"Error loading brightness area from settings, using fallback: {e}")
        
        area = np.array([area_p1, area_p2, area_p3, area_p4], dtype=np.float32)
        
        # Calculate current brightness on original frame
        current_brightness = self.brightnessController.calculateBrightness(self.vision_system.image, area)
        
        # Compute PID adjustment
        self.brightnessAdjustment = self.brightnessController.compute(current_brightness)
        
        # Apply adjustment only once
        self.vision_system.image = self.brightnessController.adjustBrightness(
            self.vision_system.image, self.brightnessAdjustment, area
        )