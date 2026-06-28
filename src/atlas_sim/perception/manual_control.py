#!/usr/bin/env python3

import sys
import threading
import termios
import tty
import select

import rclpy
from rclpy.node import Node

from geometry_msgs.msg import Twist

class ManualControl(Node):
    def __init__(self):
        super().__init__("manual_control")
        self.publisher = self.create_publisher(
            Twist,
            "/cmd_vel",
            10
        )

        self.linear_speed = 1.0
        self.angular_speed = 2.0

        self.msg = Twist()
        self.lock = threading.Lock()
        self.settings = termios.tcgetattr(sys.stdin)
        tty.setcbreak(sys.stdin.fileno())
        self.timer = self.create_timer(
            0.2,
            self.publish_cmd
        )

        self.keyboard_thread = threading.Thread(
            target=self.keyboard_loop,
            daemon=True
        )
        self.keyboard_thread.start()
        self.get_logger().info("""

Controls
========
W : Forward
S : Backward
A : Rotate Left
D : Rotate Right
Q : Quit
""")

    def keyboard_loop(self):
        while rclpy.ok():
            if select.select([sys.stdin], [], [], 0.05)[0]:
                key = sys.stdin.read(1)
                if key == "\x1b":
                    key += sys.stdin.read(2)

                with self.lock:
                    self.msg = Twist()

                    if key.lower() == "w":
                        self.msg.linear.x = self.linear_speed
                    elif key.lower() == "s":
                        self.msg.linear.x = -self.linear_speed
                    elif key.lower() == "a":
                        self.msg.angular.z = self.angular_speed
                    elif key.lower() == "d":
                        self.msg.angular.z = -self.angular_speed
                    elif key.lower() == "q":
                        rclpy.shutdown()
                        return
            else:
                with self.lock:
                    self.msg = Twist()

    def publish_cmd(self):
        with self.lock:
            self.publisher.publish(self.msg)

    def destroy_node(self):
        termios.tcsetattr(
            sys.stdin,
            termios.TCSADRAIN,
            self.settings
        )
        super().destroy_node()

def main(args=None):
    rclpy.init(args=args)
    node = ManualControl()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()

if __name__ == "__main__":
    main()
