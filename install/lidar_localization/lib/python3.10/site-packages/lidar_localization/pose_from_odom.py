#!/usr/bin/env python3
import math
from typing import Optional

import rclpy
from geometry_msgs.msg import PointStamped, Pose, PoseStamped, TransformStamped
from nav_msgs.msg import Odometry
from rclpy.node import Node
from tf2_ros import TransformBroadcaster

from .pose_math import point_from_iter, quat_from_rpy, quat_multiply, rotate_point, rpy_from_quat


class PoseFromOdom(Node):
    """Expose a stable LiDAR pose interface from a LIO/SLAM odometry topic."""

    def __init__(self) -> None:
        super().__init__("lidar_pose_from_odom")

        self.declare_parameter("input_odom_topic", "/Odometry")
        self.declare_parameter("output_pose_topic", "/lidar/pose")
        self.declare_parameter("output_point_topic", "/lidar/point")
        self.declare_parameter("output_odom_topic", "/lidar/odom")
        self.declare_parameter("lidar_frame", "livox_frame")
        self.declare_parameter("base_frame", "base_link")
        self.declare_parameter("publish_tf", False)
        self.declare_parameter("output_base_frame", False)
        self.declare_parameter("lidar_to_base_xyz", [0.0, 0.0, 0.0])
        self.declare_parameter("lidar_to_base_rpy", [0.0, 0.0, 0.0])
        self.declare_parameter("log_period_sec", 1.0)

        self.input_odom_topic = self.get_parameter("input_odom_topic").value
        self.output_pose_topic = self.get_parameter("output_pose_topic").value
        self.output_point_topic = self.get_parameter("output_point_topic").value
        self.output_odom_topic = self.get_parameter("output_odom_topic").value
        self.lidar_frame = self.get_parameter("lidar_frame").value
        self.base_frame = self.get_parameter("base_frame").value
        self.publish_tf = bool(self.get_parameter("publish_tf").value)
        self.output_base_frame = bool(self.get_parameter("output_base_frame").value)
        self.log_period_sec = float(self.get_parameter("log_period_sec").value)

        self.lidar_to_base_translation = point_from_iter(
            self.get_parameter("lidar_to_base_xyz").value
        )
        lidar_to_base_rpy = [float(v) for v in self.get_parameter("lidar_to_base_rpy").value]
        self.lidar_to_base_rotation = quat_from_rpy(*lidar_to_base_rpy)

        self.pose_pub = self.create_publisher(PoseStamped, self.output_pose_topic, 10)
        self.point_pub = self.create_publisher(PointStamped, self.output_point_topic, 10)
        self.odom_pub = self.create_publisher(Odometry, self.output_odom_topic, 10)
        self.tf_broadcaster: Optional[TransformBroadcaster] = (
            TransformBroadcaster(self) if self.publish_tf else None
        )

        self.last_log_time = self.get_clock().now()
        self.subscription = self.create_subscription(
            Odometry,
            self.input_odom_topic,
            self.odom_callback,
            20,
        )

        target = self.base_frame if self.output_base_frame else self.lidar_frame
        self.get_logger().info(
            f"waiting for {self.input_odom_topic}; publishing {target} pose on "
            f"{self.output_pose_topic} and point on {self.output_point_topic}"
        )

    def odom_callback(self, msg: Odometry) -> None:
        pose = msg.pose.pose
        child_frame = self.lidar_frame

        if self.output_base_frame:
            pose = self.compose_lidar_to_base(pose)
            child_frame = self.base_frame

        pose_msg = PoseStamped()
        pose_msg.header = msg.header
        pose_msg.pose = pose
        self.pose_pub.publish(pose_msg)

        point_msg = PointStamped()
        point_msg.header = msg.header
        point_msg.point = pose.position
        self.point_pub.publish(point_msg)

        odom_msg = Odometry()
        odom_msg.header = msg.header
        odom_msg.child_frame_id = child_frame
        odom_msg.pose.pose = pose
        odom_msg.pose.covariance = msg.pose.covariance
        odom_msg.twist = msg.twist
        self.odom_pub.publish(odom_msg)

        if self.tf_broadcaster:
            self.broadcast_tf(msg.header.frame_id, child_frame, pose_msg)

        self.log_pose(pose_msg, child_frame)

    def compose_lidar_to_base(self, lidar_pose: Pose) -> Pose:
        rotated_offset = rotate_point(
            lidar_pose.orientation, self.lidar_to_base_translation
        )
        base_pose = Pose()
        base_pose.position.x = lidar_pose.position.x + rotated_offset.x
        base_pose.position.y = lidar_pose.position.y + rotated_offset.y
        base_pose.position.z = lidar_pose.position.z + rotated_offset.z
        base_pose.orientation = quat_multiply(
            lidar_pose.orientation, self.lidar_to_base_rotation
        )
        return base_pose

    def broadcast_tf(self, parent_frame: str, child_frame: str, pose_msg: PoseStamped) -> None:
        transform = TransformStamped()
        transform.header = pose_msg.header
        transform.header.frame_id = parent_frame
        transform.child_frame_id = child_frame
        transform.transform.translation.x = pose_msg.pose.position.x
        transform.transform.translation.y = pose_msg.pose.position.y
        transform.transform.translation.z = pose_msg.pose.position.z
        transform.transform.rotation = pose_msg.pose.orientation
        self.tf_broadcaster.sendTransform(transform)

    def log_pose(self, pose_msg: PoseStamped, child_frame: str) -> None:
        now = self.get_clock().now()
        if (now - self.last_log_time).nanoseconds < self.log_period_sec * 1e9:
            return
        self.last_log_time = now

        roll, pitch, yaw = rpy_from_quat(pose_msg.pose.orientation)
        p = pose_msg.pose.position
        self.get_logger().info(
            f"{child_frame} in {pose_msg.header.frame_id}: "
            f"x={p.x:.3f} y={p.y:.3f} z={p.z:.3f} "
            f"roll={math.degrees(roll):.2f}deg "
            f"pitch={math.degrees(pitch):.2f}deg "
            f"yaw={math.degrees(yaw):.2f}deg"
        )


def main() -> None:
    rclpy.init()
    node = PoseFromOdom()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
