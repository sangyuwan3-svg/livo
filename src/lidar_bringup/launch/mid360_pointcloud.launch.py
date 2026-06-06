from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    config_path = LaunchConfiguration("config_path")
    frame_id = LaunchConfiguration("frame_id")
    publish_freq = LaunchConfiguration("publish_freq")
    multi_topic = LaunchConfiguration("multi_topic")
    rviz = LaunchConfiguration("rviz")

    driver = Node(
        package="livox_ros_driver2",
        executable="livox_ros_driver2_node",
        name="livox_lidar_publisher",
        output="screen",
        parameters=[
            {
                "xfer_format": 0,
                "multi_topic": ParameterValue(multi_topic, value_type=int),
                "data_src": 0,
                "publish_freq": ParameterValue(publish_freq, value_type=float),
                "output_data_type": 0,
                "frame_id": frame_id,
                "lvx_file_path": "",
                "user_config_path": config_path,
                "cmdline_input_bd_code": "livox0000000001",
            }
        ],
    )

    rviz_node = Node(
        condition=IfCondition(rviz),
        package="rviz2",
        executable="rviz2",
        name="rviz2",
        output="screen",
        arguments=[
            "-d",
            PathJoinSubstitution(
                [FindPackageShare("lidar_bringup"), "rviz", "mid360.rviz"]
            ),
        ],
    )

    return LaunchDescription(
        [
            DeclareLaunchArgument(
                "config_path",
                default_value=PathJoinSubstitution(
                    [FindPackageShare("lidar_bringup"), "config", "mid360_config.json"]
                ),
            ),
            DeclareLaunchArgument("frame_id", default_value="livox_frame"),
            DeclareLaunchArgument("publish_freq", default_value="10.0"),
            DeclareLaunchArgument("multi_topic", default_value="0"),
            DeclareLaunchArgument("rviz", default_value="true"),
            driver,
            rviz_node,
        ]
    )
