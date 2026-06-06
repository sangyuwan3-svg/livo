from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    start_driver = LaunchConfiguration("start_driver")
    start_fast_lio = LaunchConfiguration("start_fast_lio")
    start_pose_interface = LaunchConfiguration("start_pose_interface")
    fast_lio_rviz = LaunchConfiguration("fast_lio_rviz")
    input_odom_topic = LaunchConfiguration("input_odom_topic")

    driver_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution(
                [
                    FindPackageShare("lidar_bringup"),
                    "launch",
                    "mid360_custom_msg.launch.py",
                ]
            )
        ),
        condition=IfCondition(start_driver),
    )

    fast_lio_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution(
                [FindPackageShare("fast_lio"), "launch", "mapping.launch.py"]
            )
        ),
        launch_arguments={
            "config_file": "mid360.yaml",
            "rviz": fast_lio_rviz,
        }.items(),
        condition=IfCondition(start_fast_lio),
    )

    pose_interface_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution(
                [
                    FindPackageShare("lidar_localization"),
                    "launch",
                    "lidar_pose_from_odom.launch.py",
                ]
            )
        ),
        launch_arguments={"input_odom_topic": input_odom_topic}.items(),
        condition=IfCondition(start_pose_interface),
    )

    return LaunchDescription(
        [
            DeclareLaunchArgument("start_driver", default_value="true"),
            DeclareLaunchArgument("start_fast_lio", default_value="true"),
            DeclareLaunchArgument("start_pose_interface", default_value="true"),
            DeclareLaunchArgument("fast_lio_rviz", default_value="false"),
            DeclareLaunchArgument("input_odom_topic", default_value="/Odometry"),
            driver_launch,
            fast_lio_launch,
            pose_interface_launch,
        ]
    )
