import time
from typing import List, Tuple, Optional
from modules.contour_matching import CompareContours
from modules.utils.contours import is_contour_inside_polygon
from communication_layer.api.v1.topics import VisionTopics
from modules.shared.MessageBroker import MessageBroker
from modules.utils.custom_logging import log_info_message
from ..operations import close_contours


class VisionWorkflow:
    """Workflow for vision-related operations in the nesting process."""
    
    def __init__(self, vision_service, logger_context):
        self.vision_service = vision_service
        self.logger_context = logger_context
        self.delay_between_captures = 1  # seconds
    
    def setup_vision_capture(self, region: str = "pickup") -> None:
        """
        Setup vision system for capturing workpieces.
        
        Args:
            region: Vision region to configure
        """
        broker = MessageBroker()
        broker.publish(VisionTopics.THRESHOLD_REGION, {"region": region})
        time.sleep(self.delay_between_captures)
    
    def get_contours_with_retries(self, max_retries: int = 10, 
                                retry_delay: int = 1) -> Tuple[bool, Optional[List]]:
        """
        Try multiple times to get contours from the vision system.
        
        Args:
            max_retries: Maximum number of retry attempts
            retry_delay: Delay between retries in seconds
            
        Returns:
            Tuple of (success, contours) - contours is None if failed
        """
        for attempt in range(1, max_retries + 1):
            contours = self.vision_service.contours

            # SUCCESS: contours available
            if contours and len(contours) > 0:
                log_info_message(self.logger_context, f"Contours found on attempt {attempt}")
                return True, contours

            # Not found yet → attempt retry
            if attempt < max_retries:
                log_info_message(
                    self.logger_context, 
                    f"No contours detected (attempt {attempt}/{max_retries}), retrying..."
                )
                time.sleep(retry_delay)

        # FAILED after all retries
        log_info_message(self.logger_context, "Max retries reached, no contours found.")
        return False, None
    
    def process_detected_contours(self, contours: List) -> List:
        """
        Process and prepare detected contours.
        
        Args:
            contours: Raw contours from vision system
            
        Returns:
            Processed contours
        """
        # Close contours by adding first point to end
        close_contours(contours)
        log_info_message(self.logger_context, f"Processing {len(contours)} detected contours...")
        return contours
    
    def filter_contours_by_pickup_area(self, contours: List) -> Optional[List]:
        """
        Filter contours to only include those in the pickup area.
        
        Args:
            contours: Contours to filter
            
        Returns:
            Filtered contours or None if no pickup area defined
        """
        pickup_area = self.vision_service.getPickupAreaPoints()
        
        if pickup_area is not None and len(pickup_area) >= 4:
            initial_count = len(contours)
            filtered_contours = []
            
            for contour in contours:
                if is_contour_inside_polygon(
                    contour, pickup_area[0], pickup_area[1], pickup_area[2], pickup_area[3]
                ):
                    filtered_contours.append(contour)
            
            log_info_message(
                self.logger_context, 
                f"Filtered {initial_count} contours to {len(filtered_contours)} in pickup area"
            )
            return filtered_contours
        
        log_info_message(self.logger_context, "No pickup area defined, processing all contours")
        return contours
    
    def match_contours_to_workpieces(self, workpieces: List, 
                                   contours: List) -> Tuple[Optional[dict], Optional[List]]:
        """
        Match detected contours with workpiece templates.
        
        Args:
            workpieces: List of workpiece templates to match against
            contours: Detected contours
            
        Returns:
            Tuple of (matches_data, no_matches) or (None, None) if error
        """
        try:
            log_info_message(
                self.logger_context, 
                f"Matching {len(contours)} contours against {len(workpieces)} workpiece templates"
            )
            
            matches_data, no_matches, _ = CompareContours.findMatchingWorkpieces(workpieces, contours)
            
            if matches_data and 'workpieces' in matches_data:
                match_count = len(matches_data['workpieces']) if matches_data['workpieces'] else 0
                log_info_message(self.logger_context, f"Found {match_count} matching workpieces")
            
            return matches_data, no_matches
            
        except Exception as e:
            import traceback
            log_info_message(self.logger_context, f"Error during contour matching: {str(e)}")
            traceback.print_exc()
            return None, None