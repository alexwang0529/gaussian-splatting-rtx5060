# 训练、评估与工具用法

先按[中文配置教程](README-CN.md)安装环境。在仓库根目录打开 PowerShell，激活 `gaussian-splatting` 环境。将示例中的输入和输出改成自己的路径。

## 从图片或视频开始

图片放入 `data/my_scene/input/`。以下两个命令分别从图片集和视频开始。它们会调用 COLMAP 预处理并启动 CUDA 训练。视频流程需要 FFmpeg。

```powershell
conda activate gaussian-splatting
python .\train_images.py -s .\data\my_scene -m .\output\my_scene
python .\train_video.py --video .\data\my_video.mp4 -s .\data\video_scene -m .\output\video_scene --fps 2
```

视频已抽帧时可追加 `--skip_extraction`，COLMAP 也已完成时再追加 `--skip_conversion`。更换视频或抽帧频率时使用新的数据目录。`--no_gpu` 让 COLMAP 使用 CPU，训练仍使用 CUDA。

只运行 COLMAP 时可执行 `python .\convert.py -s .\data\my_scene`。已有 `images/` 与 `sparse/0/` 的场景可以直接传给 `train.py`。显存紧张时可试用 `-r 2 --data_device cpu`，分别降低输入分辨率和将图像缓存放在系统内存。

## 渲染和评估

在训练时加入 `--eval` 留出测试视角，然后渲染并计算 PSNR、SSIM 和 LPIPS。LPIPS 首次运行需要下载 VGG16 和 LPIPS 权重。

```powershell
python .\train.py -s .\data\my_scene -m .\output\my_scene_eval --eval
python .\render.py -m .\output\my_scene_eval
python .\metrics.py -m .\output\my_scene_eval
```

平均指标写入 `results.json`，逐视角指标写入 `per_view.json`。也可直接编辑 `video_train_eval.py` 顶部的输入视频和目录参数，串联抽帧、预处理、训练、渲染和评估。

## 查看与导出

按[配置教程](README-CN.md#8-准备本地外部工具)安装 SIBR 后，可打开保存的模型，或连接训练进程。远程查看默认连接 `127.0.0.1:6009`，需要启动保留 Viewer 的训练，且 `-s` 应指向同一个场景。旧版 SIBR 建议使用英文或数字场景子目录名。

```powershell
python .\SIBR_viewer.py -m .\output\my_scene_eval
python .\SIBR_remote_viewer.py -s .\data\my_scene
```

默认 30000 轮训练的高斯模型位于 `point_cloud/iteration_30000/point_cloud.ply`。可用下面的脚本将高斯中心和近似 RGB 颜色导出为普通 PLY 点云。

```powershell
python .\export_point_cloud.py -i .\output\my_scene_eval\point_cloud\iteration_30000\point_cloud.ply -o .\output\my_scene_eval\point_cloud_rgb.ply
```

## 调整输入图像大小

```powershell
python .\resize_images.py -s .\data\my_scene\input -o .\data\my_scene_small\input --width 1280
```

默认保持宽高比。缩放后的图片需要重新进行 COLMAP 预处理。
