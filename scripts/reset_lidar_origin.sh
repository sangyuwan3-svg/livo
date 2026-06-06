#!/usr/bin/env bash
set -euo pipefail

WORKSPACE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source "${WORKSPACE_DIR}/scripts/source_lidar.sh"

ros2 service call /lidar/reset_origin std_srvs/srv/Trigger "{}"
