#!/usr/bin/env bash
set -euo pipefail

WORKSPACE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SDK_SRC="${WORKSPACE_DIR}/third_party/Livox-SDK2"
SDK_INSTALL="${SDK_SRC}/install"

set +u
source /opt/ros/humble/setup.bash
set -u

cmake -S "${SDK_SRC}" -B "${SDK_SRC}/build" \
  -DCMAKE_BUILD_TYPE=Release \
  -DCMAKE_INSTALL_PREFIX="${SDK_INSTALL}"
cmake --build "${SDK_SRC}/build" --parallel "$(nproc)"
cmake --install "${SDK_SRC}/build"

cp -f "${WORKSPACE_DIR}/src/livox_ros_driver2/package_ROS2.xml" \
  "${WORKSPACE_DIR}/src/livox_ros_driver2/package.xml"

export LIVOX_LIDAR_SDK_ROOT="${SDK_INSTALL}"
export LD_LIBRARY_PATH="${SDK_INSTALL}/lib:${LD_LIBRARY_PATH:-}"

colcon build \
  --base-paths "${WORKSPACE_DIR}/src" \
  --cmake-args \
    -DROS_EDITION=ROS2 \
    -DDISTRO_ROS=humble \
    -DLIVOX_LIDAR_SDK_ROOT="${SDK_INSTALL}" \
    -DCMAKE_BUILD_TYPE=Release
