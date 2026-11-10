 ▐▛███▛█   Claude Code v2.1.311
▝▜██████▀  qwen3.8-max · API Usage Billing
 ▝▝   ▝▝   ~/work_prjs/open_codes/AirSLAM


❯ /init                                                                         

  Thought for 1m 47s, searched for 6 patterns, read 8 files, listed 4 directories, ran 4 shell commands (ctrl+o to expand)

● I have a complete picture of the codebase now. Let me write the CLAUDE.md
  file.

● Write(CLAUDE.md)
  ⎿  Wrote 71 lines to CLAUDE.md
      1 # CLAUDE.md
      2 
      3 This file provides guidance to Claude Code (claude.ai/code) when 
        working with code in this repository.
      4 
      5 ## Project Overview
      6 
      7 AirSLAM is an illumination-robust point-line visual SLAM system (
        IEEE TRO 2025), packaged as a ROS Noetic catkin package named `ai
        r_slam`. It runs in dual mode: V-SLAM (stereo) or VI-SLAM (stereo
     … +65 lines (~7 KB) (ctrl+o to expand)

  Thought for 5s (ctrl+o to expand)

● Created CLAUDE.md after analyzing the codebase. Highlights of what it
  captures:

  Build & Run
  - Catkin workspace build (catkin_make), no test suite, Docker image as
    recommended environment
  - The three roslaunch entry points (VO / map refinement / relocalization) with
    the launch-arg editing workflow (dataroot, saving_dir, map_root,
    visualization:=false)
  - Note that scripts/ and demo/test_feature.cpp contain hardcoded paths from
    the original authors' machines

  Architecture (the parts requiring multi-file reading)
  - The three-stage offline pipeline: MapBuilder (two-thread feature-extract →
    track producer/consumer, saves AirSLAM_mapv0.bin) → MapRefiner (sequential
    loop closure, merging, global BA, junction DB, saves mapv1.bin, breakpoint
    stepping) → MapUser (monocular relocalization)
  - Core data structures: Map as the Boost-serialized central store where local
    mapping actually lives; Frame's packed Eigen::Matrix<float, 259, Dynamic>
    feature layout and track-id linking
  - TensorRT layer: the shared build()/deserialize_engine()/save_engine()
    pattern, committed ONNX vs. gitignored first-run .engine caches, PLNet
    two-stage design, FeatureDetector/PointMatcher wrappers, DBoW2+FSuperpoint
    vocabulary
  - g2o custom vertices/edges and the optimization wrapper entry points; IMU
    preintegration for VI-SLAM mode
  - Config system: YAML ↔ read_configs.h struct 1:1 mapping, use_imu mode
    switch, T_type extrinsics convention

  Conventions — .cc/.cpp split, manual CMakeLists source registration,
  Release-only + globally suppressed warnings, TUM trajectory format,
  Eigen::Matrix4d poses. Also documented that this is a fork with local
  trajectory-output changes on develop while PRs target master.

✻ Worked for 4m 3s · done Tuesday, Nov 3, 4:21 PM

❯ 这个项目提取图像的特征有什么,使用什么方法提取的                               

  Thought for 48s, searched for 2 patterns, ran 4 shell commands (ctrl+o to expand)

● Update(CLAUDE.md)
  ⎿  Added 1 line, removed 1 line
      44  ### Core data structures
      45  
      46  - **`Map`** (include/map.h): the central store — keyframes, map
          points, maplines, covisibility graph, DBoW2 databases, IMU init
           state (gravity `Rwg`). Serialized as one Boost binary archive 
          (`.bin`); `MapRefiner`/`MapUser` are friends and also read the 
          per-frame `frames/*.txt` + `mappoints.txt` text dumps. Local ma
          pping (keyframe insertion, local BA, triangulation, outlier cul
          ling) lives here, not in MapBuilder.
      47 -- **`Frame`** (include/frame.h): all point features are stored 
         -in a single `Eigen::Matrix<float, 259, Eigen::Dynamic>` (row la
         -yout: x, y, score, then a 256-dim SuperPoint descriptor); lines
         - are `Eigen::Vector4d` endpoints; per-feature `track_id`s link 
         -Frame slots to shared `Mappoint`/`Mapline` objects. Also holds 
         -IMU pose/velocity/bias/preintegration for VI-SLAM.             
      47 +- **`Frame`** (include/frame.h): all point features are stored 
         +in a single `Eigen::Matrix<float, 259, Eigen::Dynamic>` (row la
         +yout: row 0 = score, row 1 = x, row 2 = y, rows 3–258 = 256-dim
         + SuperPoint descriptor); lines are `Eigen::Vector4d` endpoints;
         + per-feature `track_id`s link Frame slots to shared `Mappoint`/
         +`Mapline` objects. Also holds IMU pose/velocity/bias/preintegra
         +tion for VI-SLAM.                                              
      48  - **`Camera`** (include/camera.h): stereo rig; camera YAML defi
          nes intrinsics, distortion (`distortion_type`: 0 undistorted / 
          1 radtan / 2 fisheye), and camera-body extrinsics with `T_type`
           (0 = EuRoC Tbc, 1 = Kalibr Tcb), plus IMU noise parameters.
      49  
      50  ### Neural network layer (TensorRT)

  Thought for 25s (ctrl+o to expand)

● CLAUDE.md 已修正。下面是这个项目特征提取的完整情况:

  提取的特征(三类)

  ┌────────────┬───────────────────────────────────┬────────────────────────┐
  │    特征    │             表示形式              │          用途          │
  ├────────────┼───────────────────────────────────┼────────────────────────┤
  │            │ Eigen::Matrix<float, 259,         │ 跟踪、三角化成         │
  │ 关键点 +   │ N>:第0行=score,第1行=x,第2行=y,第 │ Mappoint、BoW          │
  │ 描述子     │ 3~258行=256维 SuperPoint          │ 回环/重定位            │
  │            │ 风格描述子                        │                        │
  ├────────────┼───────────────────────────────────┼────────────────────────┤
  │ 结构线段   │ Eigen::Vector4d(x1,y1,x2,y2 端点) │ 三角化成               │
  │            │                                   │ Mapline,与点耦合优化   │
  ├────────────┼───────────────────────────────────┼────────────────────────┤
  │ 交点(Junct │ 同 259 维格式,带描述子            │ 构建交点结构图数据库,  │
  │ ion)       │                                   │ 用于重定位             │
  └────────────┴───────────────────────────────────┴────────────────────────┘

  提取方法:CNN + TensorRT(非传统手工特征)

  不用 ORB/LSD 这类传统方法,全部由深度网络推理完成,统一入口是
  FeatureDetector(src/feature_detector.cc),内部按配置组合两个网络:

  1. 关键点来源由 plnet.use_superpoint 决定(vo_euroc.yaml 中为 1):
  - = 1:关键点用 SuperPoint(superpoint_v1_sim_int32.onnx),线段用 PLNet
  - = 0:关键点和线段都由 PLNet 出

  2. PLNet 是两阶段级联网络(src/plnet.cpp,模型 plnet_s0.onnx + plnet_s1.onnx):

  - 预处理:灰度图 resize 到 512×512、归一化到 [0,1]
  - Stage 0 推理(TF32):输出 512×512 关键点热力图 scores、1/8 分辨率的 256
    维描述子图
    descriptors、以及线段/交点的中间预测(lines_pred、juncs_pred、loi_features
    等)
  - CPU 后处理 wireframe_matcher:对线段-交点对做去重(最多 top-300 个交点)
  - Stage 1 推理(FP16):输入上一步中间结果,输出精修后的线段端点 lines_adjusted
    和线段得分 scores_line

  3. 解码与过滤(阈值都在配置 YAML 的 plnet 段):
  - 关键点 detect_point:热力图值 ≥ keypoint_threshold(0.004)、去掉图像边界
    remove_borders(4px)、按得分排序取 top max_keypoints(400);extract_descriptors
    在描述子图上双线性插值采样出 256 维描述子
  - 线段:得分 ≥ line_threshold(0.75)、长度 ≥
    line_length_threshold(50px)、端点在边界内
  - 交点 junction_detector:从有效线段端点位置提取,复用同一张描述子图
  - 最后所有坐标乘 w_scale/h_scale 缩放回原图分辨率

  4. 加速方式:所有 ONNX 模型(在 output/ 目录)首次运行时由 TensorRT 解析构建成
  .engine 缓存(gitignored),之后直接反序列化推理。

  另外补充:点的匹配也是神经网络(PointMatcher 包 LightGlue,matcher: 0 默认;或
  SuperGlue,matcher: 1),但线段的匹配是几何方法(line_processor.cc),不走网络。

✻ Baked for 1m 48s · done Tuesday, Nov 3, 4:23 PM

※ recap: Goal: document and explore the AirSLAM repo. Created CLAUDE.md (build, run, pipeline architecture) and explained feature extraction: keypoints, lines, junctions via SuperPoint/PLNet CNNs on TensorRT. Nothing pending; awaiting your next question. (disable recaps in /config)

❯ 这些特征提取后是怎么匹配和跟踪的                                              

  Thought for 1m 26s, searched for 4 patterns, ran 5 shell commands (ctrl+o to expand)

● 看完整个跟踪链路后,给你完整梳理。整体是两线程流水线:ExtractFeatureThread(提取+
  匹配+关键帧决策)→ 队列 → TrackingThread(位姿优化+入图),都在
  src/map_builder.cc。

  一、特征怎么匹配

  1. 点匹配 —— 神经网络(src/point_matcher.cc)

  PointMatcher::MatchingPoints 先把关键点坐标归一化(LightGlue 用 scale
  0.5,SuperGlue 用 0.7),然后:
  - LightGlue(默认 matcher: 0):把两帧的 [score, x, y, 256维描述子](259
    行里去掉第 0 行)直接喂给 TensorRT 网络,输出匹配对索引 + 置信度;
  - SuperGlue(matcher: 1):推理后做互近邻检查(indices0(i) 和 indices1(j)
    必须双向一致)才接受;
  - 可选几何校验(outlier_rejection=true 时才开):cv::findFundamentalMat
    RANSAC(阈值 20px、置信度 0.99)剔除外点。只在"当前帧 ↔
    参考关键帧"匹配时使用,左右立体匹配不用。

  点匹配用在两处:
  - 帧间跟踪:当前帧 vs 上一个关键帧(每帧都做);
  - 立体匹配:左图 vs 右图(只在关键帧/候选关键帧上做)。Frame::AddRightFeatures
    再用极线约束过滤(视差 dx 必须在 [min_x_diff, max_x_diff] 内、dy ≤
    max_y_diff),通过后直接算深度 depth = BF/视差。

  2. 线匹配 —— 不用网络,靠点匹配投票(src/line_processor.cc)

  这是本文"点线耦合"的核心技巧:
  - AssignPointsToLines:把关键点关联到线上(点到线距离 <
    3px,且落在线段端点包围盒外扩 3px 范围内),得到每条线"身上"的点集合;
  - MatchLines:利用已匹配好的点对给线对投票——每对匹配点各自所在的线对 (l0, l1)
    得 1 票,构成投票矩阵;然后行/列取最大且互为最大、票数 ≥
    2、票数²/min(两线点数) ≥ 0.8 才算匹配成功。

  所以线的匹配完全"搭便车"于点匹配结果,零额外网络开销。立体线匹配(左图线 vs
  右图线)用的也是同一函数。

  二、跟踪怎么做(TrackingThread → TrackFrame)

  1. IMU 预积分:_preinteration_keyframe.AddBatchData 把两关键帧间的 IMU
     数据预积分挂到帧上(VI-SLAM 模式);
  2. 关联地图元素:把"当前帧 ↔ 参考关键帧"的点匹配转成 mappoint 
     关联(参考帧的每个特征已有 track_id 和 mappoint 指针,直接继承);线用上面的
     MatchLines 匹配后同样继承 line_track_id 和 mapline;
  3. 求初始位姿(FramePoseOptimization):
     - IMU 已初始化且预积分有效(Δt < 2s)→ 用预积分 Predict 推算位姿(位移 > 1m
       视为异常回退);
     - 否则 → cv::solvePnPRansac(SolvePnPWithCV)用匹配到的 3D 点求解;
     - PnP 内点太少或位移异常 → 直接沿用上一帧位姿;
  4. g2o 位姿优化:FrameOptimization 固定所有 3D 点,只优化当前帧位姿(+ IMU
     模式下还有速度、bias),约束是单目点 + 双目点重投影边(pixel_sigma=0.8)和 IMU
     预积分边。注意跟踪阶段的位姿优化只用点,不加线约束(线的约束容器声明了但没填)
     ;
  5. 内点判定与传播:内点数 > lost_num_match(10)才算跟踪成功,然后把
     track_id、mappoint/mapline 指针正式写入当前帧。

  三、关键帧决策(AddKeyframeCheck,在特征线程里)

  基于当前帧与参考关键帧的匹配情况:
  - 匹配数 < min_num_match(30)→ 当前帧立即作关键帧;
  - 匹配率 < tracking_point_rate(0.65)或匹配数 < max_num_match(80)→
    下一帧作关键帧(IMU 未初始化时阈值放宽 1.1/0.7 倍,加速初始化);
  - 匹配点平均视差超过 图像面积 × tracking_parallax_rate² → 下一帧作关键帧;
  - 否则不插。另外若判为关键帧但立体点 < 10,会推迟并强制下一帧补做右图提取。

  四、插入关键帧后(Map::InsertKeyframe,局部建图)

  - 无 mappoint 的特征新建 Mappoint(反投影给初值),无 mapline 的线新建
    Mapline;有立体匹配的线直接双目三角化端点;
  - 观测数 > 2 的 Mappoint 做多视图三角化;线通过它关联的 mappoint
    三角化(TriangulateMaplineByMappoints)—— 又是点线耦合;
  - 局部 BA(LocalMapOptimization):滑动窗口最多 5 个关键帧,点和线一起优化(VI
    模式加 IMU 边、速度、bias),窗口外观测到这些元素的关键帧作为固定帧;
  - VI-SLAM 且 IMU 未初始化时触发 InitializeIMU(估计重力方向 Rwg、bias、尺度)。

  一句话总结:点用 LightGlue/SuperGlue 网络匹配(RANSAC
  几何校验兜底),线靠"点在线上 + 点匹配投票"的几何方法匹配;跟踪是 IMU 预积分/PnP
  给初值 + g2o 优化点重投影,线不参与帧级位姿优化,只在关键帧插入后的局部 BA
  和后端全局优化中与点耦合。

✻ Churned for 2m 34s · done Tuesday, Nov 3, 4:40 PM

※ recap: We documented this AirSLAM repo in CLAUDE.md, then walked through feature extraction and the matching/tracking pipeline. No task is pending; next step is whatever you'd like to explore or modify. (disable recaps in /config)

❯ 重定位是怎么实现的                                                            

  Thought for 1m 0s, searched for 1 pattern, ran 4 shell commands (ctrl+o to expand)

● 重定位在 MapUser::Relocalization(src/map_user.cc)中实现,只需单目查询图像,核心
  思路是"复用建好的地图 + 双层检索验证"。整个流程如下:

  〇、前置条件:地图里预建了两个数据库

  LoadMap 加载 AirSLAM_mapv1.bin(map refinement
  的产物),里面除了关键帧/Mappoint/Mapline,还序列化了:

  1. 关键点 BoW 数据库 _database:用预训练词典 voc/point_voc_L4.bin
     把所有关键帧的 256 维描述子转成词袋,维护倒排文件(单词 →
     哪些关键帧的哪些特征);
  2. 交点数据库 _junction_database + _junction_voc:MapRefiner::BuildJunctionData
     base(src/map_refiner.cc:956)在建图末端在线训练一个小词典(k=10, L=3, TF-IDF
     加权, L1_NORM 打分),把每个关键帧的交点(junction)描述子入库;同时为每帧调
     FindJunctionConnections 构建交点结构图——把每条线段的两个端点在 5×5
     窗口内关联到最近交点,连成边(frame.cc:581)。这张"线框图"就是论文里用于重定位
     的结构图。

  一、查询帧处理

  1. 图像去畸变(UndistortImage),FeatureDetector 提取关键点 + 线段 + 交点(注意
     reloc 配置里 use_superpoint: 0,点线交全部由 PLNet 出);
  2. 关键点和交点描述子分别经各自数据库 FrameToBow 转成 BoW 向量。

  二、候选检索:关键点 BoW → 分组 → 交点结构图重排序

  这是三层漏斗:

  1. BoW 检索与过滤
  - _database->Query 从倒排文件找出与查询帧共享单词的关键帧;
  - 共享词数 < max(最大共享词数 × 0.3, 8) 的直接丢弃;
  - 幸存帧用 DBoW2 L1 相似度打分。

  2. 共视分组(和回环检测同款套路)
  - 每个候选帧与其共视关键帧(共享观测 > 10)合成一组,组内最高分帧当"代表";
  - 组分数 = 组内 top-5 帧分数之和(抑制大组占便宜);
  - 组数 > 3 时,剔除分数 < 最佳组 50% 的组,然后按组分排序。

  3. 交点结构图一致性重排序(本文的创新点,map_user.cc:288–345)
  - 对查询帧调 FindJunctionConnections 得到自己的交点邻接图;
  - 对每个候选组的代表帧:通过交点倒排文件找到查询交点 ↔ 关键帧交点的匹配对,填
    match_matrix;
  - 统计两个量:
    - match_num:匹配上的交点对总数;
    - line_match_num:其中结构一致的——查询帧里交点 i 和 idx1
      有边相连,关键帧里对应的 j 和 idx2 也有边相连(即匹配保持了线框的连接关系);
  - rate = line_match_num / match_num,组分数追加 交点BoW得分 × (1 + rate) ——
    结构边一致性越好加分越多;
  - 重新排序。

  三、精匹配与位姿求解

  1. LightGlue 精匹配:取重排序后 top-3 组的代表帧,逐一与查询帧跑
     PointMatcher::MatchingPoints(开 outlier_rejection,即 F 矩阵 RANSAC
     几何校验),保留匹配数最多的一组;匹配数 < min_inlier_num(45)→ 重定位失败;
  2. PnP 求位姿:匹配到的关键帧特征都挂着地图里的 3D Mappoint,直接
     cv::solvePnPRansac(SolvePnPWithCV)解出查询帧位姿;
  3. 可选 g2o 精化(pose_refinement: 1,默认开):固定 3D 点、只优化位姿的
     FrameOptimization(单目+双目重投影边,pixel_sigma=0.8),更稳但更慢;
  4. 精化后内点数仍 < 45 → 判失败;成功则输出 Eigen::Matrix4d 位姿,可选发布
     /AirSLAM/reloc/* 可视化(位姿、轨迹、内点 3D 点)。

  四、外层驱动(demo/relocalization.cpp)

  对查询文件夹里的图像按文件名排序逐帧调 Relocalization,把结果位姿按 TUM
  格式写到 traj_path(你这个 fork 改成了时间戳字符串),最后打印 recall = 成功数 / 
  总数。

  总结:检索用"关键点 BoW 找地方 + 共视分组抗单帧噪声",验证用"交点 BoW + 线框结构
  一致性重排序"(对光照/视角变化鲁棒,这是纯外观检索做不到的),定位用"LightGlue
  精匹配 + PnP(+g2o 精化)"。失败的任何一层都直接返回
  false,没有重试机制——每张查询图像独立处理,不维护时序状态。

✻ Worked for 1m 41s · done Tuesday, Nov 3, 5:08 PM

❯ 回环检测和地图优化是怎么实现的                                                

  Thought for 2m 0s, searched for 2 patterns, ran 8 shell commands (ctrl+o to expand)

● 回环检测和地图优化都在 MapRefiner(src/map_refiner.cc)里,由
  demo/map_refinement.cpp 按固定顺序串起来:加载 mapv0 → 建共视图 → 回环检测 → 
  位姿图优化 → 融合地图(点/线合并 + 中间 BA)→ 全局 BA → 重建共视图 → 
  建交点数据库 → 存 mapv1。逐步拆解:

  一、回环检测 LoopDetection(:65–235)

  按关键帧 id 顺序遍历全图,边查边增量建库(每帧先 Query 再
  AddFrame,所以只会和更早的帧配对):

  1. BoW 检索:关键点描述子转 BoW,倒排文件查共享单词的帧;
  2. 过滤(比重定位多两条):
     - 共享词数 ≥ max(最大共享词数 × 0.5, 8)(重定位是 0.3,回环更严);
     - 剔除 id ≥ 当前帧的"未来帧"、剔除共视邻域帧(避免把紧邻帧当回环);
  3. 打分 + 共视分组:L1 相似度打分;候选帧与共视帧(共享观测
     > 10)合并成组,组内最高分帧当代表,组分 = 成员分数之和;
  4. 里程计距离过滤(回环特有):代表帧与当前帧的位姿距离必须 < 总里程 × 
     3%(odometry_length 在遍历时累加)——真回环在有漂移的里程计坐标下也应该"不算太
     远",这条能砍掉大量感知混叠;
  5. 组数 > 3 时剔除 < 最佳组 50% 的组,排序后取 **top-5** 组做 LightGlue
     精匹配(带 F 矩阵 RANSAC),取匹配最多的;匹配数 > 50 才进入几何验证。

  二、回环验证:相对位姿估计 RelativatePoseEstimation(:237–460)

  1. PnP 求相对位姿:查询帧特征 ↔ 回环帧的 Mappoint,固定 3D 点跑 g2o
     FrameOptimization;有效点 ≥ 50 且内点 ≥ 50
     才接受,得到查询帧位姿后换算出相对位姿 Rlq, tlq(回环帧 → 查询帧);
  2. 引导式重匹配(扩大约束):
     - 对 PnP 中是外点/没匹配上的查询特征:在其 BoW
       单词的倒排文件里、限定回环组内的帧中找描述子距离 < 5
       的最佳匹配,再用重投影误差校验;
     - 对匹配上但尚未三角化的 Mappoint:用相对位姿构造 F 矩阵做极线校验(<
       10px),通过则加观测并三角化;
  3. 产出两样东西:loop_frame_pairs(相对位姿约束,给位姿图)和
     merged_mappoints(查询帧点 ↔ 回环帧点的重复点对,给融合)。

  顺带一提:遍历时对每帧调 DetectSentences(把每条线上关键点的 BoW
  词序列当作"句子"),但 FindSameSentences/ComputeSentenseSimilarity
  在当前代码里没有任何调用点——是 AirVO 遗留/备用逻辑,现在验证全靠 PnP。

  三、位姿图优化 PoseGraphRefinement(:463–590)

  - 注意门槛:if(_map->_mappoints.size() < 80000) return; ——
    只有大地图才做位姿图,小地图直接跳到融合+全局 BA(反正全局 BA 会兜底);
  - 建图:所有关键帧 VertexVIPose 顶点(第 0
    帧固定),边有两类——相邻关键帧的里程计相对位姿边 +
    回环检测得到的回环约束边(EdgeRelativePose),PoseGraphOptimization 优化 20 次;
  - 修正传播:优化只动位姿,所以要事后搬运地图元素——对每帧算旧位姿→新位姿的刚体变
    换 (tr, tt),找到某点的任一观测帧,用该帧的变换直接搬 Mappoint
    位置;线用同一变换搬 Plücker 坐标(g2o::Line3D)和端点。

  四、地图融合 MergeMap(:593–955)

  回环两侧同一段路会被建成两套点/线,必须去重:

  1. 点融合 MergeMappoints:把 merged_mappoints 里的重复对做并查集式分组(一个点可
  能出现在多对里,组合并);每组选第一个有效的点当"最佳点",把其余点的观测(frame_id
  → keypoint_idx)全部转移给它(同步改帧上的指针和
  track_id),必要时重新三角化,其余点 SetBad() 并从地图删除。

  2. 中间全局 BA:GlobalBA(10, 10, 
  点线外点剔除都开)——融合后先粗优化一轮,把合并产生的不一致压下去。

  3. 线融合 MergeMaplines:线没有描述子匹配,靠共享 Mappoint 判重(又是点线耦合):
  - 统计每对线共享多少"线上的点"(建图时每帧的 points_on_lines 关系);
  - 共享 ≥ 5 个 → 直接同组;共享 3~4 个 → 调 check_is_same_line
    几何校验……但这个函数第一行就是 return 
    true;(:761,后面投影误差检验全是死代码),几何校验实际被禁用了;
  - 之后与点融合同款:分组、转移观测、TriangulateMaplineByMappoints
    重三角化、删冗余线。

  五、全局优化 GlobalMapOptimization(:1007)= GlobalBA(50, 40)

  标准的两阶段全局 BA(g2o_optimization.cc:1488):

  - 顶点:全部关键帧位姿(固定第 0 帧)+ 全部有效
    Mappoint(setMarginalized(true),利用 Schur 消元)+ 全部 Mapline(VertexLine3D);
  - 边:单目/双目点重投影边 + 单目/双目线重投影边,chi2 阈值来自配置 mr_euroc.yaml
    的 optimization(mono_point: 50, stereo_point: 75, mono_line: 50,
    stereo_line: 75),第一轮带鲁棒核;
  - 两阶段:优化 50 次 → 把 chi2 超阈值或深度为负的边 setLevel(1)
    剔除并去掉鲁棒核 → 再优化 40 次 →
    重新检查,把仍然超阈值的观测记为外点,RemoveOutliers/RemoveLineOutliers
    从地图数据结构里真正删掉;
  - 回写优化后的位姿、点位置、线坐标。

  六、收尾

  重建共视图(融合后观测关系变了)→
  BuildJunctionDatabase(在清理后的地图上训练交点词典、建交点 BoW
  库和结构图,供重定位用)→ 存 trajectory_v1.txt 和 AirSLAM_mapv1.bin(Boost
  二进制序列化,连数据库一起打包)。

  与重定位的对比:检索骨架相同(BoW → 共视分组 →
  LightGlue),但回环多了"排除邻域/未来帧 + 里程计距离过滤",验证用 PnP
  相对位姿(要产出约束边)而非交点结构图重排序;而重定位组分数只取 top-5
  求和、回环是全组求和。整个过程是单线程离线的,breakpoint
  参数只是在各阶段间停下来等你按 c。

✻ Crunched for 3m 11s · done Tuesday, Nov 3, 5:16 PM

※ recap: We documented the AirSLAM repo (CLAUDE.md created) and I've been explaining its architecture: feature extraction, matching/tracking, relocalization, and loop closure/map refinement. Nothing is in progress; just ask your next question about the codebase. (disable recaps in /config)

❯ 我如果要移植该项目的特征提取和匹配算法,以及构建特征database,并且保存和加载地  
  图,我应该怎么实现,怎么移植,怎么和我的项目对接                                 

  Thought for 3m 12s, searched for 1 pattern (ctrl+o to expand)

● 这是个很实际的问题。我基于对这个代码库依赖关系的分析,给你一份可落地的移植方案
  。先说两个必须知道的前提,再按三个子系统(耦合度从低到高)分别讲怎么拆、怎么改、
  怎么对接。

  ⚠️ 前提 1:许可证

  LICENSE.md 是 GPLv3。把这些代码移植进你的项目,你的项目若对外分发也必须以 GPLv3
  开源(纯内部使用不分发则无此义务)。另外网络模型本身来源各异(SuperPoint/SuperGl
  ue/LightGlue 官方权重通常限非商业,PLNet
  是作者自研),商用前需逐个确认。如果是商业闭源项目,更安全的路线是"参考架构、自己
  重写实现、用自己训练的模型",而不是直接拷代码。

  ⚠️ 前提 2:TensorRT 版本

  代码用的是 TRT 8.x 
  API(getBindingIndex、executeV2、buildSerializedNetwork)。你的环境若是 TRT
  10+,这些已被移除,需要改成
  getTensorName/setInputShape/setTensorAddress/enqueueV3 风格——改动集中在
  plnet.cpp、super_point.cpp、light_glue.cpp、super_glue.cpp 和
  tensorrtbuffer,工作量中等但必须做。

  ---

  子系统 A:特征提取 + 匹配(耦合度低,可近乎原样移植)

  需要拷的文件

  ┌───────────────────────────┬─────────────────────────────────────────────┐
  │           文件            │                    作用                     │
  ├───────────────────────────┼─────────────────────────────────────────────┤
  │ 3rdparty/tensorrtbuffer/  │ GPU buffer 管理,TRT 推理的地基              │
  │ 整个目录                  │                                             │
  ├───────────────────────────┼─────────────────────────────────────────────┤
  │ include/super_point.h +   │ SuperPoint 关键点                           │
  │ src/super_point.cpp       │                                             │
  ├───────────────────────────┼─────────────────────────────────────────────┤
  │ include/plnet.h +         │ PLNet 两阶段(点/线/交点)                    │
  │ src/plnet.cpp             │                                             │
  ├───────────────────────────┼─────────────────────────────────────────────┤
  │ include/light_glue.h +    │ LightGlue 匹配                              │
  │ src/light_glue.cpp        │                                             │
  ├───────────────────────────┼─────────────────────────────────────────────┤
  │ include/super_glue.h +    │ 可选,不用 SuperGlue 就不拷                  │
  │ src/super_glue.cpp        │                                             │
  ├───────────────────────────┼─────────────────────────────────────────────┤
  │ include/feature_detector. │                                             │
  │ h +                       │ 检测统一入口                                │
  │ src/feature_detector.cc   │                                             │
  ├───────────────────────────┼─────────────────────────────────────────────┤
  │ include/point_matcher.h + │ 匹配统一入口                                │
  │  src/point_matcher.cc     │                                             │
  ├───────────────────────────┼─────────────────────────────────────────────┤
  │ include/read_configs.h    │                                             │
  │ 里的                      │ 配置结构体(可拆出来)                        │
  │ PLNetConfig/SuperPointCon │                                             │
  │ fig/PointMatcherConfig    │                                             │
  ├───────────────────────────┼─────────────────────────────────────────────┤
  │ include/utils.h +         │ 只需要                                      │
  │ src/utils.cc 的一部分     │ ConcatenateFolderAndFileName、FileExists、M │
  │                           │ akeDir、PathExists、DescriptorDistance      │
  ├───────────────────────────┼─────────────────────────────────────────────┤
  │ output/*.onnx             │ 模型文件                                    │
  ├───────────────────────────┼─────────────────────────────────────────────┤
  │ (若要线匹配)src/line_proc │ 只拷这两个函数——是纯 Eigen/OpenCV           │
  │ essor.cc 里的             │ 自由函数;整个文件会拖进 g2o 和              │
  │ AssignPointsToLines +     │ opencv_ximgproc 依赖                        │
  │ MatchLines                │                                             │
  └───────────────────────────┴─────────────────────────────────────────────┘

  可以扔掉的依赖:ROS、g2o、Frame/Map/Camera 全部 SLAM
  类、boost、yaml-cpp(如果你把三个 Config
  结构体改接自己的配置系统)。剩下的依赖只有:Eigen3、OpenCV ≥ 
  4.2、CUDA、TensorRT(nvinfer + nvonnxparser)、C++17。这些文件里没有任何一行 ROS
  代码,所以对接 ROS1/ROS2/非 ROS 项目都一样。

  必须注意的适配点

  1. 输入输出约定:输入单通道灰度图(去畸变是你项目的事);输出是
     Eigen::Matrix<float, 259, N>(行 0=score, 1=x, 2=y, 3~258=256 维描述子)+
     线段 Vector4d。坐标已自动缩放回原图分辨率。
  2. PLNet 内部尺寸全部硬编码:resize 到 512×512(不保持长宽比)、stage-1 的 buffer
     维度写死(128×128×3 条线、top-300 交点)。不要试图改输入尺寸,ONNX
     模型就是按这个导出的。
  3. engine 缓存机制:首次运行会解析 ONNX 编译 .engine 写到
     model_dir(需要写权限,且很慢,几分钟级);engine 与 GPU 架构 + TRT
     版本绑定,换环境必须删掉重编。
  4. 线程安全:TRT execution context 不是线程安全的。多线程各自持有独立的
     FeatureDetector/PointMatcher 实例(engine
     可各自反序列化同一份文件),或全局加锁。
  5. 模式选择:原项目 VO 阶段 use_superpoint: 1(点用 SuperPoint,线用
     PLNet),重定位 use_superpoint: 0(全 PLNet)。如果你只要点特征,SuperPoint + 
     LightGlue 是最小组合,PLNet 可以不port;要线/交点才需要 PLNet。
  6. 匹配前 NormalizeKeypoints 的 scale 是
     LightGlue=0.5、SuperGlue=0.7,别搞混;outlier_rejection=true 时内部做 F 矩阵
     RANSAC(20px)。

  建议的对接方式:写一层 facade

  不要把 259×N 的 Eigen 矩阵直接渗进你的项目,包一层:

  // air_frontend.h —— 你项目唯一需要 include 的头
  struct AirFrameFeatures {
    std::vector<cv::KeyPoint> keypoints;              // 给你的跟踪/BA用
    cv::Mat descriptors;                              // N×256 
  float,给你的BoW/匹配用
    std::vector<Eigen::Vector4d> lines;               // 可选
    Eigen::Matrix<float,259,Eigen::Dynamic> raw;      // 
  匹配网络的原始输入,内部保留
  };

  class AirFrontend {
  public:
    AirFrontend(const std::string& model_dir, const Options& opt); // 内部build 
  engines
    void Extract(const cv::Mat& gray, AirFrameFeatures& out);
    int  Match(const AirFrameFeatures& a, const AirFrameFeatures& b,
               std::vector<cv::DMatch>& matches, bool geometric_check);
  };

  转换只有一处:raw 的行 1/2 → cv::KeyPoint,行 3~258 → descriptors(注意描述子是
  L2 归一化的 float,DescriptorDistance = 2(1−dᵀd) ∈ [0,4])。

  验证方法

  抄 demo/test_feature.cpp 的思路(去掉 ROS 和硬编码路径)写个最小 main:读一张图 →
  Extract → 画出点线存图;读两张图 → Match → 画匹配连线。先在原 Docker 环境(xuku
  anhit/air_slam:v4)里跑通,再迁到你的环境,能把"移植问题"和"环境问题"分开排查。

  ---

  子系统 B:特征 Database(耦合度中,核心是换掉 FramePtr)

  好消息:我查过 src/bow/database.cc,Database 对 SLAM 的耦合非常浅——FramePtr
  只被当作 map 的 key 用,FrameToBow 本来就有接受裸
  Eigen::Matrix<float,259,Dynamic> 的重载。移植步骤:

  1. 拷 3rdparty/DBoW2/ 整个目录。注意这是魔改版(加了 FSuperpoint
     特征类、WordIdToFeatures、倒排文件),不能用 GitHub 上的原版 DBoW2 替代;
  2. 拷 include/bow/FSuperpoint.h、src/bow/FSuperpoint.cc、include/bow/database.
     h、src/bow/database.cc;
  3. 全局把 FramePtr 替换成 int frame_id(或你自己的轻量句柄):_frame_bow_vectors
     、_inverted_file、AddFrame、Query 的签名;删掉两个接受 FramePtr 的
     FrameToBow 重载(保留 Eigen 矩阵版);
  4. serialize 函数同步修改——替换后不再需要 boost 的 shared_ptr 序列化,普通
     map<int,...> 即可(boost serialization 头文件可以保留,词典加载还要用,见下);
  5. 词典:直接用 voc/point_voc_L4.bin(k=10、L=4、TF-IDF 加权、L1_NORM 打分,针对
     256 维 SuperPoint 系描述子)。加载走 Database::LoadVocabulary(path),内部是
     boost 反序列化 SuperpointVocabulary(serialize 模板实现在 database.cc
     里)——所以词典文件也绑定 boost 序列化格式。想彻底去
     boost,可以自己遍历词典树导出成纯二进制再写个加载器;
  6. 想训练自己的词典(换描述子或提升域内性能):收集你数据上的描述子集合调
     voc->create(features),现成范本就是 MapRefiner::BuildJunctionDatabase(map_re
     finer.cc:956,交点词典就是这么在线训的,k=10、L=3)。

  移植后你的检索流水线(照抄原项目模式即可):

  入库:  FrameToBow(raw_features) → AddFrame(frame_id, word_features, 
  bow_vector)
  检索:  Query(bow) → map<id,共享词数>
  过滤:  共享词数 ≥ max(0.3×最大值, 8)          // 重定位用0.3,回环用0.5
  打分:  Score(库内bow, 查询bow)                 // L1相似度
  分组:  按你自己的共视/位姿邻近合并候选         // 可选
  验证:  AirFrontend::Match(带几何校验) + PnP    // 可选

  如果还要交点结构图那套重定位增强:额外需要 ① PLNet 的 junction 输出;② 把
  Frame::FindJunctionConnections(frame.cc:581)抽成自由函数——它只用到交点坐标、线
  段和图像宽高,很好抽;③ 用步骤 6 的方法训一个交点词典 + 第二个 Database 实例。

  ---

  子系统 C:地图保存/加载(耦合度高,建议不要原样移植)

  原项目的地图文件 AirSLAM_mapv{0,1}.bin 是整个 Map 类图的 boost 
  二进制序列化:Map → Camera + Frame + Mappoint + Mapline + 共视图 + 两个 
  Database + 词典,serialize 模板全部内联在头文件里,Frame 的序列化还引用 IMU
  预积分和 g2o types。这意味着:

  - 想原样读写这个格式,就得把 Frame/Mappoint/Mapline/Camera/Map/imu.h/g2o types 
    全套类都拷走,等于移植了半个 SLAM 后端;
  - boost 二进制归档与类布局、boost 版本强绑定,格式本身很脆。

  所以分两种情况:

  情况 1:你连 SLAM 后端一起要 → 整套拷贝上述类,接受"同编译器同 boost
  版本才能读旧地图"的约束。

  情况 2(推荐):你只要 A+B,地图格式自己设计 → 你需要的数据其实很少,建议这样的
  schema:

  my_map/
  ├── meta.yaml                 # 版本、相机内参、关键帧数
  ├── keyframes/
  │   └── <id>.bin              # timestamp, pose(4×4,可无),
  │                             # features 259×N (float), lines M×4,
  │                             # junctions K×259(可选), 描述子已含在259里
  └── voc.bin                   # 词典(或直接引用外部 point_voc_L4.bin)

  关键设计决策:
  - 倒排文件、BoW 向量不落盘,加载时重建:读每个关键帧的 raw features → FrameToBow
    → AddFrame,几百个关键帧也就秒级。这样地图格式完全不依赖 Database
    的内部结构,升级词典不用改地图;
  - 存储实现用裸 ofstream + Eigen 二进制写(Eigen::save 或手写 matrix.data()
    块)即可,想更工程化用 flatbuffers/protobuf;
  - 加载器输出
    vector<MyKeyframe>,你的项目怎么消费(可视化、重定位、接着建图)随你。

  与原项目地图互通的旁路:Map::SaveMap(map.cc:1227)还有一套文本导出格式(frames/<i
  d>.txt:id+位姿+每个特征的 track_id/坐标/描述子;mappoints.txt),格式简单稳定,适
  合写个解析器把原项目建的地图转进你的格式。注意 VO
  流程里这个调用被注释掉了(map_builder.cc:565),要用的话自己放开或单独调一次。

  ---

  移植顺序建议(每步都可独立验证)

  1. 最小闭环:在官方 Docker 里拷 A 的文件 + 一个最小
     CMake(find_package(CUDA/OpenCV) + 手动 find_path/find_library 定位
     NvInfer.h/nvinfer),跑通单图检测、双图匹配;
  2. 迁到你的环境:换出 Docker 后先只验证 engine
     能否重编成功(TRT/CUDA/驱动版本是第一雷区);
  3. facade 接入你的前端:替换你项目原有的特征提取,做 259 矩阵 ↔
     你的特征结构转换;
  4. 移植 
     Database(FramePtr→int),用一段自建序列验证"入库→检索→打分"行为与原项目一致;
  5. 实现自己的地图 save/load;
  6. (可选)线匹配、交点结构图、PnP 验证等增强。

  CMake 骨架供参考:

  find_package(OpenCV 4.2 REQUIRED)
  find_package(Eigen3 REQUIRED)
  find_package(CUDA REQUIRED)          # 或 enable_language(CUDA)
  find_path(TENSORRT_INCLUDE NvInfer.h HINTS ${TensorRT_ROOT}/include)
  find_library(NVINFER nvinfer HINTS ${TensorRT_ROOT}/lib)
  find_library(NVONNXPARSER nvonnxparser HINTS ${TensorRT_ROOT}/lib)

  add_subdirectory(3rdparty/tensorrtbuffer)
  add_subdirectory(3rdparty/DBoW2)
  add_library(air_frontend STATIC
    src/super_point.cpp src/plnet.cpp src/light_glue.cpp
    src/feature_detector.cc src/point_matcher.cc src/bow/database.cc
  src/bow/FSuperpoint.cc
    src/my_utils.cc)   # 只含你摘出来的utils函数
  target_link_libraries(air_frontend ${NVINFER} ${NVONNXPARSER} ${OpenCV_LIBS}
    ${CUDA_LIBRARIES} tensorrtbuffer DBoW2)

  ---

  最后一点:你说"和我的项目对接"——如果你告诉我你项目的形态(ROS1/ROS2?自己的
  VIO/SLAM 还是纯定位?目标平台是 PC 还是 Jetson?TRT
  版本?),我可以给出更具体的对接层设计和需要避开的坑(比如 Jetson 上要用 DLA 或
  FP16、TRT 10 的 API 迁移清单)。

✻ Churned for 4m 48s · done Wednesday 2:49 PM

※ recap: You're planning to port AirSLAM's feature extraction, matching, BoW database, and map I/O into your own project; I've delivered the full porting guide. Next: tell me your project's setup (ROS version, platform, TensorRT version) for concrete integration advice.

❯ frame->AddLeftFeatures 和frame->AddRightFeatures这两个函数是在干什么          

  Thought for 37s, searched for 1 pattern, ran 1 shell command (ctrl+o to expand)

● 这两个函数是 Frame 的"特征装载"入口(src/frame.cc:93 和 :139),分工很明确:左图特
  征构成帧的本体,右图特征只被"消费"成深度信息,右图特征本身不保存。逐个拆:

  AddLeftFeatures(features_left, lines_left) —— 建立帧的主体特征

  把左图的 259×N 特征矩阵装进 Frame,并初始化所有配套数据结构:

  1. _features = features_left:这份 259×N 矩阵成为整帧的"规范特征数组",之后所有
     按索引访问的东西(track_id、mappoint、深度、描述子)都以它为基准;
  2. 生成 cv::KeyPoint 数组:每列转成 KeyPoint(x, y, size=8, angle=-1, score);
  3. 建网格索引 _feature_grid:把每个关键点按坐标塞进 48×64
     的格子(FRAME_GRID_ROWS/COLS),供后续
     FindNeighborKeypoints/投影搜索快速找邻近点;
  4. 初始化立体信息为"无":_u_right 和 _depth 全部填 -1 —— 表示"还没有右图深度";
  5. 初始化跟踪关联:track_ids 全 -1、_mappoints 全
     nullptr(等跟踪线程从参考帧继承,或插入关键帧时分配新 id);
  6. 点线关联:存下左图线段 _lines,调 AssignPointsToLines 算出
     _points_on_lines(每条线上有哪些关键点、距离多少)——这就是后面 MatchLines
     投票匹配线、以及 TriangulateMaplineByMappoints 用点三角化线的基础数据;
  7. 线的跟踪关联初始化:_line_track_ids 全 -1、_maplines 全 nullptr。

  AddRightFeatures(features_right, lines_right, stereo_matches) —— 
  把右图变成左图特征的深度

  入参里的 stereo_matches 是已经用 LightGlue 匹配好的左右图点对。它做四件事:

  1. 极线约束过滤匹配(frame.cc:147–157):图像已校正,所以合法匹配必须满足 MinXDiff
     < |x_left − x_right| < MaxXDiff(视差范围对应有效深度范围,来自 camera yaml
     的 depth_lower/upper_thr)且 |y_left − y_right| ≤ MaxYDiff(同行约束);
  2. 计算立体深度(:159–173):对每个幸存匹配,记下 _u_right[idx_left] = 
     x_right(该点在右图的 u 坐标),并算 _depth[idx_left] = BF / 
     视差(经典双目公式)。返回的 good_stereo_point 就是有效立体点计数——MapBuilder
     用它判断初始化是否成立(< 90 不初始化)、关键帧是否够格(< 10 就推迟);
  3. 右图的点线关联 + 左右线匹配(:175–192):对右图特征也调
     AssignPointsToLines,然后用
     MatchLines(靠立体点对投票)把每条左图线对应到右图线,存进 _lines_right[i]
     并标记 _lines_right_valid[i]——这样插入关键帧时 TriangulateStereoLine
     就能直接双目三角化这条线;
  4. 右图特征用完即弃:右图的 259×N 矩阵不会存进 Frame,只在函数内临时用。

  为什么这么设计

  帧的身份就是左相机;右图唯一的贡献是给左图特征贴上 (u, v, u_right) 三元组。看
  GetKeypointPosition(frame.cc:216):它返回 Vector3d(x, y, 
  u_right),下游优化代码全靠 keypoint(2) > 0 区分——有右图 u 就是双目约束(stereo 
  edge,权重 75),是 -1 就是单目约束(mono edge,权重 50)。你在
  FramePoseOptimization、GlobalBA 里看到的 mono/stereo 分流就源于此。

  这也解释了 MapBuilder 里的调用模式:每一帧都只跑 AddLeftFeatures(普通帧连右图都
  不提取,省时间);只有初始化帧和关键帧(候选)才提取右图并调
  AddRightFeatures——普通帧跟踪靠"与参考关键帧的匹配 +
  继承深度"就够了,不需要新鲜的双目深度。
✻ Worked for 1m 8s · done 2:33 PM

❯ AssignPointsToLines函数内部的逻辑原理是什么                                   

  Thought for 1m 14s (ctrl+o to expand)

● AssignPointsToLines(src/line_processor.cc:68)做的事一句话概括:给每条检测出的线
  段,找出"落在这条线段上"的所有关键点,输出 relation[i] = map<关键点索引, 
  点到线距离>。这就是帧里 _points_on_lines
  的来源,是整个"点线耦合"的地基——线匹配投票(MatchLines)、用点三角化线(Triangulat
  eMaplineByMappoints)、回环融合线去重、"句子"BoW 全都消费这个结构。

  内部逻辑分三段:

  1. 预计算:线段的隐式方程(向量化)

  A = y2 − y1;   B = x1 − x2;   C = x2·y1 − x1·y2;   D = √(A² + B²)

  过两点 (x1,y1)、(x2,y2) 的直线可以写成隐式方程 A·x + B·y + C = 
  0(代入任一端点验证为 0)。其中:
  - (A, B) 是直线的法向量;
  - D = ‖(A,B)‖ 恰好等于线段长度;
  - 点到直线的距离有闭式公式:|A·px + B·py + C| / D。

  这些系数用 Eigen 数组运算对所有线一次算完(输入的点坐标取 259×N 矩阵的第 1、2
  行,线段数组用 Eigen::Map 零拷贝映射 Vector4d
  的连续内存)。不过后面的主循环仍是逐线×逐点的标量判断,复杂度 O(线数 × 点数)。

  2. 对每个(线 i, 点 j)做三道筛选

  ① 包围盒粗筛(便宜的就先做)
  点必须落在线段的轴对齐包围盒外扩 3px 内:

  if(px < min_lx − 3 || px > max_lx + 3 || py < min_ly − 3 || py > max_ly + 3)
  continue;

  大多数点在这一步就被拒掉,避免算后面的距离。注意包围盒只是必要条件——对斜线段,盒
  内的点也可能离线很远,所以需要第二道。

  ② 点到直线距离 ≤ 3px

  pl_distance = |A·px + B·py + C| / D;
  if(pl_distance > 3) continue;

  用的是无限长直线的距离公式,阈值 3
  像素。但通过这道只说明点在直线附近,可能落在线段的延长线上,所以需要第三道。

  ③ 投影落在线段内(余弦定理判断)

  side1 = |P − 端点1|²;  side2 = |P − 端点2|²;  line_side = |线段|² (= D²)
  接受条件: side1 ≤ 9  ||  side2 ≤ 9  ||  (side1 < line_side + side2 && side2 <
  line_side + side1)

  这是用勾股/余弦不等式做的"垂足是否在线段内"测试。对三角形 P-E1-E2:
  - side2 < side1 + line_side ⟺ E1 处的角是锐角 ⟺ P 在 E1 端的垂线"内侧";
  - side1 < side2 + line_side ⟺ E2 处的角是锐角;
  - 两角同时为锐 ⟺ P 的垂足严格落在线段内部。等价于常用的 0 ≤ (P−E1)·(E2−E1) ≤ 
    |E2−E1|²,但只用平方距离,不开方不算点积方向,数值上省事。

  前两个 ≤ 9(即距端点 3px 内,9 = 3²)是端点豁免条款,很关键:PLNet 检出的交点(junct
  ion)本来就在线段端点附近,检测器的定位噪声可能让它们略微越过端点、导致锐角测试
  失败——没有这条豁免,恰恰是信息量最大的端点/交点处关键点会被丢掉。

  3. 输出

  通过的点记入 points_on_line[j] = pl_distance——注意 value
  存的不是布尔而是实际垂直距离,虽然目前下游(MatchLines 投票、线三角化)只用
  key,距离值留着可以做加权。

  两个值得注意的点(尤其你要移植的话)

  1. 空线段会崩:Eigen::Map(lines[0].data(), ...) 在 lines
     为空时是未定义行为(对空 vector 取 lines[0])。原项目里 PLNet
     几乎总能出几条线所以没炸,移植时建议加一行 if(lines.empty()) { 
     relation.clear(); return; };
  2. 3px 是写死的:包围盒膨胀、距离阈值、端点豁免共用同一个魔数 3,和配置里的
     line_threshold 无关。如果你的图像分辨率与原项目(752×480
     一类)差很多,这个像素阈值可能要按比例调。

  设计上它就是典型的"粗筛→精算"漏斗:包围盒拒掉绝大多数点对(纯比较运算),距离公式
  和余弦测试只对少数候选做,所以在 400 点 × 上百条线的规模下每帧开销可以忽略。

✻ Cooked for 1m 47s · done 3:27 PM

※ recap: We documented AirSLAM (CLAUDE.md) and walked through its feature extraction, matching, tracking, relocalization, loop closure, and porting plan; last covered AssignPointsToLines internals. No pending action; ask your next question or name the porting step to start.

❯ MatchLines 内部的实现原理                                                     

  Thought for 1m 15s (ctrl+o to expand)

● MatchLines(src/line_processor.cc:122)解决的是一个很实际的问题:PLNet 输出的线段
  只有端点坐标和得分,没有描述子,也没有专门的线匹配网络——线根本没法直接做外观匹配
  。它的解法是:借用已经匹配好的关键点对当"证据",给线对投票。核心假设:如果帧 0
  的线 l0 和帧 1 的线 l1 是同一条物理线,那么"落在 l0 上的点"和"落在 l1
  上的点"之间应该存在大量已匹配的点对。

  实现分四步:

  第 1 步:倒排点-线关系

  输入 points_on_line0[i] = map<点idx, 距离> 是 AssignPointsToLines
  的输出(每条线上有哪些点)。先把它反转成每个点落在哪些线上:

  assigned_lines0[点idx] = {线id, 线id, ...}

  注意是 vector 而不是单个 id——一个点可以同时在多条线上(典型情况:交点处的关键点
  同时属于两条相交线;或检测出的重叠线段)。

  第 2 步:投票矩阵

  建一个 L0 × L1 的整数矩阵,遍历每一对已匹配的点 (idx0, idx1):

  for(l0 : idx0所在的线)
    for(l1 : idx1所在的线)
      matching_matrix(l0, l1) += 1;

  即:一对匹配点,给"它俩所在的线的每种组合"各投一票。matching_matrix(l0, l1)
  最终的物理含义是:连接 l0 和 l1 的匹配点对数量。

  投票为什么能区分真假?如果 l0、l1 真是同一条线,线上每一个成功匹配的关键点都会给
  它俩投一票,票数会累积到很高;而偶然组合(比如 l0 和一条与它相交的线
  l1',只有交点附近一两个点同时落在两者上)只能得到零星几票。

  第 3 步:互为最大 + 硬门槛

  对每行(frame 0 的线)和每列(frame 1 的线)分别找票数最大的位置,然后遍历列 j,接受
  l0 = col_max_location 与 l1 = j 这对匹配需要同时满足三个条件:

  1. col_max_val ≥ 
     2:至少两对匹配点支持。单票太脆——交点处的一个点偶然同时落在两条线上就能产生
     1 票;
  2. 互为最大(交叉检查):row_max_location[col_max_location] == j,即 l1 也必须是
     l0 的最佳拍板对象。这保证匹配的唯一性:一个 frame-0 的线最多得到一个 frame-1
     的匹配(平票时 maxCoeff 取第一个最大,只有一个 j
     能通过互检),避免多条线争抢同一条;
  3. 覆盖率得分 ≥ 0.8:见下。

  第 4 步:得分公式的几何含义

  score = votes² / min(l0上的点数, l1上的点数) ≥ 0.8

  把式子拆开看:score = votes × (votes / min(N0, N1)),第二个因子是覆盖比——较短那
  条线上的点有多大比例通过匹配点连到了对方。所以这个得分同时惩罚两种情况:

  - 绝对证据太少:votes 小则 score 小(平方放大惩罚);
  - 相对覆盖太低:长线只匹配上一小段也不行。

  它还隐含一个随线长自适应的门槛:通过需要 votes ≥ √(0.8 × min(N0,N1)),即短线(5
  个点)要 2 票,长线(45 个点)要 6
  票——线越长,偶然票越多,要求的支持也水涨船高。举两个例子:短线 10 个点、9 票 →
  81/10 = 8.1,轻松通过;10 个点只有 2 票 → 4/10 = 0.4,拒绝。

  通过的写入输出:line_matches[l0] = l1(按 frame 0 的线索引,未匹配的保持 -1)。

  为什么这个设计好

  1. 零额外网络开销:线匹配完全搭点匹配的便车,而这正是论文"点线耦合"(coupled)的体
     现之一;
  2. 抗光照:线的"匹配"最终建立在 SuperPoint/LightGlue
     这类抗光照的点特征之上,线自己不需要外观;
  3. 便宜:O(P·k² + L0·L1),k 是每点平均所在线数(通常 1,交点处 2),矩阵就百来个
     int;
  4. 两处复用,同一函数干两件事:
     - Frame::AddRightFeatures:传左右图的立体点匹配 → 匹配左右线的同名线 → 存
       _lines_right 供双目三角化线;
     - MapBuilder::TrackFrame:传参考关键帧↔当前帧的点匹配 → 时间方向的线跟踪 →
       传播 line_track_id 和 Mapline 指针。

  弱点(移植时留意)

  - 完全依赖点匹配质量:LightGlue 在弱纹理/大视角变化下失败时,线也跟着匹配不上——
    点挂了线没有任何独立救回的手段;
  - 3px
    的点线归属容差在密集交点区域会产生串票(一个点属于多条线,笛卡尔积式投票),靠
    ≥2 票和 0.8 得分兜底,但极端情况仍可能错配;
  - 只输出单向(frame0 →
    frame1)结果,靠互检保证一致;平票时取第一个最大,行为确定但未必选对;
  - 代码里 row_max_value、col_max_value
    两个向量填了但从未参与判断,是死变量,移植时可以删。

✻ Brewed for 1m 50s · done 4:07 PM

❯ AddKeyframeCheck内部的实现原理                                                

  Thought for 1m 54s (ctrl+o to expand)

● AddKeyframeCheck(src/map_builder.cc:434)是关键帧插入策略的决策核心,在特征线程
  里被调用。它拿到的材料是:当前帧 ↔ 参考关键帧(上一个关键帧)的 LightGlue
  匹配结果(已经过 F 矩阵 RANSAC 几何校验),输出一个三级决策:

  // 返回值: 0 = 当前帧立即作关键帧; 1 = 下一帧作关键帧; 2 = 不插

  对应的配置在 vo_euroc.yaml:min_num_match: 30, max_num_match: 80, 
  tracking_point_rate: 0.65, tracking_parallax_rate: 0.1。

  判定逻辑(按执行顺序)

  ① 紧急判定:跟踪快断了 → 返回 0

  if(match_num < min_num_match /*30*/) return 0;

  与参考关键帧的匹配数跌破
  30,说明跟踪濒临失败(剧烈运动/模糊/遮挡/视角突变)。这是唯一返回 0 
  的路径——必须立刻把当前帧转成关键帧,刷新参考、给地图重新锚定,来不及等下一帧。

  ② IMU 未初始化时的阈值特判

  if(UseIMU() && !_map->IMUInit()){
    feature_tracking_thr *= 1.1;   // 0.65 → 0.715
    ration_thr *= 0.7;             // 0.1  → 0.07
  }

  VI-SLAM 初始化(估尺度、重力、bias)需要足够的运动激励和多样视角。这两个调整都朝
  更激进插帧的方向:跟踪率阈值调高 → 更容易判"匹配率不足";视差阈值调低 →
  视差条件更容易触发(阈值是 图像面积 × thr²,从 ~3610px² 降到
  ~1768px²)。初始化完成后恢复原值。

  ③ 冗余判定:当前帧信息量够大 → 返回 1

  if(match_num / ref_features.cols() < 0.65      // 参考帧的特征只剩<65%还被跟踪
  || match_num / current_features.cols() < 0.65  // 当前帧有>35%是新出现的特征
  || match_num < max_num_match /*80*/)           // 绝对匹配数偏低(30~80之间)
    return 1;

  三个条件从不同角度度量"当前视野相对参考关键帧已经变化多少":
  - match/参考帧比例低 → 参考帧内容大量丢失(旋转、遮挡、出视野);
  - match/当前帧比例低 → 大量新内容进入视野(典型:前进运动);
  - 绝对数在 30~80 之间 → 不算危险但已经偏弱。

  任一成立,说明"该换新关键帧了",但注意返回的是 1(下一帧)而不是 0——因为匹配数 ≥
  30,当前帧还能可靠跟踪,不紧急。

  ④ 视差判定:相机走远了 → 返回 1

  parallax = 参考帧关键点坐标 − 当前帧关键点坐标;   // 每对匹配点的2D位移
  average_parallax = (parallax * parallax.transpose()).sum() / match_num;
  if(average_parallax > 图像宽×高 × 0.1² /*≈3610px²*/) return 1;

  匹配率都健康,但如果匹配点的平均像素位移很大,说明相机相对参考关键帧平移/旋转已
  经可观——参考帧"过期"了,新关键帧能提供更长的三角化基线。EuRoC
  分辨率下阈值折算成 RMS 约 60px。

  ⑤ 都不触发 → 返回 2

  匹配又多又稳、视差又小:当前帧相对参考关键帧是冗余的,插了只会白白增加后端优化负
  担,不插。

  返回值如何被调用方消费(理解 0 和 1 的区别)

  在 ExtractFeatureThread(map_builder.cc:106–127)里:

  - 返回 0(紧急):如果当前帧还是 NormalFrame(没提过右图),当场补做右图 SuperPoint
    提取 + 左右立体匹配,然后检查 good_stereo_point ≥ 
    10——够格才真插;不够(立体深度太少,插了也三角化不出东西)就降级为普通帧,并置
    _insert_next_keyframe = true 让下一帧重试;
  - 返回 1(计划性):置 _insert_next_keyframe
    标志。下一帧从一进特征线程就走关键帧候选路径:左右图 +
    交点全提取、立体匹配、预先定为 KeyFrame
    类型——把昂贵的双目处理提前安排而不是事后补救;
  - 返回 2:普通帧,继续跟踪。

  所以设计哲学是:0 = 不惜代价立即插(应急),1 = 预约下一帧插(常规),2 = 
  不插(冗余)。常规路径统一走"预约",保证成为关键帧的那一帧从提取阶段就是完整准备
  过的(有右图、有立体深度、有交点)。

  一个值得注意的实现细节(移植时留意)

  视差的计算式 (parallax * parallax.transpose()).sum() 展开后是:

  Σ(dxᵢ + dyᵢ)² / N  =  平均平方视差 + 2·mean(dx·dy)

  而意图上的平均平方视差应该是 Σ(dx² + dy²)/N(即那个 2×2 矩阵的迹,.trace(),或
  parallax.array().square().sum())。现在的写法多了一个交叉项
  2·mean(dx·dy):当运动方向沿对角线(dx、dy 同号)时视差被高估最多 2 倍,反向相关时
  被低估。实际能跑是因为阈值本身是经验调出来的,但有效阈值随运动方向变化。这与
  ORB-SLAM2 里"平均视差"的写法不同(那边是逐点算 dx*dx+dy*dy
  再平均)。如果你要移植:照抄则行为与原项目完全一致;改成 .trace()
  更合数学意图,但关键帧插入节奏会略有变化,阈值 0.1 可能需要重调。

  整体上这套策略可以看作 ORB-SLAM 关键帧插入的简化版:同样基于"跟踪冗余度 +
  视差"思想,但没有共视关系评分和"尽量多插"的激进策略,全部阈值集中在 keyframe
  配置段,换数据集时只需要调这四个数。

✻ Cooked for 2m 33s · done 4:25 PM

❯ /export airslam_learn.md                                                      
  ⎿  Conversation exported to:
     /home/paco/work_prjs/open_codes/AirSLAM/airslam_learn.md

❯ map.cc中的InsertKeyframe函数解析                                              

  Thought for 1m 59s, searched for 2 patterns, ran 3 shell commands (ctrl+o to expand)

● Map::InsertKeyframe(src/map.cc:30–120)是 AirSLAM 的局部建图(Local 
  Mapping)入口。先说清它的调用位置:MapBuilder::TrackingThread →
  MapBuilder::InsertKeyframe(map_builder.cc:473,负责给无 id 的特征分配新
  track_id)→ Map::InsertKeyframe。注意这个项目没有独立的 local mapping 
  线程,下面这些工作(包括局部
  BA)全部在跟踪线程里同步执行——特征线程的缓冲队列(上限 5 帧)提供背压,防止跑飞。

  函数体按五个阶段走:

  ① 注册关键帧

  _keyframes[frame_id] = frame;  _keyframe_ids.push_back(frame_id);

  ② Mappoint 的创建与观测挂接(:36–72)

  遍历该帧的每个特征 i:

  - 没有 mappoint 的特征 → 新建:new Mappoint(track_ids[i]) ——Mappoint 的 id 
    直接就是 track_id,这是帧特征与地图点之间唯一的身份纽带(跟踪线程传播
    track_id,地图端按 id 建点)。随后:
    - SetDescriptor:把该特征的 256 维描述子存为点的代表描述子(后续
      BoW/重定位用);
    - BackProjectPoint 给初始 3D 位置——注意(frame.cc:299)它要求 _depth[idx] > 
      0,即只有带立体深度的特征能反投影出初值;纯单目特征建出来的点初始无位置,处于
      UnTriangulated 状态,等多视图三角化;
  - 每个特征都做:mpt->AddObverser(frame_id, i) 建立双向观测链(帧→点靠
    _mappoints[i],点→帧靠 obversers map),这是后面一切三角化、局部
    BA、外点剔除的数据基础;
  - 触发三角化:点仍是 UnTriangulated 且观测数 > 2 → TriangulateMappoint。

  TriangulateMappoint(:367)的原理

  对所有观测帧:关键点 BackProjectMono 成单位射线,乘帧旋转得到世界系下的 bearing 
  向量,同时记下各相机光心位置。然后解一个线性最小二乘——找 3D 点 p
  使它到所有射线的垂直距离平方和最小:

  AxtAx = N·I − Σ b̂ᵢb̂ᵢᵀ ,  Axtbx = Σcᵢ − Σ b̂ᵢ(b̂ᵢᵀcᵢ)

  用 ColPivHouseholderQR 求解,秩 < 3 直接放弃(射线共面/平行,即视差不足,点保持
  UnTriangulated
  等以后)。注意这里没有视差角、重投影误差检查——质量控制完全后置给局部 BA
  的外点剔除。

  ③ Mapline 的创建与三角化(:74–108)

  对每条线 i,同样的模式,但多一条捷径:

  - 有右图匹配线(_lines_right_valid[i],来自 AddRightFeatures 的立体线匹配)→ 立即
    TriangulateStereoLine:左右两条 2D 线直接三角化出 3D 端点,标记该帧端点状态为
    1;
  - 否则等观测数 ≥ 2 时走 TriangulateMaplineByMappoints。

  TriangulateMaplineByMappoints(:416)——"用点三角化线"

  这是点线耦合最典型的体现,线不直接做多视图几何,而是:

  1. 收集线上的 3D 点:遍历所有观测帧,取该帧 GetPointsOnLine(idx)(就是
     AssignPointsToLines 算好的点-线归属),把这些关键点挂着的有效 Mappoint 
     的世界坐标收进来(距离 > 3px 的跳过,去重),不足 3 个点则失败;
  2. 鲁棒拟合直线:最多迭代 4 轮 cv::fitLine(DIST_HUBER) → 算每个点到线的 3D 距离
     → 保留 < 0.1m 的内点 → 重拟合,直到全是内点或点不够;
  3. 转 Plücker 坐标:g2o::Line3D::fromCartesian 存为线的 3D
     表示(优化里用的就是它);
  4. 确定端点:找方向向量绝对值最大的分量轴,把内点沿该轴排序,取最两端的点作为线段
     端点——即线段的" extent"由线上点的分布范围决定(所以端点会随观测增多而变化,有
     SetEndpointsUpdateStatus(false) 标记待更新);
  5. 所有观测帧的端点状态置 1。

  ④ 局部 BA:LocalMapOptimization(:556–855)

  关键帧 ≥ 2 才做(第一个关键帧只记录为 imu_init_frame)。流程:

  1. 选窗口:沿 PreviousFrame 链往回数,最多 5 个最新关键帧;窗口最老帧(以及地图第
     0 帧)位姿固定;
  2. 收集固定帧:窗口外的关键帧,只要观测到窗口内任何点/线,就按观测数排序后以固定
     位姿加入优化(fixed_frames),把窗口锚在外部结构上;
  3. 收集地图元素:窗口帧观测到的所有有效 Mappoint/Mapline(用
     local_map_optimization_frame_id 时间戳去重,避免重复遍历);
  4. 建约束:
     - 点:keypoint(2) > 0(有 u_right)→ 双目边,否则单目边,pixel_sigma 都是
       0.8;至少 1 个双目或 ≥ 2 个单目观测才入优化(保证可解);
     - 线:有右图线 → 双目线边,否则单目线边;sigma 有个特别设定:观测数 > 3 ? 0.1 :
       0.001——观测多的线反而放宽权重;
     - IMU 已初始化 → 加速度/bias 顶点和相邻帧间的预积分边;
  5. 优化与剔除外点:LocalmapOptimization 内部先优化 5 次 → 按 chi2 阈值(配置里
     mono_point:50/stereo_point:75/mono_line:50/stereo_line:75)标记外点并去掉鲁
     棒核 → 再优化 15 次;标记为非内点的观测经 RemoveOutliers/RemoveLineOutliers
     真正断开帧-元素观测关系(失去所有观测的点/线被删除);
  6. 回写:非固定帧的新位姿、速度、bias,点的新位置,线的 Plücker 坐标 +
     UppdateMapline 重算端点;最后发布可视化。

  ⑤ IMU 初始化触发(:115–117)

  VI-SLAM 模式且 IMU 未初始化 →
  InitializeIMU(frame)(:1046)。门槛条件:距第一个关键帧 ≥ 3 秒、窗口内 ≥ 10
  个关键帧、且相邻帧位移都 ≥ 5mm(静止不动直接失败并重置
  imu_init_frame,等下一次有运动再试)。通过后:先用线性方法估陀螺
  bias(ComputeGyrBias)、从速度序列提取重力方向(ComputeVelocity),再用带 IMU
  预积分边的 g2o 优化联合精化位姿/速度/bias/重力,成功后设置 _Rwg 和 _imu_init = 
  true——此后跟踪的位姿初值就能走预积分预测路径了。

  收尾细节

  MapBuilder::InsertKeyframe 在 Map::InsertKeyframe
  返回后还做两件事:_map->UpdateFrameTrackIds(_track_id) 处理一个延迟建点队列
  to_update_track_id(别处标记的"该补建
  mappoint"的特征,在此统一建点挂观测,map.cc:885),以及用当前 bias
  重置预积分器(开始累积到下一关键帧的 IMU 数据)。

  一图总结数据流:

  关键帧(带track_id) ──► 建点/挂观测 ──► 多视图三角化点(最小二乘射线交)
                  └──► 建线/挂观测 ──► 有线立体匹配? ─是─► 双目直接三角化
                                          └─否─► 用线上的3D点拟合(Plücker+端点)
                  └──► 5帧滑窗局部BA(点边+线边+IMU边,固定帧锚定) ──► 剔外点 ──► 
  回写
                  └──► (VI-SLAM) 满足运动激励则初始化IMU(bias/重力/尺度)

✻ Brewed for 3m 0s · done 4:53 PM

※ recap: We're studying the AirSLAM codebase (CLAUDE.md created), walking through its internals: feature extraction/matching, tracking, relocalization, loop closure, and most recently Map::InsertKeyframe's local mapping logic. Next: tell me which module to analyze, or continue the porting plan.

❯ TrackFrame函数解析                                                            

  Thought for 2m 9s, searched for 1 pattern (ctrl+o to expand)

● TrackFrame(src/map_builder.cc:235–290)是跟踪线程的核心:对每个非初始化帧,把特征
  线程算好的"当前帧 ↔
  参考关键帧"点匹配,升级成当前帧与地图元素(Mappoint/Mapline)的关联 + 
  帧位姿。它是典型的"先试算、成功才提交"两阶段结构。

  输入与上下文

  int TrackFrame(FramePtr ref_frame,        // 参考关键帧(不是上一帧!)
                 FramePtr current_frame,    // 当前帧
                 std::vector<cv::DMatch>& matches,  // 
  特征线程已算好的点匹配(LightGlue + F-RANSAC)
                 Preinteration& preinteration)      // 
  参考关键帧→当前帧的IMU预积分

  注意 ref_frame 是上一个关键帧:所有普通帧都直接锚定到关键帧的地图元素上跟踪,而
  不是帧到帧接力——避免误差逐帧累积,这是关键帧法的标准做法。

  第 1 步:线匹配(搭点匹配的便车)

  MatchLines(ref_points_on_lines, current_points_on_lines, matches, ...,
  line_matches);

  用当前已有的点匹配 + 两帧各自的 _points_on_lines(点线归属)跑投票匹配,输出
  line_matches[i] = j(参考帧第 i 条线 ↔ 当前帧第 j 条线,-1 为未匹配)。

  一个容易忽略的事实:普通帧根本没提线(ExtractFeatureThread 里 NormalFrame
  只跑单图点检测,left_lines 为空),所以 MatchLines
  对普通帧是空操作——线跟踪实际只在关键帧候选帧上发生。这与"只有关键帧进地图"的设
  计自洽:普通帧不需要线的地图关联。

  第 2 步:点匹配 → 地图关联(试算阶段)

  std::vector<int> inliers(N, -1);                    // 全部先标 -1
  std::vector<MappointPtr> matched_mappoints(N, nullptr);
  for(match : matches){
    matched_mappoints[idx1] = ref_frame_mappoints[idx0];   // 
  继承参考帧特征挂的3D点(可能为nullptr)
    inliers[idx1] = ref_frame->GetTrackId(idx0);           // 
  预置为参考帧的track_id
  }

  两个细节:
  - matched_mappoints 可能是 nullptr——参考帧特征的点可能已被局部 BA
    当外点剔除(RemoveOutliers 会断开帧-点链接);nullptr 的点在位姿优化里被跳过;
  - inliers 数组在这里语义复用:优化前它存的是参考帧 track_id(>0
    表示"有候选关联"),优化后 FramePoseOptimization 会把外点位置改写成
    -1。所以最终 inliers[idx] > 0 同时意味着"是内点"且"参考帧有合法 track_id"。

  第 3 步:帧位姿优化

  int num_inliers = FramePoseOptimization(ref_frame, current_frame,
  matched_mappoints, inliers, preinteration);

  (前面聊过,这里概括)初值三级回退:IMU 预积分预测(位移 >1m 判异常)→
  cv::solvePnPRansac(内点不足或位移异常再退)→ 上一跟踪帧位姿;然后 g2o 固定全部
  3D 点、只优化当前帧位姿(VI
  模式联合速度/bias,加预积分边),约束是单目/双目点重投影(sigma 0.8),按 chi2
  标记外点(inliers[idx] = -1),返回内点数。线约束在这一步不参与。

  第 4 步:提交阶段(有门槛)

  if(num_inliers > lost_num_match /*10*/){

  只有内点数过线才提交关联,做三件事:

  1. 传播点的身份:对每个内点匹配,current_frame->SetTrackId(idx1, ref的track_id)
     + InsertMappoint(idx1, 同一个Mappoint指针)——当前帧正式"看见"了这个地图点;
  2. 就地清洗 matches:外点匹配从 matches 里 erase(引用传参,清洗后的结果流向
     PublishFrame 可视化;注意关键帧决策 AddKeyframeCheck
     早在特征线程就用未清洗的匹配做完了);
  3. 传播线的身份:对 line_matches[i] = j ≥ 0 且参考帧线有合法 line_track_id
     的,当前帧第 j 条线继承 track_id 和 Mapline 指针。

  如果跟踪失败(≤10 内点)则什么都不提交:当前帧所有 track_id 保持 -1、无
  mappoint。后果是优雅的——该帧照常输出位姿(用回退初值),如果它之后被选为关键帧,Ma
  pBuilder::InsertKeyframe 会给它所有无 id 的特征分配全新
  track_id、建全新地图点,相当于跟踪断裂后重新起锚。

  返回值的去向

  TrackingThread 里:track_inliers > lost_num_match 时更新 _last_tracked_frame = 
  frame——它是下一帧 PnP 合理性检查("位移 <
  1m")的参照,只记成功跟踪的帧,防止一帧坏位姿污染后续初值判断。

  一个真实的边界缺陷

  提交检查点用的是 inliers[idx1] > 0,而线那边用的是 line_track_id >= 
  0——不一致,且点这边是错的。_track_id 从 0
  起计数(map_builder.cc:25,后置自增),第一个关键帧的 0 号特征 track_id 就是
  0:它永远通不过 > 0 检查,匹配被误 erase、track_id
  不传播;等含它的帧成为关键帧时会为它建新 id、新点,造成这一个点的重复建图。影响
  范围只有一个点,所以实际无人察觉,但如果你移植这段逻辑,建议改成 >= 
  0(线的写法就是对的)。

  小结(数据流)

  点匹配(特征线程,LightGlue+RANSAC)
          │
          ├─► MatchLines ──► line_matches(仅关键帧候选有线)
          ├─► 试算关联: matched_mappoints + inliers(=ref track_id)
          ├─► FramePoseOptimization: 初值(IMU→PnP→上帧) + g2o位姿优化 ──► 
  num_inliers, 外点置-1
          └─► num_inliers > 10 ?
                ├─ 是: 提交 track_id/Mappoint/Mapline 继承, 清洗matches
                └─ 否: 全部不提交(该帧若成关键帧则重新起锚)

✻ Brewed for 2m 52s · done 6:00 PM

※ recap: We're studying the AirSLAM codebase: I created CLAUDE.md, then explained feature extraction, matching/tracking, relocalization, loop closure, and key functions like InsertKeyframe and TrackFrame. Next: tell me which function or subsystem to analyze, or your porting question.