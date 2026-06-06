from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    params_file = LaunchConfiguration("params_file")
    input_odom_topic = LaunchConfiguration("input_odom_topic")

    return LaunchDescription(
        [
            DeclareLaunchArgument(
                "params_file",
                default_value=PathJoinSubstitution(
                    [
                        FindPackageShare("lidar_localization"),
                        "config",
                        "lidar_pose_interface.yaml",
                    ]
                ),
            ),
            DeclareLaunchArgument("input_odom_topic", default_value="/Odometry"),
            Node(
                package="lidar_localization",
                executable="pose_from_odom",
                name="lidar_pose_from_odom",
                output="screen",
                parameters=[
                    params_file,
                    {"input_odom_topic": input_odom_topic},
                ],
            ),
        ]
    )
