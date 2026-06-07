#!/usr/bin/env python3
import math
import os
import socket
import struct
import termios
import time
from glob import glob
from typing import Optional

import rclpy
from geometry_msgs.msg import PoseStamped
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node

from .pose_math import rpy_from_quat


CANFD_BRS = 0x01
CAN_RAW_FD_FRAMES = 5
CANFD_FRAME_FORMAT = "=IBBBB64s"
CANFD_FRAME_SIZE = struct.calcsize(CANFD_FRAME_FORMAT)
CANFD_DLC_BY_LENGTH = {
    0: "0",
    1: "1",
    2: "2",
    3: "3",
    4: "4",
    5: "5",
    6: "6",
    7: "7",
    8: "8",
    12: "9",
    16: "A",
    20: "B",
    24: "C",
    32: "D",
    48: "E",
    64: "F",
}


class SocketCanFdTransport:
    def __init__(self, interface: str) -> None:
        self.interface = interface
        can_raw = getattr(socket, "CAN_RAW", 1)
        sol_can_raw = getattr(socket, "SOL_CAN_RAW", 101)
        self.socket = socket.socket(socket.AF_CAN, socket.SOCK_RAW, can_raw)
        self.socket.setsockopt(sol_can_raw, CAN_RAW_FD_FRAMES, struct.pack("I", 1))
        self.socket.bind((interface,))

    def send(self, can_id: int, payload: bytes, enable_brs: bool) -> None:
        flags = CANFD_BRS if enable_brs else 0
        frame = struct.pack(
            CANFD_FRAME_FORMAT,
            can_id,
            len(payload),
            flags,
            0,
            0,
            payload.ljust(64, b"\x00"),
        )
        self.socket.send(frame)

    def close(self) -> None:
        self.socket.close()


class SlcanFdTransport:
    def __init__(
        self,
        device: str,
        nominal_speed_command: str,
        data_speed_command: str,
        auto_retransmit: bool,
    ) -> None:
        self.device = device
        self.fd = os.open(device, os.O_RDWR | os.O_NOCTTY | os.O_NONBLOCK)
        self.configure_serial_port()
        self.write_command("C")
        self.write_command(nominal_speed_command)
        self.write_command(data_speed_command)
        self.write_command("A1" if auto_retransmit else "A0")
        self.write_command("O")

    def configure_serial_port(self) -> None:
        attrs = termios.tcgetattr(self.fd)
        attrs[0] = 0
        attrs[1] = 0
        attrs[2] = termios.CLOCAL | termios.CREAD | termios.CS8
        attrs[3] = 0
        attrs[6][termios.VMIN] = 0
        attrs[6][termios.VTIME] = 0
        speed = getattr(termios, "B3000000", termios.B115200)
        attrs[4] = speed
        attrs[5] = speed
        termios.tcsetattr(self.fd, termios.TCSANOW, attrs)
        termios.tcflush(self.fd, termios.TCIOFLUSH)

    def write_command(self, command: str) -> None:
        os.write(self.fd, f"{command}\r".encode("ascii"))
        time.sleep(0.02)

    def send(self, can_id: int, payload: bytes, enable_brs: bool) -> None:
        if len(payload) not in CANFD_DLC_BY_LENGTH:
            raise ValueError(f"invalid CAN FD payload length: {len(payload)}")
        command = "b" if enable_brs else "d"
        dlc = CANFD_DLC_BY_LENGTH[len(payload)]
        line = f"{command}{can_id:03X}{dlc}{payload.hex().upper()}\r"
        os.write(self.fd, line.encode("ascii"))

    def close(self) -> None:
        self.write_command("C")
        os.close(self.fd)


class CanFdPoseSender(Node):
    def __init__(self) -> None:
        super().__init__("canfd_pose_sender")

        self.declare_parameter("pose_topic", "/lidar/pose")
        self.declare_parameter("transport", "auto")
        self.declare_parameter("can_interface", "can0")
        self.declare_parameter("serial_device", "auto")
        self.declare_parameter("can_id", 0x12)
        self.declare_parameter("send_rate_hz", 50.0)
        self.declare_parameter("enable_brs", True)
        self.declare_parameter("auto_retransmit", False)
        self.declare_parameter("yaw_offset_deg", -90.0)
        self.declare_parameter("slcan_nominal_speed_command", "S8")
        self.declare_parameter("slcan_data_speed_command", "Y2")

        self.pose_topic = self.get_parameter("pose_topic").value
        self.transport_name = self.get_parameter("transport").value
        self.can_interface = self.get_parameter("can_interface").value
        self.serial_device = self.get_parameter("serial_device").value
        self.can_id = int(self.get_parameter("can_id").value)
        self.send_rate_hz = float(self.get_parameter("send_rate_hz").value)
        self.enable_brs = bool(self.get_parameter("enable_brs").value)
        self.auto_retransmit = bool(self.get_parameter("auto_retransmit").value)
        self.slcan_nominal_speed_command = self.get_parameter(
            "slcan_nominal_speed_command"
        ).value
        self.slcan_data_speed_command = self.get_parameter(
            "slcan_data_speed_command"
        ).value
        self.yaw_offset_rad = math.radians(
            float(self.get_parameter("yaw_offset_deg").value)
        )
        self.latest_pose: Optional[PoseStamped] = None

        self.transport = self.open_transport()
        self.subscription = self.create_subscription(
            PoseStamped, self.pose_topic, self.pose_callback, 10
        )
        self.timer = self.create_timer(1.0 / self.send_rate_hz, self.timer_callback)

        self.get_logger().info(
            f"sending {self.pose_topic} as CAN FD id=0x{self.can_id:03X} "
            f"via {self.transport_name} rate={self.send_rate_hz:.1f}Hz "
            f"brs={'on' if self.enable_brs else 'off'} "
            "payload=<x,y,z,yaw float32 little-endian>"
        )

    def open_transport(self):
        transport = str(self.transport_name).lower()
        if transport == "auto":
            if os.path.exists(f"/sys/class/net/{self.can_interface}"):
                transport = "socketcan"
            elif self.find_serial_device():
                transport = "slcan_fd"
            else:
                raise RuntimeError(
                    f"neither SocketCAN {self.can_interface} nor serial "
                    f"{self.serial_device} exists"
                )

        if transport == "socketcan":
            self.transport_name = f"socketcan:{self.can_interface}"
            return SocketCanFdTransport(self.can_interface)
        if transport in ("slcan_fd", "serial", "canable2"):
            self.serial_device = self.find_serial_device(required=True)
            self.transport_name = f"slcan_fd:{self.serial_device}"
            return SlcanFdTransport(
                self.serial_device,
                self.slcan_nominal_speed_command,
                self.slcan_data_speed_command,
                self.auto_retransmit,
            )

        raise ValueError(
            "transport must be one of: auto, socketcan, slcan_fd, serial, canable2"
        )

    def find_serial_device(self, required: bool = False) -> str:
        if self.serial_device != "auto":
            if os.path.exists(self.serial_device):
                return self.serial_device
            if required:
                raise RuntimeError(f"serial device does not exist: {self.serial_device}")
            return ""

        candidates = sorted(glob("/dev/ttyACM*")) + sorted(glob("/dev/ttyUSB*"))
        if candidates:
            return candidates[0]
        if required:
            raise RuntimeError("no /dev/ttyACM* or /dev/ttyUSB* serial device found")
        return ""

    def pose_callback(self, msg: PoseStamped) -> None:
        self.latest_pose = msg

    def timer_callback(self) -> None:
        if self.latest_pose is None:
            self.get_logger().warn(
                f"waiting for {self.pose_topic}", throttle_duration_sec=2.0
            )
            return

        pose = self.latest_pose.pose
        _, _, yaw = rpy_from_quat(pose.orientation)
        yaw = self.normalize_angle(yaw + self.yaw_offset_rad)

        payload = struct.pack(
            "<ffff",
            float(pose.position.x),
            float(pose.position.y),
            float(pose.position.z),
            float(yaw),
        )
        try:
            self.transport.send(self.can_id, payload, self.enable_brs)
        except OSError as exc:
            self.get_logger().error(f"failed to send CAN FD frame: {exc}")

    @staticmethod
    def normalize_angle(angle: float) -> float:
        return math.atan2(math.sin(angle), math.cos(angle))

    def destroy_node(self) -> bool:
        self.transport.close()
        return super().destroy_node()


def main() -> None:
    rclpy.init()
    node = CanFdPoseSender()
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == "__main__":
    main()
