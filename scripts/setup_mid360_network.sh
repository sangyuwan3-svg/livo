#!/usr/bin/env bash
set -euo pipefail

IFACE="${1:-}"
CIDR="${2:-192.168.1.50/24}"

if [[ -z "${IFACE}" ]]; then
  echo "Usage: $0 <ethernet-interface> [host-cidr]"
  echo
  echo "Available interfaces:"
  ip -br link
  exit 2
fi

sudo ip link set "${IFACE}" up
sudo ip addr replace "${CIDR}" dev "${IFACE}"

echo "Configured ${IFACE}:"
ip -br addr show "${IFACE}"
