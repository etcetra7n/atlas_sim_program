from launch import LaunchDescription
from launch.actions import ExecuteProcess
from launch_ros.actions import Node
from launch.actions import TimerAction, LogInfo

from ament_index_python.packages import get_package_share_directory

from pathlib import Path
import os
import xacro

data_dir = Path.cwd().parent.parent / "dataset" / "rosbags"
world_name = "tugbot_depot"

def get_next_folder():
    base_dir = data_dir / world_name
    base_dir.mkdir(parents=True, exist_ok=True)
    numbers = [
        int(folder.name.removeprefix("run_"))
        for folder in base_dir.iterdir()
        if (
            folder.is_dir()
            and folder.name.startswith("run_")
            and folder.name.removeprefix("run_").isdigit()
        )
    ]
    next_number = max(numbers, default=-1) + 1
    return base_dir / f"run_{next_number:04d}"

def generate_launch_description():
    pkg = get_package_share_directory(
        "atlas_sim"
    )
    
    world = os.path.join(
        pkg,
        "worlds",
        f"{world_name}.sdf"
    )

    xacro_file = os.path.join(
        pkg,
        "urdf",
        "rover.urdf.xacro"
    )

    robot_description = xacro.process_file(
        xacro_file
    ).toxml()

    gazebo = ExecuteProcess(
        cmd=[
            "gz",
            "sim",
            "-s",
            "-r",
            world
        ],
        output="screen"
    )

    robot_state_publisher = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        parameters=[
            { "robot_description": robot_description }
        ],
        output="screen"
    )

    spawn = TimerAction(
        period=5.0,
        actions=[
            Node(
                package="ros_gz_sim",
                executable="create",
                arguments=[
                    "-world", world_name,
                    "-name", "rover",
                    "-topic", "robot_description"
                ],
                output="screen"
            ),
            LogInfo(
                msg="Rover spawned"
            ),
        ]
    )

    depth_bridge = Node(
        package="ros_gz_bridge",
        executable="parameter_bridge",
        arguments=[
            f"/world/{world_name}/model/rover/link/base_link/sensor/depth_camera/depth_image@sensor_msgs/msg/Image@gz.msgs.Image"
        ],
        remappings=[
            (
                f"/world/{world_name}/model/rover/link/base_link/sensor/depth_camera/depth_image",
                "/depth/image"
            )
        ]
    )

    camera_info_bridge = Node(
        package="ros_gz_bridge",
        executable="parameter_bridge",
        arguments=[
            f"/world/{world_name}/model/rover/link/base_link/sensor/depth_camera/camera_info@sensor_msgs/msg/CameraInfo@gz.msgs.CameraInfo"
        ],
        remappings=[
            (
                f"/world/{world_name}/model/rover/link/base_link/sensor/depth_camera/camera_info",
                "/depth/camera_info"
            )
        ]
    )

    cmd_vel_bridge = Node(
        package="ros_gz_bridge",
        executable="parameter_bridge",
        arguments=[
            "/cmd_vel@geometry_msgs/msg/Twist@gz.msgs.Twist"
        ],
        output="screen"
    )

    sim_window = TimerAction(
        period=9.0,
        actions=[
            Node(
                package='atlas_sim',
                executable='sim_window',
                name='sim_window',
                output='screen',
            ),
            LogInfo(
                msg="Sim window started"
            ),
        ]
    )

    session_dir = str(get_next_folder())
    rosbag = TimerAction(
        period=10.0,
        actions=[
            ExecuteProcess(
                cmd=[
                    "ros2", "bag", "record",
                    "-o", session_dir,

                    "/cmd_vel",
                    "/depth/image",
                    "/depth/camera_info",
                    "/odom",
                    "/tf",
                    "/tf_static"
                ],
                output="screen",
            ),
            LogInfo(msg=f"Recording to {session_dir}")
        ]
    )

    return LaunchDescription([
        gazebo,
        robot_state_publisher,
        spawn,
        depth_bridge,
        camera_info_bridge,
        cmd_vel_bridge,
        sim_window,
        rosbag
    ])
