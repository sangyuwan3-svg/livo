#!/usr/bin/env bash
set -euo pipefail

WORKSPACE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source "${WORKSPACE_DIR}/scripts/source_lidar.sh"

echo "ROS_DISTRO=${ROS_DISTRO:-}"
echo "LIVOX_LIDAR_SDK_ROOT=${LIVOX_LIDAR_SDK_ROOT:-}"
echo "LD_LIBRARY_PATH=${LD_LIBRARY_PATH:-}"
echo
ros2 pkg prefix livox_ros_driver2
ros2 pkg prefix lidar_bringup
echo
ros2 interface show livox_ros_driver2/msg/CustomMsg
