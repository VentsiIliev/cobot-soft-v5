import numpy as np
from typing import Tuple, List
from modules.shared.core.ContourStandartized import Contour
from ..models import WorkpieceDimensions


def process_workpiece_contour(match, centroid: Tuple[float, float], orientation: float) -> Tuple[Contour, List]:
    """
    Get and rotate contour for processing.
    
    Args:
        match: Matched workpiece object
        centroid: Centroid coordinates for rotation
        orientation: Rotation angle in degrees
    
    Returns:
        Tuple of (processed Contour object, original contour)
    """
    cnt = match.get_main_contour()
    cnt_object = Contour(cnt)
    cnt_object.rotate(-orientation, centroid)  # Align with X-axis
    return cnt_object, cnt


def calculate_workpiece_dimensions(cnt_object: Contour) -> WorkpieceDimensions:
    """
    Calculate workpiece dimensions from contour.
    
    Args:
        cnt_object: Contour object to analyze
    
    Returns:
        WorkpieceDimensions containing width, height, center, and minRect
    """
    min_rect = cnt_object.getMinAreaRect()
    bbox_center = (min_rect[0][0], min_rect[0][1])
    width = min_rect[1][0]
    height = min_rect[1][1]
    
    # Ensure width is always the larger dimension
    if width < height:
        width, height = height, width

    return WorkpieceDimensions(
        width=width,
        height=height,
        bbox_center=bbox_center,
        min_rect=min_rect
    )


def translate_contour_to_target(cnt_object: Contour, bbox_center: Tuple[float, float], 
                                target_x: float, target_y: float) -> Tuple[Tuple[float, float], float, float]:
    """
    Translate contour to target position and return new centroid.
    
    Args:
        cnt_object: Contour object to translate
        bbox_center: Current bounding box center
        target_x: Target X position
        target_y: Target Y position
    
    Returns:
        Tuple of (new_centroid, translation_x, translation_y)
    """
    translation_x = target_x - bbox_center[0]
    translation_y = target_y - bbox_center[1]
    cnt_object.translate(translation_x, translation_y)
    new_centroid = cnt_object.getCentroid()
    return new_centroid, translation_x, translation_y


def close_contours(contours: List) -> None:
    """
    Close contours by adding the first point to the end.
    
    Args:
        contours: List of contours to close (modifies in place)
    """
    for i, cnt in enumerate(contours):
        if len(cnt) > 0:
            # Close the contour by adding first point to the end using numpy concatenation
            # Ensure dimensions match: cnt is (n, 1, 2), so reshape first point to (1, 1, 2)
            first_point = cnt[0].reshape(1, 1, 2)
            contours[i] = np.vstack([cnt, first_point])