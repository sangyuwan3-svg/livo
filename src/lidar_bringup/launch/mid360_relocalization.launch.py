from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    start_driver = LaunchConfiguration("start_driver")
    start_fast_lio = LaunchConfiguration("start_fast_lio")
    start_map_localizer = LaunchConfiguration("start_map_localizer")
    start_pose_interface = LaunchConfiguration("start_pose_interface")
    fast_lio_rviz = LaunchConfiguration("fast_lio_rviz")
    map_path = LaunchConfiguration("map_path")

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
            "config_path": PathJoinSubstitution(
                [FindPackageShare("fast_lio"), "config"]
            ),
            "config_file": "mid360.yaml",
            "rviz": fast_lio_rviz,
            "rviz_cfg": PathJoinSubstitution(
                [
                    FindPackageShare("lidar_bringup"),
                    "rviz",
                    "mid360_relocalization.rviz",
                ]
            ),
        }.items(),
        condition=IfCondition(start_fast_lio),
    )

    map_localizer = Node(
        package="lidar_map_localization",
        executable="map_localizer",
        name="map_localizer",
        output="screen",
        parameters=[
            PathJoinSubstitution(
                [
                    FindPackageShare("lidar_map_localization"),
                    "config",
                    "map_localizer.yaml",
                ]
            ),
            {"map_path": map_path},
        ],
        condition=IfCondition(start_map_localizer),
    )

    pose_interface = Node(
        package="lidar_localization",
        executable="pose_from_odom",
        name="lidar_pose_from_odom",
        output="screen",
        parameters=[
            PathJoinSubstitution(
                [
                    FindPackageShare("lidar_localization"),
                    "config",
                    "lidar_pose_interface.yaml",
                ]
            ),
            {
                "input_odom_topic": "/map_lidar/odom",
                "zero_on_first_pose": False,
                "zero_frame_id": "map",
            },
        ],
        condition=IfCondition(start_pose_interface),
    )

    return LaunchDescription(
        [
            DeclareLaunchArgument("start_driver", default_value="true"),
            DeclareLaunchArgument("start_fast_lio", default_value="true"),
            DeclareLaunchArgument("start_map_localizer", default_value="true"),
            DeclareLaunchArgument("start_pose_interface", default_value="true"),
            DeclareLaunchArgument("fast_lio_rviz", default_value="true"),
            DeclareLaunchArgument(
                "map_path",
                default_value="/home/sangyuwan/lidar/maps/mid360_map.pcd",
            ),
            driver_launch,
            fast_lio_launch,
            map_localizer,
            pose_interface,
        ]
    )
