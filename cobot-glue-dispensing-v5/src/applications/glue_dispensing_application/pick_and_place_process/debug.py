
import os
from datetime import datetime

import numpy as np
from matplotlib import pyplot as plt, patches

from modules.utils.custom_logging import log_if_enabled, LoggingLevel


def save_nesting_debug_plot(plane, placed_contours, match_index):
    """
    Save a debug plot showing the nested contours after drop position calculation.

    Args:
        plane: The placement plane object with bounds and current state
        placed_contours: List of contours that have been placed so far
        match_index: Current match index within the cycle
    """

    # Create figure and axis
    fig, ax = plt.subplots(1, 1, figsize=(12, 8))

    # Set up plot bounds with some margin
    margin = 50  # mm
    x_min = plane.xMin - margin
    x_max = plane.xMax + margin
    y_min = plane.yMin - margin
    y_max = plane.yMax + margin

    ax.set_xlim(x_min, x_max)
    ax.set_ylim(y_min, y_max)
    ax.set_aspect('equal')

    # Draw plane boundaries
    plane_rect = patches.Rectangle(
        (plane.xMin, plane.yMin),
        plane.xMax - plane.xMin,
        plane.yMax - plane.yMin,
        linewidth=2,
        edgecolor='red',
        facecolor='none',
        label='Placement Plane'
    )
    ax.add_patch(plane_rect)

    # Draw placed contours
    colors = ['blue', 'green', 'orange', 'purple', 'brown', 'pink', 'gray', 'olive', 'cyan']
    for i, contour_data in enumerate(placed_contours):
        contour = contour_data['contour']
        color = colors[i % len(colors)]

        # Extract x and y coordinates from contour
        if len(contour.shape) == 3 and contour.shape[1] == 1:
            # Standard OpenCV contour format (n, 1, 2)
            x_coords = contour[:, 0, 0]
            y_coords = contour[:, 0, 1]
        elif len(contour.shape) == 2 and contour.shape[1] == 2:
            # Simple (n, 2) format
            x_coords = contour[:, 0]
            y_coords = contour[:, 1]
        else:

            continue

        # Close the contour by adding first point at the end
        x_coords = np.append(x_coords, x_coords[0])
        y_coords = np.append(y_coords, y_coords[0])

        # Plot contour
        ax.plot(x_coords, y_coords, color=color, linewidth=2,
                label=f"Workpiece {i + 1}")

        # Fill contour with transparency
        ax.fill(x_coords, y_coords, color=color, alpha=0.3)

        # Mark centroid
        centroid_x = np.mean(x_coords[:-1])  # Exclude duplicate first point
        centroid_y = np.mean(y_coords[:-1])
        ax.plot(centroid_x, centroid_y, 'o', color=color, markersize=8,
                markeredgecolor='black', markeredgewidth=1)

    # Add grid and labels
    ax.grid(True, alpha=0.3)
    ax.set_xlabel('X (mm)', fontsize=12)
    ax.set_ylabel('Y (mm)', fontsize=12)
    ax.set_title(f'Nesting Debug -  Match {match_index}\n'
                 f'Placed: {len(placed_contours)} workpieces, Row: {plane.rowCount}',
                 fontsize=14, fontweight='bold')

    # Add legend
    ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')

    # Add plane info text
    info_text = (f"Plane Info:\n"
                 f"Bounds: ({plane.xMin}, {plane.yMin}) to ({plane.xMax}, {plane.yMax})\n"
                 f"Current Offset: ({plane.xOffset:.1f}, {plane.yOffset:.1f})\n"
                 f"Current Row: {plane.rowCount}\n"
                 f"Tallest in Row: {plane.tallestContour:.1f}mm\n"
                 f"Spacing: {plane.spacing}mm")

    ax.text(0.02, 0.98, info_text, transform=ax.transAxes, fontsize=10,
            verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))

    # Save plot
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"nesting_debug_cycle_match{match_index:02d}_{timestamp}.png"

    # Create debug directory if it doesn't exist
    debug_dir = "nesting_visualizations"
    if not os.path.exists(debug_dir):
        os.makedirs(debug_dir)

    filepath = os.path.join(debug_dir, filename)

    plt.tight_layout()
    plt.savefig(filepath, dpi=150, bbox_inches='tight')
    plt.close()

