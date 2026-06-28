#!/usr/bin/env python3

from pynput import keyboard

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist

class Controls(Node):
    def __init__(self):
        super().__init__("controls")

        self.publisher = self.create_publisher(
            Twist,
            "/cmd_vel",
            10
        )

        self.linear_speed = 1.0
        self.angular_speed = 2.0

        self.keys = set()

        self.timer = self.create_timer(
            0.1,
            self.publish_cmd
        )

        self.listener = keyboard.Listener(
            on_press=self.on_press,
            on_release=self.on_release
        )
        self.listener.start()

        self.get_logger().info("""
Controls
========
W : Forward
S : Backward
A : Rotate Left
D : Rotate Right
""")

    def on_press(self, key):
        try:
            self.keys.add(key.char.lower())
        except AttributeError:
            pass

    def on_release(self, key):
        try:
            self.keys.discard(key.char.lower())

        except AttributeError:
            pass

    def publish_cmd(self):
        msg = Twist()

        if "w" in self.keys:
            msg.linear.x += self.linear_speed
        if "s" in self.keys:
            msg.linear.x -= self.linear_speed
        if "a" in self.keys:
            msg.angular.z += self.angular_speed
        if "d" in self.keys:
            msg.angular.z -= self.angular_speed

        self.publisher.publish(msg)

def main(args=None):
    rclpy.init(args=args)
    node = Controls()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.listener.stop()
        node.destroy_node()

        if rclpy.ok():
            rclpy.shutdown()

if __name__ == "__main__":
    main()