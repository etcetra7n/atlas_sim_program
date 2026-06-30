#!/usr/bin/env python3

import cv2
import numpy as np
import pygame

import rclpy
from rclpy.node import Node

from geometry_msgs.msg import Twist
from sensor_msgs.msg import Image
from cv_bridge import CvBridge

class SimWindow(Node):
    def __init__(self):
        super().__init__("sim_window")
        self.bridge = CvBridge()
        self.publisher = self.create_publisher(
            Twist,
            "/cmd_vel",
            10,
        )
        self.subscription = self.create_subscription(
            Image,
            "/depth/image",
            self.image_callback,
            10,
        )

        self.linear_speed = 1.0
        self.angular_speed = 2.0

        self.latest_surface = None
        self.min_depth = 0.0
        self.max_depth = 0.0

        pygame.init()
        pygame.font.init()

        self.font = pygame.font.SysFont(None, 28)

        self.width = 960
        self.height = 540

        self.screen = pygame.display.set_mode(
            (self.width, self.height)
        )
        pygame.display.set_caption("Atlas Simulator")
        self.clock = pygame.time.Clock()
        self.timer = self.create_timer(
            0.02,      # 50 Hz
            self.update
        )
        self.get_logger().info("""
====================================
 Atlas Simulator
====================================

Click the window once.

W : Forward
S : Reverse
A : Rotate Left
D : Rotate Right
ESC : Quit

====================================
""")

    def image_callback(self, msg: Image):

        try:
            depth = self.bridge.imgmsg_to_cv2(
                msg,
                desired_encoding="32FC1",
            )

            depth = np.nan_to_num(
                depth,
                nan=0.0,
                posinf=0.0,
                neginf=0.0,
            )

            valid = depth[depth > 0]

            if valid.size == 0:
                return

            self.min_depth = float(valid.min())
            self.max_depth = float(valid.max())

            normalized = np.interp(
                depth,
                (self.min_depth, self.max_depth),
                (0, 255),
            ).astype(np.uint8)

            colored = cv2.applyColorMap(
                normalized,
                cv2.COLORMAP_JET,
            )

            rgb = cv2.cvtColor(
                colored,
                cv2.COLOR_BGR2RGB,
            )

            surface = pygame.surfarray.make_surface(
                np.transpose(rgb, (1, 0, 2))
            )

            self.latest_surface = surface

        except Exception as e:
            self.get_logger().error(str(e))

    def update(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                rclpy.shutdown()
                return

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    rclpy.shutdown()
                    return
        keys = pygame.key.get_pressed()
        msg = Twist()

        if keys[pygame.K_w]:
            msg.linear.x += self.linear_speed
        if keys[pygame.K_s]:
            msg.linear.x -= self.linear_speed
        if keys[pygame.K_a]:
            msg.angular.z += self.angular_speed
        if keys[pygame.K_d]:
            msg.angular.z -= self.angular_speed

        self.publisher.publish(msg)
        self.screen.fill((25, 25, 25))

        if self.latest_surface is not None:
            image = pygame.transform.scale(
                self.latest_surface,
                (self.width, self.height),
            )
            self.screen.blit(image, (0, 0))

        # Semi-transparent HUD background
        hud = pygame.Surface((280, 90), pygame.SRCALPHA)
        hud.fill((0, 0, 0, 140))
        self.screen.blit(hud, (10, 10))

        lines = [
            f"Min Depth : {self.min_depth:.2f} m",
            f"Max Depth : {self.max_depth:.2f} m",
            f"FPS : {self.clock.get_fps():.1f}",
        ]

        y = 20
        for line in lines:
            text = self.font.render(
                line,
                True,
                (255, 255, 255),
            )
            self.screen.blit(text, (20, y))
            y += 28

        # Crosshair
        cx = self.width // 2
        cy = self.height // 2

        pygame.draw.line(
            self.screen,
            (255, 255, 255),
            (cx - 12, cy),
            (cx + 12, cy),
            2,
        )

        pygame.draw.line(
            self.screen,
            (255, 255, 255),
            (cx, cy - 12),
            (cx, cy + 12),
            2,
        )

        pygame.display.flip()
        self.clock.tick(60)

    def destroy_node(self):
        pygame.quit()
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = SimWindow()

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