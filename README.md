# lidar

ROS 2 Humble workspace for Livox MID-360.

## What Is Included

- Official `Livox-SDK2` pinned to `v1.3.1`.
- Official `livox_ros_driver2` pinned to `1.2.6`.
- `FAST_LIO` ROS 2 branch for MID-360 LiDAR-inertial odometry.
- Local `lidar_bringup` package with MID-360 config and launch files.
- Local `lidar_localization` package that exposes a stable LiDAR pose interface.
- Scripts to build, configure, source, run, record, and check the workspace without installing the SDK into `/usr/local`.

## Build

```bash
cd ~/lidar
./scripts/build_lidar.sh
```

## Configure MID-360 IPs

MID-360 units normally use a static IP like `192.168.1.1XX`, where `XX` is the last two digits of the serial number. Set the wired host address to the same subnet, commonly `192.168.1.50/24`.

Configure the wired interface, replacing `eno1` if your Ethernet interface has another name:

```bash
ip -br link
cd ~/lidar
./scripts/setup_mid360_network.sh eno1 192.168.1.50/24
```

Update this workspace config:

```bash
cd ~/lidar
./scripts/configure_mid360.py --host-ip 192.168.1.50 --lidar-ip 192.168.1.124
```

Replace `192.168.1.124` with the actual LiDAR IP. You can check connectivity with:

```bash
ping 192.168.1.124
```

## Run

PointCloud2 plus RViz:

```bash
cd ~/lidar
./scripts/run_mid360_rviz.sh
```

Livox custom message format only:

```bash
cd ~/lidar
./scripts/run_mid360_custom_msg.sh
```

MID-360 driver + FAST-LIO + LiDAR pose interface:

```bash
cd ~/lidar
./scripts/run_mid360_fast_lio.sh
```

This launch starts:

- `livox_ros_driver2`: publishes `/livox/lidar` and `/livox/imu`
- `fast_lio`: subscribes to `/livox/lidar` and `/livox/imu`, publishes `/Odometry`
- `lidar_localization`: subscribes to `/Odometry`, publishes `/lidar/pose`, `/lidar/point`, and `/lidar/odom`

## Mapping

Start mapping:

```bash
cd ~/lidar
./scripts/run_mid360_fast_lio.sh
```

Move the robot slowly through the environment. Start with 5-10 seconds still, then move smoothly and avoid fast spins during the first test.

Check that mapping and odometry are alive:

```bash
source ~/lidar/scripts/source_lidar.sh
ros2 topic hz /Odometry
ros2 topic hz /cloud_registered
ros2 topic hz /lidar/pose
```

Save the accumulated map:

```bash
cd ~/lidar
./scripts/save_fast_lio_map.sh
```

The map is saved to:

```bash
~/lidar/maps/mid360_map.pcd
```

## LiDAR Pose Coordinates

After `run_mid360_fast_lio.sh` is running, print the current LiDAR pose:

```bash
cd ~/lidar
./scripts/print_lidar_pose.sh
```

Read just the xyz coordinate:

```bash
source ~/lidar/scripts/source_lidar.sh
ros2 topic echo /lidar/point
```

Important frames:

- `/Odometry`: FAST-LIO raw odometry, usually `camera_init -> body`
- `/lidar/pose`: LiDAR pose re-exposed by this workspace
- `/lidar/point`: LiDAR xyz position only
- `/lidar/odom`: same pose as odometry, with the child frame set by our interface

For now, `/lidar/pose` represents the MID-360/LiDAR body pose produced from FAST-LIO odometry. The later LiDAR-to-vehicle-center transform is intentionally left as a parameterized interface in:

```bash
~/lidar/src/lidar_localization/config/lidar_pose_interface.yaml
```

By default, this workspace waits 5 seconds after the first FAST-LIO odometry message, then locks the `/lidar/*` output origin. Keep the robot still during those first 5 seconds. To reset the output origin later:

```bash
cd ~/lidar
./scripts/reset_lidar_origin.sh
```

When the LiDAR-to-vehicle-center extrinsic is measured, set:

```yaml
output_base_frame: true
lidar_to_base_xyz: [0.0, 0.0, 0.0]
lidar_to_base_rpy: [0.0, 0.0, 0.0]
```

## Point Coordinates

Point coordinates are obstacle/scene points in the LiDAR frame. They are different from the LiDAR's own pose.

Print the nearest valid point in the LiDAR frame:

```bash
cd ~/lidar
source ./scripts/source_lidar.sh
./scripts/print_lidar_points.py --nearest
```

Print sampled points from one point cloud:

```bash
./scripts/print_lidar_points.py --count 10 --step 500
```

Coordinates are in meters in `livox_frame`, with the LiDAR as the origin.

## Record Data

Record driver, FAST-LIO, pose, and TF topics:

```bash
cd ~/lidar
./scripts/record_mid360_localization_bag.sh
```

## Notes

- Source the workspace manually when needed:

  ```bash
  source ~/lidar/scripts/source_lidar.sh
  ```

- Validate the install:

  ```bash
  ~/lidar/scripts/check_mid360.sh
  ```

- If launch prints `bind failed`, the host IP in `mid360_config.json` is not assigned to any local network interface.

- If `/lidar/pose` has no data, check whether FAST-LIO is producing `/Odometry`:

  ```bash
  source ~/lidar/scripts/source_lidar.sh
  ros2 topic hz /Odometry
  ```

- The SDK shared library is installed under `~/lidar/third_party/Livox-SDK2/install/lib`, so the scripts set `LD_LIBRARY_PATH` automatically.

## Official References

- Livox ROS Driver 2: https://github.com/Livox-SDK/livox_ros_driver2
- Livox SDK2: https://github.com/Livox-SDK/Livox-SDK2
- FAST-LIO: https://github.com/hku-mars/FAST_LIO
- MID-360 protocol wiki: https://livox-wiki-en.readthedocs.io/en/latest/tutorials/new_product/mid360/mid360.html
