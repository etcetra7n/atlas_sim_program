import rclpy
from rclpy.node import Node

from sensor_msgs.msg import Image
from cv_bridge import CvBridge

import cv2
import numpy as np


class DepthViewer(Node):
    def __init__(self):
        super().__init__("depth_viewer")

        self.bridge = CvBridge()

        self.subscription = self.create_subscription(
            Image,
            "/depth/image",
            self.image_callback,
            10,
        )

        self.get_logger().info("Depth viewer started")

    def image_callback(self, msg: Image):
        try:
            depth = self.bridge.imgmsg_to_cv2(
                msg,
                desired_encoding="32FC1",
            )

            # Replace invalid values
            depth = np.nan_to_num(
                depth,
                nan=0.0,
                posinf=0.0,
                neginf=0.0,
            )

            # Ignore zeros when computing range
            valid = depth[depth > 0]

            if len(valid) == 0:
                self.get_logger().warn(
                    "No valid depth pixels"
                )
                return

            min_depth = valid.min()
            max_depth = valid.max()

            # Normalize to 0-255
            normalized = np.interp(
                depth,
                (min_depth, max_depth),
                (0, 255),
            ).astype(np.uint8)

            # Apply false color
            colored = cv2.applyColorMap(
                normalized,
                cv2.COLORMAP_JET,
            )

            # Display min/max depth
            cv2.putText(
                colored,
                f"Min: {min_depth:.2f}m",
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (255, 255, 255),
                2,
            )

            cv2.putText(
                colored,
                f"Max: {max_depth:.2f}m",
                (10, 60),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (255, 255, 255),
                2,
            )

            cv2.imshow("Depth Image", colored)
            cv2.waitKey(1)

        except Exception as e:
            self.get_logger().error(str(e))


def main(args=None):
    rclpy.init(args=args)

    node = DepthViewer()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass

    cv2.destroyAllWindows()
    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
