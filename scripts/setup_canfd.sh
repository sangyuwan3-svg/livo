#!/usr/bin/env bash
set -euo pipefail

IFACE="${1:-can0}"
BITRATE="${2:-1000000}"
DBITRATE="${3:-2000000}"

sudo ip link set "${IFACE}" down 2>/dev/null || true
sudo ip link set "${IFACE}" txqueuelen 1000
sudo ip link set "${IFACE}" type can \
  bitrate "${BITRATE}" \
  dbitrate "${DBITRATE}" \
  fd on \
  one-shot on
sudo ip link set "${IFACE}" up

ip -details link show "${IFACE}"
