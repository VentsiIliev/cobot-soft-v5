# Running without ROS2 available — provide lightweight stubs so module can be imported
class _RCLPyStub:
    @staticmethod
    def spin_once(node, timeout_sec=0.0):
        return None

rclpy = _RCLPyStub()


class Node:
    def __init__(self, name=None):
        pass

    def create_publisher(self, msg_type, topic, qos):
        class _Pub:
            def publish(self, msg):
                return None
        return _Pub()

    def create_subscription(self, msg_type, topic, callback, qos):
        return None

    def create_client(self, srv_type, srv_name):
        class _Client:
            def service_is_ready(self):
                return False

            def call_async(self, req):
                class _Future:
                    def done(self):
                        return False

                    def result(self):
                        return None

                    def add_done_callback(self, cb):
                        return None
                return _Future()
        return _Client()

    def create_timer(self, period, callback):
        return None


class ActionClient:
    pass


class Pose:
    def __init__(self):
        class _P:
            x = 0.0
            y = 0.0
            z = 0.0

        class _O:
            x = 0.0
            y = 0.0
            z = 0.0
            w = 1.0

        self.position = _P()
        self.orientation = _O()


class PoseStamped:
    def __init__(self):
        self.pose = Pose()


class PoseArray:
    def __init__(self):
        class _H:
            frame_id = ''

        self.header = _H()
        self.poses = []


class Float64MultiArray:
    def __init__(self):
        self.data = []


class Float32MultiArray:
    def __init__(self):
        self.data = []


class Int32MultiArray:
    def __init__(self):
        self.data = []


class Bool:
    def __init__(self, data=False):
        self.data = data


class JointState:
    def __init__(self):
        self.position = []
        self.name = []


# MoveIt message stubs
class MotionSequenceRequest:
    """Stub for moveit_msgs.msg.MotionSequenceRequest"""
    def __init__(self):
        pass


class GetPositionFK:
    """Stub for moveit_msgs.srv.GetPositionFK"""
    class Request:
        def __init__(self):
            class _Header:
                frame_id = ''

            class _RobotState:
                def __init__(self):
                    self.joint_state = JointState()

            self.header = _Header()
            self.fk_link_names = []
            self.robot_state = _RobotState()

    class Response:
        def __init__(self):
            self.pose_stamped = []


MoveGroup = object