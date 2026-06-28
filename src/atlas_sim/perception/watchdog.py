#!/usr/bin/env python3

import struct

import rclpy
from rclpy.node import Node

from sensor_msgs.msg import Image
from sensor_msgs.msg import CameraInfo

class PerceptionNode(Node):
    def __init__(self):
        super().__init__("perception_node")
        self.camera_info = None
        self.create_subscription(
            CameraInfo,
            "/camera_info",
            self.camera_info_callback,
            10,
        )
        self.create_subscription(
            Image,
            "/depth/image",
            self.image_callback,
            10,
        )
        self.get_logger().info("Waiting for depth images...")

    def camera_info_callback(self, msg: CameraInfo):
        print(msg)
        self.camera_info = msg

    def image_callback(self, msg: Image):
        width = msg.width
        height = msg.height
        center_x = width // 2
        center_y = height // 2
        try:
            if msg.encoding == "32FC1":
                index = center_y * width + center_x
                depth = struct.unpack_from(
                    "f",
                    msg.data,
                    index * 4,
                )[0]
            elif msg.encoding == "16UC1":
                index = center_y * width + center_x
                depth_mm = struct.unpack_from(
                    "H",
                    msg.data,
                    index * 2,
                )[0]
                depth = depth_mm / 1000.0
            else:
                self.get_logger().warn(
                    f"Unsupported encoding: {msg.encoding}"
                )
                return
        except Exception as e:
            self.get_logger().error(str(e))
            return
        print("\n" + "=" * 60)
        print(
            f"Image: {width}x{height} "
            f"encoding={msg.encoding}"
        )
        print(
            f"Center depth: {depth:.3f} m"
        )

        if self.camera_info:
            fx = self.camera_info.k[0]
            fy = self.camera_info.k[4]
            cx = self.camera_info.k[2]
            cy = self.camera_info.k[5]
            print(
                f"fx={fx:.2f} "
                f"fy={fy:.2f} "
                f"cx={cx:.2f} "
                f"cy={cy:.2f}"
            )
        print("=" * 60)

def main():
    rclpy.init()
    node = PerceptionNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass

    node.destroy_node()
    rclpy.shutdown()

if __name__ == "__main__":
    main()
