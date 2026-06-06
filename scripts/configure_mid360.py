#!/usr/bin/env python3
import argparse
import ipaddress
import json
from pathlib import Path


def ip(value: str) -> str:
    return str(ipaddress.ip_address(value))


def main() -> None:
    workspace = Path(__file__).resolve().parents[1]
    source_config = (
        workspace / "src" / "lidar_bringup" / "config" / "mid360_config.json"
    )
    installed_config = (
        workspace
        / "install"
        / "lidar_bringup"
        / "share"
        / "lidar_bringup"
        / "config"
        / "mid360_config.json"
    )

    parser = argparse.ArgumentParser(
        description="Update lidar_bringup MID-360 JSON network settings."
    )
    parser.add_argument("--host-ip", required=True, type=ip)
    parser.add_argument("--lidar-ip", required=True, type=ip)
    parser.add_argument(
        "--config",
        type=Path,
        help="Only update this config file instead of the source and installed configs.",
    )
    args = parser.parse_args()

    configs = [args.config] if args.config else [source_config]
    if not args.config and installed_config.exists():
        configs.append(installed_config)

    for config in configs:
        with config.open("r", encoding="utf-8") as handle:
            data = json.load(handle)

        host = data["MID360"]["host_net_info"]
        host["host_ip"] = args.host_ip
        data["lidar_configs"][0]["ip"] = args.lidar_ip

        with config.open("w", encoding="utf-8") as handle:
            json.dump(data, handle, indent=2)
            handle.write("\n")

        print(f"Updated {config}")

    print(f"host_ip={args.host_ip}")
    print(f"lidar_ip={args.lidar_ip}")


if __name__ == "__main__":
    main()
