# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

AirSLAM is an illumination-robust point-line visual SLAM system (IEEE TRO 2025), packaged as a ROS Noetic catkin package named `air_slam`. It runs in dual mode: V-SLAM (stereo) or VI-SLAM (stereo + IMU), selected by the `use_imu` flag in the camera config YAML. Deep networks (SuperPoint/PLNet feature extraction, LightGlue/SuperGlue matching) run through NVIDIA TensorRT; the backend (tracking, local mapping, bundle adjustment) is classical g2o optimization.

This repo is a fork (origin `BaoTan/AirSLAM`) of `sair-lab/AirSLAM`. The `develop` branch (default working branch) carries local modifications: TUM-style trajectory output, timestamp rounding, and EuRoC ground-truth conversion. `master` tracks upstream; PRs usually target `master`.

## Build & Run

The package must live inside a catkin workspace (e.g. `~/catkin_ws/src/AirSLAM`). Build from the workspace root:

```bash
catkin_make                      # or: catkin_make --pkg air_slam
source ~/catkin_ws/devel/setup.bash
```

There is no test suite. `test_feature` (demo/test_feature.cpp) is a manual feature-visualization tool with hardcoded paths from the original authors' machine.

Run the three pipeline stages via launch files (each also starts RViz unless `visualization:=false` is passed):

```bash
roslaunch air_slam vo_euroc.launch      # mapping (visual odometry)
roslaunch air_slam mr_euroc.launch      # map refinement (offline, sequential)
roslaunch air_slam reloc_euroc.launch   # relocalization against the refined map
```

Launch args point at package-relative paths (`$(find air_slam)/...`); edit `dataroot`, `saving_dir` (must already exist), and `map_root` per dataset. Launch/config pairs exist for euroc, oivio, tartanair, uma_bumblebee, dark_euroc under `launch/` and `configs/`. A Docker image (`xukuanhit/air_slam:v4`) with all dependencies is the recommended environment; key deps: OpenCV 4.2, Eigen3, Ceres 2.0, G2O (tag 20230223_git), TensorRT 8.6.1.6, CUDA 12.1, yaml-cpp, Boost (serialization), gflags, glog.

The Python scripts in `scripts/` (evaluation via evo, batch runners, `euroc_gt2tum.py` for ASL csv → TUM ground truth) contain hardcoded absolute paths that must be edited before use.

## Pipeline Architecture

Three executables in `demo/`, each wrapping one pipeline class:

1. **`visual_odometry` → `MapBuilder`** (include/map_builder.h, src/map_builder.cc): reads an ASL/EuRoC-format dataset (`cam0/data`, `cam1/data`, `imu0/data.csv` — IMU optional) via `Dataset`, then runs two producer/consumer threads connected by mutex-guarded queues: `ExtractFeatureThread` (TensorRT feature detection on left+right images) → `TrackingThread` (matching against reference keyframe, frame pose optimization, keyframe insertion, local map optimization inside `Map`). Outputs `AirSLAM_mapv0.bin` + `trajectory_v0.txt` (TUM) to `saving_dir`.

2. **`map_refinement` → `MapRefiner`** (src/map_refiner.cc): offline, strictly sequential: load mapv0 + vocabulary → build covisibility graph → loop detection (DBoW2 bag-of-words over SuperPoint descriptors, "sentence" similarity from line-adjacent keypoints) → pose graph refinement → merge duplicate mappoints/maplines → global BA → build junction database → save `AirSLAM_mapv1.bin` + `trajectory_v1.txt`. The `breakpoint` launch arg pauses between stages (press `c` to continue).

3. **`relocalization` → `MapUser`** (src/map_user.cc): loads mapv1 + vocabulary, localizes single monocular query images (folder of images) using keypoints, lines, and the junction structure graph; writes a TUM trajectory to `traj_path` and prints recall.

### Core data structures

- **`Map`** (include/map.h): the central store — keyframes, mappoints, maplines, covisibility graph, DBoW2 databases, IMU init state (gravity `Rwg`). Serialized as one Boost binary archive (`.bin`); `MapRefiner`/`MapUser` are friends and also read the per-frame `frames/*.txt` + `mappoints.txt` text dumps. Local mapping (keyframe insertion, local BA, triangulation, outlier culling) lives here, not in MapBuilder.
- **`Frame`** (include/frame.h): all point features are stored in a single `Eigen::Matrix<float, 259, Eigen::Dynamic>` (row layout: row 0 = score, row 1 = x, row 2 = y, rows 3–258 = 256-dim SuperPoint descriptor); lines are `Eigen::Vector4d` endpoints; per-feature `track_id`s link Frame slots to shared `Mappoint`/`Mapline` objects. Also holds IMU pose/velocity/bias/preintegration for VI-SLAM.
- **`Camera`** (include/camera.h): stereo rig; camera YAML defines intrinsics, distortion (`distortion_type`: 0 undistorted / 1 radtan / 2 fisheye), and camera-body extrinsics with `T_type` (0 = EuRoC Tbc, 1 = Kalibr Tcb), plus IMU noise parameters.

### Neural network layer (TensorRT)

All inference classes follow the same pattern: `build()` → `deserialize_engine()` from a cached `.engine` file, else parse the `.onnx` and `save_engine()`. ONNX models are committed in `output/`; `.engine` files are generated on first run (gitignored — the first run is slow). GPU buffers use the vendored `3rdparty/tensorrtbuffer`.

- `FeatureDetector` wraps `PLNet` (two engines: stage 0 = keypoint/descriptor head or `SuperPoint` when `use_superpoint: 1`, stage 1 = line + junction head) and is the single entry point for detection.
- `PointMatcher` wraps `LightGlue` (`matcher: 0` in config) or `SuperGlue` (`matcher: 1`); features must be normalized to model input size first.
- Vocabulary: `3rdparty/DBoW2` is extended with `FSuperpoint` (256-dim float descriptor vocabulary) in `src/bow/`; the pretrained vocabulary is `voc/point_voc_L4.bin`.

### Optimization (g2o)

`src/g2o_optimization/` defines custom vertices (`VertexLine3D`, `VertexViPose`, `VertexIMU`) and edges (point/line reprojection, IMU preintegration, relative pose). `g2o_optimization.h` exposes the wrappers used by the pipeline: `FrameOptimization` (tracking, coupled points+lines), `LocalmapOptimization`, `PoseGraphOptimization` (loop closure), `GlobalBA`, and IMU initialization/validation. IMU preintegration is `Preinteration` in include/imu.h.

### Config system

Every stage YAML in `configs/` maps 1:1 onto a struct in `include/read_configs.h` (`VisualOdometryConfigs`, `MapRefinementConfigs`, `RelocalizationConfigs`), which parses the file and resolves model paths against the `model_dir` launch arg. Adding a config field requires touching both the YAML and the corresponding `Load()` method. `RosPublisher` topics/throttles are configured here too; `ThreadPublisher<T>` provides the async publish threads for visualization on `/AirSLAM/*` topics.

## Conventions

- Source files mix `.cc` (core SLAM) and `.cpp` (TensorRT network classes); new files must be added manually to the `add_library(air_slam_lib ...)` list in CMakeLists.txt — there is no globbing.
- Build is Release-only (`set(CMAKE_BUILD_TYPE "release")`) and warnings are globally suppressed (`add_definitions(-w)`), so compiler warnings will not surface issues.
- Poses are `Eigen::Matrix4d` (camera-to-world); trajectories are written in TUM format (`timestamp tx ty tz qx qy qz qw`) via `SaveTumTrajectoryToFile` in src/utils.cc; image timestamps are parsed from filenames via `ImageNameToTime`.
- Shared-pointer typedefs (`FramePtr`, `MappointPtr`, `MapPtr`, ...) are declared next to each class.
