#!/usr/bin/env bash
WORKSPACE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SDK_INSTALL="${WORKSPACE_DIR}/third_party/Livox-SDK2/install"

_restore_nounset=0
if [[ $- == *u* ]]; then
  _restore_nounset=1
  set +u
fi

source /opt/ros/humble/setup.bash
export LIVOX_LIDAR_SDK_ROOT="${SDK_INSTALL}"
export LD_LIBRARY_PATH="${SDK_INSTALL}/lib:${LD_LIBRARY_PATH:-}"
source "${WORKSPACE_DIR}/install/setup.bash"

if [[ "${_restore_nounset}" -eq 1 ]]; then
  set -u
fi
unset _restore_nounset
