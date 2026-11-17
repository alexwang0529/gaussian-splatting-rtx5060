# 3D Gaussian Splatting · Windows / RTX 5060 Laptop

[English](README.md) · **简体中文**

本项目在 Windows 和 RTX 5060 Laptop GPU 上运行 GraphDeco 的 3D Gaussian Splatting 训练与渲染代码，提供编译器与 CUDA 配置，以及场景预处理、训练、评估、查看和点云导出脚本。请准备自己的图片或视频，并按下文安装对应外部工具。

## 相较 GraphDeco 官方仓库的改动

以下改动以 GraphDeco 的固定基线提交 `54c035f` 为参照。 [上游 README](https://github.com/graphdeco-inria/gaussian-splatting/blob/54c035f7834b564019656c3e3fcc3646292f727d/README.md)

| 文件 | 改动与作用 |
| --- | --- |
| [`environment.windows-cu128.yml`](environment.windows-cu128.yml), [`requirements.windows.txt`](requirements.windows.txt), [`setup_windows.ps1`](setup_windows.ps1), [`scripts/verify_gpu.py`](scripts/verify_gpu.py) | 上游环境固定了 Python 3.7.13、PyTorch 1.12.1 和 CUDA 11.6。本项目使用 Python 3.10 与 PyTorch 2.7.1/cu128，加载 MSVC 14.38，为 `sm_120` 编译，并在 GPU 上验证 CUDA 扩展。 |
| [`train_images.py`](train_images.py), [`train_video.py`](train_video.py), [`video_train_eval.py`](video_train_eval.py) | 新增图片训练、视频训练、视频到评估三个入口。脚本使用当前 Python 解释器，子进程失败时终止后续步骤。 |
| [`convert.py`](convert.py), [`utils/local_tools.py`](utils/local_tools.py) | 支持查找项目内的外部工具和 `PATH` 中的可执行文件。在场景目录内以相对路径传递数据库和图片位置，适配含中文字符的 Windows 路径下的 COLMAP 3.8。 |
| [`SIBR_viewer.py`](SIBR_viewer.py), [`SIBR_remote_viewer.py`](SIBR_remote_viewer.py), [`gaussian_renderer/network_gui.py`](gaussian_renderer/network_gui.py), [`train.py`](train.py) | 新增本地和实时查看器启动脚本。训练端读取完整 TCP 消息，以 UTF-8 字节长度发送路径，并报告断线错误。远程启动器可为旧版查看器提供 ASCII 相对场景路径。 |
| [`scene/gaussian_model.py`](scene/gaussian_model.py) | 每批写入 65,536 个高斯点以降低保存 PLY 时的系统内存峰值，写入成功后再用临时文件替换目标。 |
| [`metrics.py`](metrics.py) | 复用单个 VGG LPIPS 网络，关闭梯度计算，评估失败时返回非零退出码。PSNR、SSIM 和 LPIPS 沿用上游定义。 |
| [`resize_images.py`](resize_images.py), [`export_point_cloud.py`](export_point_cloud.py) | 新增等比例缩图和图片采样，以及将高斯中心与近似 RGB 颜色导出为普通 PLY 点云的功能。 |

## Windows 配置教程

### 1. 安装前置软件

下列组合已在 Windows 上验证。准备支持子模块的 Git for Windows，并确保 PowerShell 中能使用 Conda。如需初始化，运行 `conda init powershell` 后重新打开终端。

| 组件 | 已验证配置 |
| --- | --- |
| 电脑 / 显卡 | Lenovo Legion R7000P ADR10 (83LT), NVIDIA GeForce RTX 5060 Laptop GPU (8 GB, `sm_120`) |
| NVIDIA 驱动 | 592.01 |
| Python | 3.10.22 (Conda) |
| PyTorch / torchvision | 2.7.1+cu128 / 0.22.1+cu128 |
| CUDA Toolkit | 12.8 Update 1 (`nvcc V12.8.93`) |
| Windows 编译器 | Visual Studio 2022 / MSVC 14.38.33130 (`cl 19.38.x`) |
| NumPy / OpenCV | 1.26.4 / 4.11.0.86 |

1. 在 Visual Studio Installer 中为 Visual Studio 2022 或 Build Tools 2022 选择 **使用 C++ 的桌面开发**。在 **单个组件** 中勾选 **MSVC v143 x64/x86 生成工具（v14.38–17.8）** 和一个 Windows 10 或 11 SDK。
2. 安装适用于 Windows x86-64 的 CUDA Toolkit 12.8 Update 1。安装脚本默认从 `C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.8` 查找工具包。
3. 打开 PowerShell，运行 `nvidia-smi` 和 `nvcc --version`。前者显示驱动支持的 CUDA 版本，使用 `nvcc` 确认实际用于编译的 Toolkit 版本。

[Visual Studio](https://visualstudio.microsoft.com/vs/older-downloads/) · [MSVC / CUDA 12.8](https://docs.nvidia.com/cuda/archive/12.8.1/cuda-installation-guide-microsoft-windows/index.html#system-requirements) · [CUDA Toolkit 12.8.1](https://developer.nvidia.com/cuda-12-8-1-download-archive) · [Miniconda](https://www.anaconda.com/docs/getting-started/miniconda/main) · [PyTorch 2.7.1](https://pytorch.org/get-started/previous-versions/#v271)

### 2. 克隆仓库、创建环境并编译扩展

在 PowerShell 中运行以下命令。如果已有 `gaussian-splatting` 环境，激活后直接运行安装脚本。

```powershell
git clone --recurse-submodules https://github.com/alexwang0529/gaussian-splatting-rtx5060.git
Set-Location .\gaussian-splatting-rtx5060
conda env create -f .\environment.windows-cu128.yml
conda activate gaussian-splatting
powershell -ExecutionPolicy Bypass -File .\setup_windows.ps1
```

脚本加载 x64 MSVC 14.38 工具集，安装 cu128 版 PyTorch 和 Python 依赖，编译 `simple-knn`、`diff-gaussian-rasterization` 和 `fused-ssim`，并检查安装结果。若要指定某个环境，可用 `-Python` 传入 `python.exe` 的完整路径。

如果克隆中断，在仓库根目录运行以下命令。Git 会检出项目记录的各子模块版本。

```powershell
git submodule update --init --recursive
git submodule status --recursive
```

| 源码 | 提交 |
| --- | --- |
| GraphDeco 基线 | `54c035f7834b564019656c3e3fcc3646292f727d` |
| simple-knn | `86710c2d4b46680c02301765dd79e465819c8f19` |
| diff-gaussian-rasterization | `9c5c2028f6fbee2be239bc4c9421ff894fe4fbe0` |
| fused-ssim | `1272e21a282342e89537159e4bad508b19b34157` |
| GLM | `5c46b9c07008ae65cb81ab79cd677ecc1934b903` |
| SIBR_viewers | `d8856f60c5384cc1975439193bb627d77d917d77` |

### 3. 验证安装

在已激活的环境中运行以下检查。GPU 脚本验证 KNN、fused SSIM、启用和关闭抗锯齿时的光栅化前向与反向计算，以及训练模块导入。预期输出 `ALL GPU CHECKS PASSED` 和 `No broken requirements found.`

```powershell
python .\scripts\verify_gpu.py
python -m pip check
```

### 4. 安装外部工具

COLMAP 用于原始图片预处理，FFmpeg 供视频脚本抽帧，ImageMagick 供 `convert.py --resize` 使用，SIBR 提供两种查看器。请保留各工具配套的 DLL 和插件。脚本可从 `external/` 或 `PATH` 查找可执行文件。本项目验证使用的是 COLMAP 3.8 Windows CUDA 版。

```text
external/
├─ COLMAP-3.8-windows-cuda/
│  ├─ bin/colmap.exe
│  └─ lib/
├─ ffmpeg/bin/ffmpeg.exe
├─ ImageMagick-7.1.1-Q16-HDRI/magick.exe
└─ viewers/bin/
   ├─ SIBR_remoteGaussian_app.exe
   └─ SIBR_gaussianViewer_app.exe
```

[COLMAP 3.8 CUDA](https://github.com/colmap/colmap/releases/tag/3.8) · [FFmpeg](https://ffmpeg.org/download.html#build-windows) · [ImageMagick](https://imagemagick.org/script/download.php#windows) · [SIBR](https://github.com/graphdeco-inria/gaussian-splatting#interactive-viewers)

### 手动配置和编译扩展

手动新建环境时，执行下列命令即可完成与 YAML 安装对应的准备工作。若已有 Conda 环境，从加载编译器的命令开始。

```powershell
conda create -n gaussian-splatting python=3.10 pip -y
conda activate gaussian-splatting
python -m pip install torch==2.7.1 torchvision==0.22.1 --index-url https://download.pytorch.org/whl/cu128
python -m pip install -r .\requirements.windows.txt
```

在已激活环境的 PowerShell 中加载 MSVC 14.38 并设置编译变量。`cl` 应显示 x64 的 19.38.x。如使用自定义 Toolkit 安装目录，在此调整 `CUDA_HOME`。`TORCH_CUDA_ARCH_LIST=12.0` 对应已验证的 RTX 5060 Laptop GPU，`MAX_JOBS=2` 用于限制编译并行数。

```powershell
$VsWhere = Join-Path ${env:ProgramFiles(x86)} 'Microsoft Visual Studio\Installer\vswhere.exe'
$VsPath = & $VsWhere -version '[17.0,18.0)' -products '*' -requires Microsoft.VisualStudio.Component.VC.14.38.17.8.x86.x64 -property installationPath | Select-Object -First 1
if (-not $VsPath) { throw 'Install VS 2022 and MSVC 14.38 x64/x86.' }
Import-Module (Join-Path $VsPath 'Common7\Tools\Microsoft.VisualStudio.DevShell.dll')
Enter-VsDevShell -VsInstallPath $VsPath -SkipAutomaticLocation -DevCmdArguments '-arch=x64 -host_arch=x64 -vcvars_ver=14.38'
cl

$env:CUDA_HOME = Join-Path $env:ProgramFiles 'NVIDIA GPU Computing Toolkit\CUDA\v12.8'
$env:CUDA_PATH = $env:CUDA_HOME
$env:Path = "$env:CUDA_HOME\bin;$env:Path"
$env:PYTHONUTF8 = '1'
$env:TORCH_CUDA_ARCH_LIST = '12.0'
$env:DISTUTILS_USE_SDK = '1'
$env:MAX_JOBS = '2'
$env:VSLANG = '1033'
```

逐条安装。`--no-build-isolation` 让扩展编译使用当前环境中的 PyTorch。三个扩展安装完毕后，重新运行 GPU 和依赖检查。

```powershell
python -m pip install --no-deps --no-build-isolation --no-cache-dir -v .\submodules\simple-knn
python -m pip install --no-deps --no-build-isolation --no-cache-dir -v .\submodules\diff-gaussian-rasterization
python -m pip install --no-deps --no-build-isolation --no-cache-dir -v .\submodules\fused-ssim
```

## 训练与辅助工具

激活 Conda 环境后，在仓库根目录运行以下示例。训练命令中的 `-s` 指向场景目录，`-m` 指向模型输出目录。默认训练 30,000 轮后，在模型目录下的 `point_cloud/iteration_30000/point_cloud.ply` 保存训练好的高斯模型。

### 从图片或视频训练

从照片训练时，将原始图片放入 `data/my_scene/input/`。从视频训练时，将视频放在 `data/my_video.mp4`，或通过 `--video` 指定路径。示例每秒抽取两帧。两个脚本都会将 `--iterations`、`--eval`、`-r` 等额外参数传给 `train.py`。

```powershell
python .\train_images.py -s .\data\my_scene -m .\output\my_scene
python .\train_video.py --video .\data\my_video.mp4 -s .\data\video_scene -m .\output\video_scene --fps 2
```

- 用 `--skip_extraction` 复用已抽取的帧。若相同帧已完成 COLMAP 重建，再加 `--skip_conversion`。对于 `train_images.py`，可单独用 `--skip_conversion` 复用已完成的 COLMAP 场景。
- 更换视频或抽帧频率时使用新的场景目录。视频脚本在抽帧前会检查已有的帧和重建结果。
- `--no_gpu` 让 COLMAP 特征提取和匹配使用 CPU，训练仍使用 CUDA。对于 8 GB 显存，`-r 2 --data_device cpu` 可将输入宽高减半，并把图像缓存放在系统内存中。

### 单独运行 COLMAP

将原始图片放入场景的 `input/` 目录。转换脚本会将去畸变后的图片写入 `images/`，相机和稀疏点云模型写入 `sparse/0/`。加上 `--resize` 时，ImageMagick 还会生成 `images_2/`、`images_4/` 和 `images_8/`。`--colmap_executable` 和 `--magick_executable` 可指定自定义的可执行文件路径。

```powershell
python .\convert.py -s .\data\my_scene
```

### 训练、渲染和评估

已有 COLMAP 场景时，在训练时加上 `--eval` 留出测试视角。之后渲染测试视角并计算 PSNR、SSIM 和 LPIPS。首次运行 LPIPS 需要下载 VGG16 和 LPIPS 权重。模型目录中的 `results.json` 记录场景平均指标，`per_view.json` 记录逐视角指标。

```powershell
python .\train.py -s .\data\my_scene -m .\output\my_scene_eval --eval
python .\render.py -m .\output\my_scene_eval --skip_train
python .\metrics.py -m .\output\my_scene_eval
```

### 从视频一键运行到评估

编辑 `video_train_eval.py` 顶部的常量。用 `VIDEO_PATH` 和 `FPS` 设置输入，用 `DATA_DIR` 存放抽帧和 COLMAP 文件，用 `MODEL_DIR` 存放模型、渲染图和指标。用 `TRAIN_ITERATIONS`、`DATA_DEVICE`、`IMAGE_RESOLUTION` 设置训练参数。图片默认缓存在 CPU 内存中。脚本中的相对路径以仓库根目录为基准。

首次运行时保持 `SKIP_EXTRACTION` 和 `SKIP_COLMAP` 为 `False`。用 `SKIP_EXTRACTION=True` 复用抽帧结果，再用 `SKIP_COLMAP=True` 复用这些帧的重建结果。流程依次运行 FFmpeg、COLMAP、带 `--eval` 的训练、测试视角渲染和三项指标计算。

```powershell
python .\video_train_eval.py
```

### 查看已保存模型或实时训练

安装 SIBR 后，将包含 `point_cloud/` 的模型目录传给 `SIBR_viewer.py`。要实时查看训练，启动训练时启用查看器，然后另开一个 PowerShell，将同一场景传给 `SIBR_remote_viewer.py`。默认地址是 `127.0.0.1:6009`。更改时请在训练端和查看端使用一致的 `--ip` 与 `--port`。使用旧版 Windows 查看器时，请将场景放在项目下的 ASCII 路径中。

```powershell
python .\SIBR_viewer.py -m .\output\my_scene_eval
python .\SIBR_remote_viewer.py -s .\data\my_scene
```

### 调整输入图片大小

`resize_images.py` 会保持宽高比，并将结果写入另一个目录。可用 `--height` 限制高度，或用 `--skip 2` 按文件名排序每隔一张取一张。对缩放后的图片集重新运行 COLMAP。

```powershell
python .\resize_images.py -s .\data\my_scene\input -o .\data\my_scene_small\input --width 1280
```

### 导出普通 RGB PLY 点云

`export_point_cloud.py` 将训练好的高斯 PLY 转为普通 XYZ/RGB 点云，使用零阶球谐系数近似颜色。输出只包含点中心和颜色，可供点云软件使用。加上 `--ascii` 可输出文本 PLY。

```powershell
python .\export_point_cloud.py -i .\output\my_scene_eval\point_cloud\iteration_30000\point_cloud.ply -o .\output\my_scene_eval\point_cloud_rgb.ply
```

## 常见问题

| 现象 | 排查方式 |
| --- | --- |
| 找不到 `nvcc` | 重新打开 PowerShell，或直接检查 Toolkit 的 `bin\nvcc.exe`，确认显示 12.8。 |
| `sm_120 is not compatible` | 核对当前 Python 解释器与 `torch.__version__`，已验证的 PyTorch 版本显示 `2.7.1+cu128`。 |
| 找不到 `cl` 或版本不符 | 按手动编译命令加载 MSVC 14.38，确认显示 x64 和 `19.38.x`。 |
| Ninja 找不到含非 ASCII 字符路径下的源码，或出现 `UnicodeDecodeError` | 设置 `PYTHONUTF8=1`，重编译前移除对应扩展生成的 `build/temp.win-amd64-cpython-310/Release/build.ninja`。安装脚本会清理各扩展的这个文件。 |
| 子模块下载中断 | 用 `git config --show-origin --get-regexp 'http.*proxy'` 核对 Git 网络和代理设置，再重新运行递归子模块更新。 |
| COLMAP 提示 `unable to open database file` | 运行本仓库的 `convert.py`，它会给 COLMAP 3.8 传入相对场景路径。确认场景目录可写。 |
| `Could not recognize scene type!` | 对于 COLMAP 场景，确认 `-s` 指向包含 `images/` 和 `sparse/0/` 的目录。 |
| 图像缓存占用过多显存 | 使用 `--data_device cpu`，或使用 `-r 2` 降低输入分辨率。 |
| SIBR 断线或显示乱码场景路径 | 用本仓库的 `train.py` 重启训练，并用远程启动器传入 ASCII 相对场景路径。 |
| 首次 LPIPS 评估下载权重失败 | 检查网络和 PyTorch Hub 缓存中的 VGG16 与 LPIPS 权重文件。Windows 上默认缓存目录为 `%USERPROFILE%\.cache\torch\hub\checkpoints`。 |

## 验证记录

已验证 CUDA 扩展、从视频到短轮训练的流程，以及留出测试图片的评估。还使用一个包含 1,407,622 个高斯点、约 333 MiB 的模型对比分块保存和原 PLY 写入实现，两者输出逐字节一致。

## 作者与许可证

参考实现由 Bernhard Kerbl、Georgios Kopanas、Thomas Leimkühler 和 George Drettakis 提供。在研究中使用 3D Gaussian Splatting 时，请引用其发表于 2023 年 ACM Transactions on Graphics 的论文。 [论文与引用信息](https://repo-sam.inria.fr/fungraph/3d-gaussian-splatting/) · [GraphDeco 源码](https://github.com/graphdeco-inria/gaussian-splatting)

GraphDeco 许可证将使用范围限定为非商业研究与评估。依赖各自附有许可证。 [Gaussian Splatting 许可证](LICENSE.md) · [LPIPS 许可证](lpipsPyTorch/LICENSE)
