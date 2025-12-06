from dataclasses import dataclass


@dataclass
class GrippersConfig:
    """Configuration for gripper offsets and positioning."""
    gripper_x_offset: float  # mm, between transducer and gripper tip measured at rz = 0
    gripper_y_offset: float  # mm, between transducer and gripper tip measured at rz = 0
    double_gripper_z_offset: float  # mm, between transducer and gripper tip
    single_gripper_z_offset: float  # mm, between transducer and gripper tip