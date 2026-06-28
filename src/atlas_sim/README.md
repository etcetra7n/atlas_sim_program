# Atlas Simulator Program

A Mars rover simulation environment for collecting human navigation demonstrations to train a mapless autonomous navigation model

## Prerequisites

- ROS 2 Humble
- Gazebo Sim
- `xacro`
- `pynput`
- `ros_gz_bridge`

## Build

Source ROS 2:

```sh
source /opt/ros/humble/setup.bash
```

Generate the URDF: (_Only needed if you have modified the urdf files_)

```sh
xacro urdf/rover.urdf.xacro > urdf/rover.urdf
```

Build the workspace:

```sh
colcon build
```

Source the workspace:

```sh
source install/setup.bash
```

## Run

Launch the Gazebo simulation:

```sh
ros2 launch atlas_sim sim_launch.py
```
