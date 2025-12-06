from frontend.core.utils.localization import TranslationKeys


def translate(robot_config_ui):
    print(f"Translating RobotConfigUI")
    robot_config_ui.general_settings_tab.robot_info_group.setTitle(
        robot_config_ui.translator.get(TranslationKeys.RobotSettings.ROBOT_INFORMATION))
    robot_config_ui.general_settings_tab.robot_info_group.robot_tool_label.setText(
        robot_config_ui.translator.get(TranslationKeys.RobotSettings.ROBOT_TOOL))
    robot_config_ui.general_settings_tab.robot_info_group.robot_user_label.setText(
        robot_config_ui.translator.get(TranslationKeys.RobotSettings.ROBOT_USER))
    robot_config_ui.general_settings_tab.robot_info_group.tcp_x_offset_label.setText(
        robot_config_ui.translator.get(TranslationKeys.RobotSettings.TCP_X_OFFSET))
    robot_config_ui.general_settings_tab.robot_info_group.tcp_y_offset_label.setText(
        robot_config_ui.translator.get(TranslationKeys.RobotSettings.TCP_Y_OFFSET))
    robot_config_ui.safety_settings_tab.safety_group.setTitle(robot_config_ui.translator.get(TranslationKeys.RobotSettings.SAFETY_LIMITS))
    robot_config_ui.general_settings_tab.global_group.setTitle(
        robot_config_ui.translator.get(TranslationKeys.RobotSettings.GLOBAL_MOTION_SETTINGS))
    robot_config_ui.general_settings_tab.global_group.global_velocity_label.setText(
        robot_config_ui.translator.get(TranslationKeys.RobotSettings.GLOBAL_VELOCITY))
    robot_config_ui.general_settings_tab.global_group.global_acceleration_label.setText(
        robot_config_ui.translator.get(TranslationKeys.RobotSettings.GLOBAL_ACCELERATION))

    # Update labels using stored references 
    if hasattr(robot_config_ui, '_label_translation_map'):
        for label, translation_key in robot_config_ui._label_translation_map.items():
            if translation_key == "VELOCITY":
                label.setText(f"{robot_config_ui.translator.get(TranslationKeys.RobotSettings.VELOCITY)}:")
            elif translation_key == "ACCELERATION":
                label.setText(f"{robot_config_ui.translator.get(TranslationKeys.RobotSettings.ACCELERATION)}:")

    # Update group box titles using stored references
    if hasattr(robot_config_ui, '_group_box_translation_map'):
        for group_box, original_name in robot_config_ui._group_box_translation_map.items():
            if original_name == "LOGIN_POS":
                group_box.setTitle(robot_config_ui.translator.get(TranslationKeys.RobotSettings.LOGIN_POSITION))
            elif original_name == "CALIBRATION_POS":
                group_box.setTitle(robot_config_ui.translator.get(TranslationKeys.RobotSettings.CALIBRATION_POSITION))
            elif original_name == "NOZZLE CLEAN":
                group_box.setTitle(robot_config_ui.translator.get(TranslationKeys.RobotSettings.NOZZLE_CLEANING_POSITIONS))
            elif original_name == "TOOL CHANGER":
                group_box.setTitle(robot_config_ui.translator.get(TranslationKeys.RobotSettings.TOOL_CHANGER_POSITION))
            elif "PICKUP" in original_name:
                slot_number = original_name.split()[1]
                group_box.setTitle(
                    f"{robot_config_ui.translator.get(TranslationKeys.RobotSettings.SLOT)} {slot_number} {robot_config_ui.translator.get(TranslationKeys.RobotSettings.PICKUP_POSITIONS)}")
            elif "DROPOFF" in original_name:
                slot_number = original_name.split()[1]
                group_box.setTitle(
                    f"{robot_config_ui.translator.get(TranslationKeys.RobotSettings.SLOT)} {slot_number} {robot_config_ui.translator.get(TranslationKeys.RobotSettings.DROP_POSITIONS)}")

    # Update button texts using stored button references
    # Store button references during creation and update them directly
    if hasattr(robot_config_ui, '_button_translation_map'):
        for button, translation_key in robot_config_ui._button_translation_map.items():
            if translation_key and hasattr(TranslationKeys, translation_key.split('.')[0]):
                try:
                    # Navigate to nested attribute (e.g., "RobotSettings.EXECUTE_TRAJECTORY")
                    key_parts = translation_key.split('.')
                    key_obj = TranslationKeys
                    for part in key_parts:
                        key_obj = getattr(key_obj, part)
                    button.setText(robot_config_ui.translator.get(key_obj))
                except AttributeError:
                    # Fallback: use Message enum directly
                    try:
                        from modules.shared.localization.enums.Message import Message
                        key_name = translation_key.split('.')[-1]  # Get last part
                        if hasattr(Message, key_name):
                            button.setText(robot_config_ui.translator.get(getattr(Message, key_name)))
                    except:
                        pass  # Keep original text as fallback