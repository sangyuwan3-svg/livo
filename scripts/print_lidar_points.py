#!/usr/bin/env python3
import argparse
import math
<<<<<<< ours
from typing import Any, Iterable, Sequence

import rclpy
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
=======
from typing import Iterable, Sequence

import rclpy
from rclpy.node import Node
>>>>>>> theirs
from sensor_msgs.msg import PointCloud2
from sensor_msgs_py import point_cloud2


<<<<<<< ours
def scalar(value: Any) -> Any:
    return value.item() if hasattr(value, "item") else value


def point_to_dict(point: Any, field_names: Sequence[str]) -> dict[str, Any]:
    if hasattr(point, "dtype") and point.dtype.names:
        return {name: scalar(point[name]) for name in field_names}
    values = point.tolist() if hasattr(point, "tolist") else point
    return {name: scalar(value) for name, value in zip(field_names, values)}


def finite_xyz(point: dict[str, Any]) -> bool:
    return all(math.isfinite(float(point[name])) for name in ("x", "y", "z"))


def distance(point: dict[str, Any]) -> float:
    x = float(point["x"])
    y = float(point["y"])
    z = float(point["z"])
=======
def finite_xyz(point: Sequence[float]) -> bool:
    return all(math.isfinite(float(value)) for value in point[:3])


def distance(point: Sequence[float]) -> float:
    x, y, z = (float(value) for value in point[:3])
>>>>>>> theirs
    return math.sqrt(x * x + y * y + z * z)


class PointPrinter(Node):
    def __init__(self, args: argparse.Namespace) -> None:
        super().__init__("print_lidar_points")
        self.args = args
        self.printed_messages = 0
        self.subscription = self.create_subscription(
<<<<<<< ours
            PointCloud2, args.topic, self.callback, qos_profile_sensor_data
=======
            PointCloud2, args.topic, self.callback, 10
>>>>>>> theirs
        )

    def callback(self, msg: PointCloud2) -> None:
        fields = [field.name for field in msg.fields]
        preferred = ["x", "y", "z", "intensity", "reflectivity", "tag", "line"]
        field_names = [name for name in preferred if name in fields]
        if "x" not in field_names or "y" not in field_names or "z" not in field_names:
            self.get_logger().error(f"{self.args.topic} has no x/y/z fields: {fields}")
            rclpy.shutdown()
            return

<<<<<<< ours
        raw_points = point_cloud2.read_points(
            msg,
            field_names=field_names,
            skip_nans=True,
        )
        points = [
            point_to_dict(point, field_names)
            for point in raw_points
        ]
        points = [
            point
            for point in points
            if finite_xyz(point)
        ]
=======
        points = list(
            point_cloud2.read_points(
                msg,
                field_names=field_names,
                skip_nans=True,
            )
        )
        points = [point for point in points if finite_xyz(point)]
>>>>>>> theirs
        if not points:
            self.get_logger().warn("received point cloud, but no finite xyz points")
            return

        print(f"\nframe={msg.header.frame_id} stamp={msg.header.stamp.sec}.{msg.header.stamp.nanosec:09d} points={len(points)}")

        if self.args.nearest:
            point = min(points, key=distance)
            self.print_point("nearest", point, field_names)
        else:
            step = max(1, self.args.step)
            count = 0
            for index, point in enumerate(points[::step]):
                self.print_point(str(index * step), point, field_names)
                count += 1
                if count >= self.args.count:
                    break

        self.printed_messages += 1
        if self.printed_messages >= self.args.messages:
            rclpy.shutdown()

<<<<<<< ours
    def print_point(self, label: str, point: dict[str, Any], field_names: Iterable[str]) -> None:
        x = float(point["x"])
        y = float(point["y"])
        z = float(point["z"])
        parts = [f"{label}: x={x:.3f} y={y:.3f} z={z:.3f} range={distance(point):.3f}m"]
        for name in ("intensity", "reflectivity", "tag", "line"):
            if name in field_names and name in point:
                parts.append(f"{name}={point[name]}")
=======
    def print_point(self, label: str, point: Sequence[float], field_names: Iterable[str]) -> None:
        values = dict(zip(field_names, point))
        x = float(values["x"])
        y = float(values["y"])
        z = float(values["z"])
        parts = [f"{label}: x={x:.3f} y={y:.3f} z={z:.3f} range={distance(point):.3f}m"]
        for name in ("intensity", "reflectivity", "tag", "line"):
            if name in values:
                parts.append(f"{name}={values[name]}")
>>>>>>> theirs
        print(" ".join(parts))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Print xyz coordinates from a ROS 2 PointCloud2 topic."
    )
    parser.add_argument("--topic", default="/livox/lidar")
    parser.add_argument("--count", type=int, default=10, help="points to print per cloud")
    parser.add_argument("--messages", type=int, default=1, help="cloud messages to print")
    parser.add_argument("--step", type=int, default=100, help="sample every Nth point")
    parser.add_argument("--nearest", action="store_true", help="print only the nearest point")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    rclpy.init()
    node = PointPrinter(args)
    rclpy.spin(node)
    node.destroy_node()


if __name__ == "__main__":
    main()
