"""
Preview Click Handler - Reusable component for handling preview image clicks
Extracts common logic for coordinate mapping and pixel value extraction
"""
from typing import Optional, Tuple, Callable
from PyQt6.QtWidgets import QLabel
from PyQt6.QtGui import QPixmap


class PreviewClickHandler:
    """
    Handles click events on preview labels with coordinate mapping and pixel info extraction.

    This class encapsulates the common logic for:
    - Mapping click coordinates to pixmap coordinates (accounting for centered alignment)
    - Validating click is within image bounds
    - Extracting pixel color information
    - Optional coordinate scaling for different resolutions
    """

    def __init__(self, label: QLabel, preview_name: str = "Preview"):
        """
        Initialize the handler.

        Args:
            label: The QLabel widget displaying the preview
            preview_name: Name for debug/logging purposes
        """
        self.label = label
        self.preview_name = preview_name

    def map_click_to_pixmap_coords(self, click_x: int, click_y: int) -> Optional[Tuple[int, int]]:
        """
        Map click coordinates from label space to pixmap space.
        Accounts for centered alignment of pixmap within label.

        Args:
            click_x: X coordinate of click in label space
            click_y: Y coordinate of click in label space

        Returns:
            Tuple of (pixmap_x, pixmap_y) if click is within pixmap, None otherwise
        """
        pixmap = self.label.pixmap() if self.label else None
        if pixmap is None:
            print(f"{self.preview_name} Clicked on {click_x}:{click_y} - no image available")
            return None

        label_w = self.label.width()
        label_h = self.label.height()
        img_w = pixmap.width()
        img_h = pixmap.height()

        # Calculate top-left of the drawn pixmap inside the label (centered alignment)
        left = (label_w - img_w) // 2
        top = (label_h - img_h) // 2

        # Map click coordinates to pixmap coordinates
        pixmap_x = int(click_x - left)
        pixmap_y = int(click_y - top)

        # Validate coordinates are within pixmap bounds
        if not (0 <= pixmap_x < img_w and 0 <= pixmap_y < img_h):
            print(f"{self.preview_name} Clicked on {click_x}:{click_y} - outside image area")
            return None

        return (pixmap_x, pixmap_y)

    def get_pixel_color(self, pixmap_x: int, pixmap_y: int) -> Optional[Tuple[int, int, int]]:
        """
        Extract RGB color values at the given pixmap coordinates.

        Args:
            pixmap_x: X coordinate in pixmap space
            pixmap_y: Y coordinate in pixmap space

        Returns:
            Tuple of (r, g, b) values, or None if extraction fails
        """
        pixmap = self.label.pixmap()
        if pixmap is None:
            return None

        qimage = pixmap.toImage()
        color = qimage.pixelColor(pixmap_x, pixmap_y)
        return (color.red(), color.green(), color.blue())

    def scale_coordinates(self, pixmap_x: int, pixmap_y: int,
                         target_width: int, target_height: int) -> Tuple[int, int]:
        """
        Scale pixmap coordinates to a different resolution.
        Useful when preview is at different resolution than original image.

        Args:
            pixmap_x: X coordinate in pixmap space
            pixmap_y: Y coordinate in pixmap space
            target_width: Target resolution width
            target_height: Target resolution height

        Returns:
            Tuple of (scaled_x, scaled_y) in target resolution
        """
        pixmap = self.label.pixmap()
        if pixmap is None:
            return (pixmap_x, pixmap_y)

        img_w = pixmap.width()
        img_h = pixmap.height()

        scaled_x = int((pixmap_x / img_w) * target_width)
        scaled_y = int((pixmap_y / img_h) * target_height)

        return (scaled_x, scaled_y)

    def handle_click(self, click_x: int, click_y: int,
                     on_valid_click: Optional[Callable[[int, int, int, int, int], None]] = None,
                     scale_to_resolution: Optional[Tuple[int, int]] = None) -> Optional[dict]:
        """
        Complete click handling workflow.

        Args:
            click_x: X coordinate of click in label space
            click_y: Y coordinate of click in label space
            on_valid_click: Callback (pixmap_x, pixmap_y, r, g, b) for valid clicks
            scale_to_resolution: Optional (width, height) tuple to scale coordinates to

        Returns:
            Dictionary with click info if successful:
            {
                'pixmap_coords': (x, y),
                'scaled_coords': (x, y) if scaling enabled,
                'color_rgb': (r, g, b)
            }
        """
        # Map to pixmap coordinates
        coords = self.map_click_to_pixmap_coords(click_x, click_y)
        if coords is None:
            return None

        pixmap_x, pixmap_y = coords

        # Extract pixel color
        color = self.get_pixel_color(pixmap_x, pixmap_y)
        if color is None:
            return None

        r, g, b = color

        # Prepare result
        result = {
            'pixmap_coords': (pixmap_x, pixmap_y),
            'color_rgb': (r, g, b)
        }

        # Scale coordinates if requested
        if scale_to_resolution:
            target_w, target_h = scale_to_resolution
            scaled_x, scaled_y = self.scale_coordinates(pixmap_x, pixmap_y, target_w, target_h)
            result['scaled_coords'] = (scaled_x, scaled_y)

        # Call callback if provided
        if on_valid_click:
            on_valid_click(pixmap_x, pixmap_y, r, g, b)

        return result

