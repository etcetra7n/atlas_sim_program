#!/bin/bash

rm -rf build install log
xacro urdf/rover.urdf.xacro > urdf/rover.urdf
colcon build
