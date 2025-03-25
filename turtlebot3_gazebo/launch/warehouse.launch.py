#!/usr/bin/env python3
#
# Copyright 2019 ROBOTIS CO., LTD.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# Authors: Joep Tool

# Edited by Sean Kim for Robotics 2 

##import os

# from ament_index_python.packages import get_package_share_directory
# from launch import LaunchDescription
# from launch.actions import IncludeLaunchDescription
# from launch.launch_description_sources import PythonLaunchDescriptionSource
# from launch.substitutions import LaunchConfiguration


# def generate_launch_description():
#     launch_file_dir = os.path.join(get_package_share_directory('turtlebot3_gazebo'), 'launch')
#     pkg_gazebo_ros = get_package_share_directory('gazebo_ros')

#     use_sim_time = LaunchConfiguration('use_sim_time', default='true')
#     x_pose_1 = LaunchConfiguration('x_pose_1', default='-1.2')
#     y_pose_1 = LaunchConfiguration('y_pose_1', default='0.5')
#     x_pose_2 = LaunchConfiguration('x_pose_2', default='1.2')
#     y_pose_2 = LaunchConfiguration('y_pose_2', default='-0.5')

#     world = os.path.join(
#         get_package_share_directory('turtlebot3_gazebo'),
#         'worlds',
#         'warehouse.world'
#     )

#     gzserver_cmd = IncludeLaunchDescription(
#         PythonLaunchDescriptionSource(
#             os.path.join(pkg_gazebo_ros, 'launch', 'gzserver.launch.py')
#         ),
#         launch_arguments={'world': world}.items()
#     )

#     gzclient_cmd = IncludeLaunchDescription(
#         PythonLaunchDescriptionSource(
#             os.path.join(pkg_gazebo_ros, 'launch', 'gzclient.launch.py')
#         )
#     )

#     robot_state_publisher_cmd = IncludeLaunchDescription(
#         PythonLaunchDescriptionSource(
#             os.path.join(launch_file_dir, 'robot_state_publisher.launch.py')
#         ),
#         launch_arguments={'use_sim_time': use_sim_time}.items()
#     )

#     spawn_turtlebot_1 = IncludeLaunchDescription(
#         PythonLaunchDescriptionSource(
#             os.path.join(launch_file_dir, 'spawn_turtlebot3.launch.py')
#         ),
#         launch_arguments={
#             'x_pose': x_pose_1,
#             'y_pose': y_pose_1,
#             'yaw': '1.5708',
#             'robot_name': 'robot1',  
#             'namespace': 'robot1',  
#         }.items()
#     )

#     # Spawn second TurtleBot (robot2)
#     spawn_turtlebot_2 = IncludeLaunchDescription(
#         PythonLaunchDescriptionSource(
#             os.path.join(launch_file_dir, 'spawn_turtlebot3.launch.py')
#         ),
#         launch_arguments={
#             'x_pose': x_pose_2,
#             'y_pose': y_pose_2,
#             'yaw': '1.5708',
#             'robot_name': 'robot2',  
#             'namespace': 'robot2',   
#         }.items()
#     )

#     ld = LaunchDescription()

#     # Add the commands to the launch description
#     ld.add_action(gzserver_cmd)
#     ld.add_action(gzclient_cmd)
#     ld.add_action(robot_state_publisher_cmd)
#     ld.add_action(spawn_turtlebot_1)
#     ld.add_action(spawn_turtlebot_2)

#     return ld 

import os
import xml.etree.ElementTree as ET

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import GroupAction, IncludeLaunchDescription, RegisterEventHandler
from launch.event_handlers import OnShutdown
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import PushRosNamespace

def generate_launch_description():
    TURTLEBOT3_MODEL = os.environ['TURTLEBOT3_MODEL']

    # Configure 2 robots
    number_of_robots = 2
    namespace = 'robot'  # Namespace prefix
    pose = [[-1.2, 0.5], [1.2, -0.5]]  # Positions for 2 robots

    # Path to the original SDF model
    model_folder = 'turtlebot3_' + TURTLEBOT3_MODEL
    urdf_path = os.path.join(
        get_package_share_directory('turtlebot3_gazebo'),
        'models',
        model_folder,
        'model.sdf'
    )
    save_path = os.path.join(
        get_package_share_directory('turtlebot3_gazebo'),
        'models',
        model_folder,
        'tmp'  # Temporary folder for modified SDFs
    )

    # Ensure the tmp directory exists
    os.makedirs(save_path, exist_ok=True)

    # Gazebo world setup
    world = os.path.join(
        get_package_share_directory('turtlebot3_gazebo'),
        'worlds',
        'warehouse.world'
    )

    # Gazebo server and client
    gzserver_cmd = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(get_package_share_directory('gazebo_ros'), 'launch', 'gzserver.launch.py')
        ),
        launch_arguments={'world': world}.items()
    )
    gzclient_cmd = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(get_package_share_directory('gazebo_ros'), 'launch', 'gzclient.launch.py')
        )
    )

    # Robot State Publishers (one per robot)
    robot_state_publisher_cmd_list = []
    for count in range(number_of_robots):
        robot_state_publisher_cmd_list.append(
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(
                    os.path.join(get_package_share_directory('turtlebot3_gazebo'), 'launch', 'robot_state_publisher.launch.py')
                ),
                launch_arguments={
                    'use_sim_time': 'true',
                    'frame_prefix': f'{namespace}_{count+1}/'  # Unique frame prefix
                }.items()
            )
        )

    # Spawn robots (with modified SDFs)
    spawn_turtlebot_cmd_list = []
    for count in range(number_of_robots):
        # Modify the SDF to update frames (odom, base_footprint, base_scan)
        tree = ET.parse(urdf_path)
        root = tree.getroot()
        for odom_frame_tag in root.iter('odometry_frame'):
            odom_frame_tag.text = f'{namespace}_{count+1}/odom'
        for base_frame_tag in root.iter('robot_base_frame'):
            base_frame_tag.text = f'{namespace}_{count+1}/base_footprint'
        for scan_frame_tag in root.iter('frame_name'):
            scan_frame_tag.text = f'{namespace}_{count+1}/base_scan'

        # Save the modified SDF
        modified_sdf = ET.tostring(root, encoding='unicode')
        modified_sdf = '<?xml version="1.0" ?>\n' + modified_sdf
        tmp_sdf_path = f'{save_path}{count+1}.sdf'
        with open(tmp_sdf_path, 'w') as file:
            file.write(modified_sdf)

        # Spawn the robot
        spawn_turtlebot_cmd_list.append(
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(
                    os.path.join(get_package_share_directory('turtlebot3_gazebo'), 'launch', 'multi_spawn_turtlebot3.launch.py')
                ),
                launch_arguments={
                    'x_pose': str(pose[count][0]),
                    'y_pose': str(pose[count][1]),
                    'robot_name': f'{TURTLEBOT3_MODEL}_{count+1}',
                    'namespace': f'{namespace}_{count+1}',
                    'sdf_path': tmp_sdf_path
                }.items()
            )
        )

    # Launch description
    ld = LaunchDescription()
    ld.add_action(gzserver_cmd)
    ld.add_action(gzclient_cmd)

    # Cleanup temporary SDF files on shutdown
    ld.add_action(RegisterEventHandler(
        OnShutdown(
            on_shutdown=lambda event, context: [
                os.remove(f'{save_path}{count+1}.sdf') for count in range(number_of_robots)
            ]
        )
    ))

    # Add robots with namespaces
    for count in range(number_of_robots):
        ld.add_action(GroupAction([
            PushRosNamespace(f'{namespace}_{count+1}'),
            robot_state_publisher_cmd_list[count],
            spawn_turtlebot_cmd_list[count]
        ]))

    return ld