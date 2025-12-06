import math

from modules.utils.custom_logging import log_info_message


def log_pickup_position_calculation_result(params, logger_context, gripper_x_offset, gripper_y_offset):
    flat_centroid, pickup_x_rotated, pickup_y_rotated, orientation_radians, gripper_x_offset_rotated, gripper_y_offset_rotated, final_pickup_x, final_pickup_y, z_min, descent_height, pickup_height, pickup_positions = params
    # === LOGGING ===
    log_info_message(logger_context, f"COORDINATE TRANSFORMATION:")
    log_info_message(logger_context, f"  ├─ Before 90° rotation: ({flat_centroid[0]:.2f}, {flat_centroid[1]:.2f}) mm")
    log_info_message(logger_context, f"  └─ After 90° rotation:  ({pickup_x_rotated:.2f}, {pickup_y_rotated:.2f}) mm")
    log_info_message(logger_context, f"GRIPPER OFFSET TRANSFORMATION:")
    log_info_message(logger_context, f"  ├─ Original offsets: ({gripper_x_offset}, {gripper_y_offset}) mm")
    log_info_message(logger_context,
                     f"  └─ Rotated offsets:  ({gripper_x_offset_rotated:.2f}, {gripper_y_offset_rotated:.2f}) mm (rotated by {math.degrees(orientation_radians):.2f}°)")
    log_info_message(logger_context, f"FINAL PICKUP CALCULATION:")
    log_info_message(logger_context, f"  ├─ Rotated position: ({pickup_x_rotated:.2f}, {pickup_y_rotated:.2f}) mm")
    log_info_message(logger_context,
                     f"  ├─ Applied offsets:  ({gripper_x_offset_rotated:.2f}, {gripper_y_offset_rotated:.2f}) mm")
    log_info_message(logger_context, f"  └─ Final position:   ({final_pickup_x:.2f}, {final_pickup_y:.2f}) mm")
    log_info_message(logger_context, f"HEIGHT CALCULATIONS:")
    log_info_message(logger_context, f"  ├─ Z minimum:     {z_min} mm")
    log_info_message(logger_context, f"  ├─ Descent height: {descent_height} mm")
    log_info_message(logger_context, f"  └─ Pickup height:  {pickup_height} mm")
    log_info_message(logger_context, f"Generated {len(pickup_positions)} pickup positions (descent → pickup → lift)")
    log_info_message(logger_context, f"Pickup sequence: {pickup_positions}")


def log_match_details(logger_context, match_height, gripper, centroid, flat_centroid, orientations, match_i):
    log_info_message(logger_context, f"Match details: height={match_height}mm, gripper={gripper}")
    log_info_message(logger_context, "Applying homography transformation...")
    log_info_message(logger_context, f"HOMOGRAPHY TRANSFORMATION:")
    log_info_message(logger_context, f"  ├─ Camera coordinates: {centroid} pixels")
    log_info_message(logger_context, f"  ├─ Robot coordinates:  {flat_centroid} mm")
    log_info_message(logger_context, f"  ├─ Object orientation: {orientations[match_i]:.2f}°")
    log_info_message(logger_context, f"  └─ Assigned gripper:   {gripper}")


def log_drop_pos_calculated(logger_context, drop_off_position1, width, height):
    log_info_message(logger_context,
                     f"📍 DROP-OFF: Position calculated at {drop_off_position1[:2]} mm (Z: {drop_off_position1[2]} mm)")
    log_info_message(logger_context, f"Drop-off position: {drop_off_position1}")
    log_info_message(logger_context, f"Workpiece dimensions: {width:.1f} x {height:.1f} mm")


def log_workpiece_dimensions(logger_context, width, height, bboxCenter, minRect, orientation):
    # === LOGGING ===
    log_info_message(logger_context, f"Rotating contour by {-orientation:.2f}° to align with X-axis")
    log_info_message(logger_context, "Swapped width/height to ensure width >= height" if width != minRect[1][0] else "")
    log_info_message(logger_context, f"WORKPIECE DIMENSIONS:")
    log_info_message(logger_context, f"  ├─ Width:  {width:.2f} mm")
    log_info_message(logger_context, f"  ├─ Height: {height:.2f} mm")
    log_info_message(logger_context, f"  └─ Bbox center: ({bboxCenter[0]:.2f}, {bboxCenter[1]:.2f})")


def log_calculated_drop_position(logger_context, targetPointX, targetPointY, width, height, plane):
    log_info_message(logger_context,
                     f"Calculated target X position: {targetPointX:.1f} = {plane.xOffset} + {plane.xMin}+{width / 2} mm")
    log_info_message(logger_context,
                     f"Calculated target Y position: {targetPointY:.1f} = {plane.yOffset} + {plane.yMax}+{height / 2} mm")


def log_moving_to_next_row(logger_context, targetPointX, targetPointY, width, plane):
    log_info_message(logger_context, f"⚠️  Width exceeded, moving to next row")
    log_info_message(logger_context, f"Exceeded by: {(targetPointX + width / 2) - plane.xMax:.1f} mm")

    log_info_message(logger_context, f"NEW ROW {plane.rowCount}:")
    log_info_message(logger_context, f"  ├─ Reset to: ({targetPointX:.1f}, {targetPointY:.1f}) mm")
    log_info_message(logger_context, f"  └─ Row spacing: {plane.tallestContour + 50:.1f} mm")


def log_placement_calculations(logger_context, previous_tallest, height, plane, targetPointX, targetPointY):
    log_info_message(logger_context,
                     f"Updated tallest contour: {previous_tallest:.1f} → {height:.1f} mm" if height > previous_tallest else "")
    log_info_message(logger_context, f"PLACEMENT CALCULATION:")
    log_info_message(logger_context, f"  ├─ Current offset: ({plane.xOffset:.1f}, {plane.yOffset:.1f}) mm")
    log_info_message(logger_context, f"  ├─ Target point:  ({targetPointX:.1f}, {targetPointY:.1f}) mm")
    log_info_message(logger_context, f"  └─ Plane bounds:  ({plane.xMin}-{plane.xMax}, {plane.yMin}-{plane.yMax}) mm")
