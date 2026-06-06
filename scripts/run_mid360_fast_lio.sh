#!/usr/bin/env bash
set -euo pipefail

WORKSPACE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source "${WORKSPACE_DIR}/scripts/source_lidar.sh"

cd "${WORKSPACE_DIR}"
ros2 launch lidar_bringup mid360_fast_lio.launch.py "$@"
