#!/usr/bin/env bash
set -euo pipefail

WORKSPACE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source "${WORKSPACE_DIR}/scripts/source_lidar.sh"

mkdir -p "${WORKSPACE_DIR}/bags"
ros2 bag record \
  /livox/lidar \
  /livox/imu \
  /Odometry \
  /lidar/pose \
  /lidar/point \
  /tf \
  /tf_static \
  -o "${WORKSPACE_DIR}/bags/mid360_localization_$(date +%Y%m%d_%H%M%S)"
