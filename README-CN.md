# Gaussian Splatting 中文配置教程 · Windows / RTX 5060 Laptop

本文介绍在 Windows 上使用 RTX 5060 Laptop 复现 3D Gaussian Splatting 的环境配置方法，并说明本仓库对上游代码增加的适配与修复。教程从环境安装一直覆盖到视频抽帧、COLMAP、训练、渲染和指标评估，命令采用 PowerShell 语法。

算法实现来自 GraphDeco-Inria。本教程依据官方 README 的流程整理，针对验证硬件补充 Python、PyTorch、CUDA 和编译器的版本组合，以及复现中实际遇到的问题。[官方项目](https://github.com/graphdeco-inria/gaussian-splatting)、[对应基线版本的官方 README](https://github.com/graphdeco-inria/gaussian-splatting/blob/54c035f7834b564019656c3e3fcc3646292f727d/README.md)。

## 验证硬件

| 项目 | 型号 |
|---|---|
| 电脑 | Lenovo Legion R7000P ADR10（83LT） |
| 显卡 | NVIDIA GeForce RTX 5060 Laptop GPU，8GB 显存，计算能力 sm_120 |

下文记录的版本组合已在这台电脑上验证。其他硬件可以参考配置步骤，显卡计算能力、工具安装位置和训练显存需求应按实际设备调整。

## 与官方 README 教程的区别

比较依据为上方链接中的上游版本。官方的 `environment.yml`、作者测试过的 CUDA SDK 和可自定义环境的说明需要一起理解。

| 项目 | 官方默认配置或教程流程 | 本教程采用的方法 |
|---|---|---|
| Python / PyTorch | 环境文件使用 Python 3.7.13、PyTorch 1.12.1 | 使用 Python 3.10、PyTorch 2.7.1/cu128，适配验证显卡 |
| CUDA | 环境文件使用 cudatoolkit 11.6，README 中作者使用的扩展编译 SDK 为 11.8 | PyTorch cu128 配合 CUDA Toolkit 12.8.1 编译扩展 |
| Windows 编译器 | 作者使用 VS 2019，要求编译器与 CUDA 配套 | VS 2022，明确加载 MSVC 14.38 x64/x86 |
| 环境创建 | `conda env create --file environment.yml` | 提供 `environment.windows-cu128.yml`、手动安装命令和 `setup_windows.ps1` |
| 数据处理与评估 | 分别运行 `convert.py`、`train.py`、`render.py`、`metrics.py` | 增加视频全流程脚本，统一数据路径并检查每一步退出状态 |
| 图片缓存 | `data_device` 默认使用 CUDA | 全流程脚本使用 CPU 缓存图片，模型继续在 GPU 上训练 |
| Windows 中文路径 | 需要结合各工具的路径和编码行为处理 | 对编译文件、COLMAP 数据库路径和 SIBR 通信分别补充修复 |
| 大模型 PLY 保存 | 保存函数先构造全部属性和 Python 元组列表 | 按每块 65536 个高斯点写入，降低保存时的内存峰值 |

官方 README 也提供自定义环境的说明。这里记录的是针对上述电脑验证过的一条配置路线，其中扩展版本仍按仓库的子模块提交配套安装。

## 解决的问题与实际优势

- **新显卡环境适配。** 原先的 PyTorch 1.12.1/cu116 出现 `sm_120 is not compatible`。本教程给出可复用的 PyTorch/cu128、Toolkit 和 MSVC 组合，并提供实际 GPU 前向、反向运算检查。
- **更容易完成 Windows 扩展编译。** 通过 PowerShell 明确选择工具集、目标架构和 UTF-8 编码，覆盖找不到 `cl`、选错编译器和中文路径下 Ninja 缓存编码等问题。
- **更适合 8GB 显存下处理较多图片。** 图片缓存放入系统内存，减少输入数据常驻显存的占用。训练规模仍与图片分辨率、高斯点数量和渲染过程有关。
- **减少重复操作与错误路径。** 全流程脚本集中设置视频、FPS、数据目录和模型目录。COLMAP 或训练失败时立即停止，方便修复后复用已完成的步骤。
- **降低导出大模型时的额外内存开销。** 分块保存替代全量元组列表，已用 1407622 个点、约 333MiB 的模型验证输出逐字节一致。保存完成后再替换目标文件，减少中途写入失败损坏已有模型的风险。
- **便于定位查看与评估问题。** 补充 SIBR 中文路径启动方式，评估脚本输出具体异常并复用 LPIPS 网络，便于识别权重下载和运行错误。

以上改动集中在环境、文件读写、工具调用和流程衔接。训练优化目标与评价指标定义沿用上游实现。GPU 算子检查、独立视频短流程、测试图片指标计算和大模型保存一致性均已有验证记录。

## 配置教程

先确认以下软件版本组合。记录核对于 2026 年 11 月 16 日。

| 组件 | 验证版本 |
|---|---|
| NVIDIA 驱动 | 592.01 |
| Python | 3.10.22，Conda 环境 |
| PyTorch | 2.7.1+cu128 |
| torchvision | 0.22.1+cu128 |
| CUDA Toolkit | 12.8 Update 1，nvcc V12.8.93 |
| Visual Studio | VS 2022，验证时使用 Professional |
| MSVC 工具集 | 14.38.33130，对应 cl 19.38.x |
| NumPy | 1.26.4 |
| OpenCV | opencv-python 4.11.0.86 |
| 官方代码基线 | `54c035f7834b564019656c3e3fcc3646292f727d` |

本仓库为这组配置提供 `environment.windows-cu128.yml`。后面的步骤同时给出手动配置方式，方便定位安装问题。

完成第 1～4 步后，可以直接运行 `powershell -ExecutionPolicy Bypass -File .\setup_windows.ps1` 安装并检查 CUDA 扩展，再继续第 8 步。需要手动编译或定位问题时，按第 5～7 步操作。自动配置脚本的 PowerShell 语法已检查，编译过程已通过手动等效命令验证。

### 1. 准备 Visual Studio 2022 编译工具

安装 Visual Studio 2022 或 Build Tools 2022。在 Visual Studio Installer 中选择“使用 C++ 的桌面开发”，并在“单个组件”中安装以下组件。

- `MSVC v143 - VS 2022 C++ x64/x86 生成工具 (v14.38–17.8)`。
- 一个 Windows 10 或 Windows 11 SDK。

`14.38` 是编译工具集版本，`17.8` 表示该工具集对应的 VS 2022 版本。整套 VS 可以更新到 17.14，同时保留 14.38 工具集。CUDA 12.8 的官方支持表列出了 VS 2022/MSVC 193x。[VS 历史版本入口](https://visualstudio.microsoft.com/vs/older-downloads/)、[CUDA Windows 编译器兼容表](https://docs.nvidia.com/cuda/archive/12.8.1/cuda-installation-guide-microsoft-windows/index.html#system-requirements)。

当电脑安装了多套 VS/MSVC 时，后面的命令会明确选择 14.38 工具集。

### 2. 安装 CUDA Toolkit 12.8.1

先完成 VS 组件安装，再运行 CUDA 安装程序。下载页选择 Windows、x86_64、对应的 Windows 版本和 `exe (local)`。[CUDA Toolkit 12.8.1 官方下载](https://developer.nvidia.com/cuda-12-8-1-download-archive)。

验证时采用“自定义安装”，安装 CUDA 工具包组件。电脑已有合适的新版驱动时，可取消勾选 `Driver components`。遇到正在运行的 Visual Studio 提示时，保存工作并关闭 VS，再点击 Retry。

默认工具包目录如下。

```text
C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.8
```

安装完成后新开 PowerShell，检查驱动和编译器。

```powershell
nvidia-smi
nvcc --version
```

`nvcc` 应显示 `release 12.8`。如果终端还没有刷新 PATH，可直接验证安装文件。

```powershell
& 'C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.8\bin\nvcc.exe' --version
```

`nvidia-smi` 中的 CUDA Version 表示驱动支持的 CUDA 版本上限。编译此项目所用的 Toolkit 版本由 `nvcc --version` 确认。

### 3. 下载完整项目及子模块

首次下载时，在希望存放项目的父目录打开 PowerShell。复制当前 GitHub 仓库页面 Code 菜单中的 HTTPS 地址，在提示时粘贴。

```powershell
$RepositoryUrl = Read-Host '粘贴当前仓库的 HTTPS 克隆地址'
git clone --recursive $RepositoryUrl gaussian-splatting
Set-Location .\gaussian-splatting
```

后续命令均在项目根目录执行。本文使用本仓库提供的 Windows 配置文件、辅助脚本和修复。

验证时使用的上游代码和子模块提交如下。当前仓库的适配代码建立在这些版本之上。

| 仓库 | 提交 |
|---|---|
| gaussian-splatting | `54c035f7834b564019656c3e3fcc3646292f727d` |
| simple-knn | `86710c2d4b46680c02301765dd79e465819c8f19` |
| diff-gaussian-rasterization | `9c5c2028f6fbee2be239bc4c9421ff894fe4fbe0` |
| fused-ssim | `1272e21a282342e89537159e4bad508b19b34157` |
| GLM | `5c46b9c07008ae65cb81ab79cd677ecc1934b903` |
| SIBR_viewers | `d8856f60c5384cc1975439193bb627d77d917d77` |

下载中断后，在项目根目录补齐子模块，并检查检出状态。

```powershell
git submodule update --init --recursive
git submodule status --recursive
```

主仓库 ZIP 需要额外补齐各个子模块。递归克隆能够按主仓库记录的提交检出依赖。[官方仓库](https://github.com/graphdeco-inria/gaussian-splatting)。

如果 Git 报本地代理连接失败，先核对 Git 配置与代理软件实际监听端口。

```powershell
git config --show-origin --get-regexp 'http.*proxy'
```

例如代理软件确实监听 7890 时，可以对单次克隆指定代理。该示例中的端口需按自己的代理配置修改，`$RepositoryUrl` 使用前面复制的当前仓库地址。

```powershell
git -c http.proxy=http://127.0.0.1:7890 -c https.proxy=http://127.0.0.1:7890 clone --recursive $RepositoryUrl gaussian-splatting
```

主仓库已经下载、子模块下载失败时，在项目内补下载即可。

```powershell
git -c http.proxy=http://127.0.0.1:7890 -c https.proxy=http://127.0.0.1:7890 submodule update --init --recursive --jobs 1
```

能够直连 GitHub 时，也可以对单次命令清空代理。

```powershell
git -c http.proxy= -c https.proxy= submodule update --init --recursive --jobs 1
```

### 4. 创建 Python 环境并安装 PyTorch

先安装可在 PowerShell 中使用的 Conda，例如 [Miniconda](https://www.anaconda.com/docs/getting-started/miniconda/main)。如果尚未初始化 PowerShell，执行 `conda init powershell` 后重新打开终端。

从零配置时执行以下命令，环境统一命名为 `gaussian-splatting`。

```powershell
conda create -n gaussian-splatting python=3.10 pip -y
conda activate gaussian-splatting
python -m pip install torch==2.7.1 torchvision==0.22.1 --index-url https://download.pytorch.org/whl/cu128
python -m pip install -r .\requirements.windows.txt
```

PyTorch 安装成功后，预期版本字符串为 `2.7.1+cu128`。上述 Windows/cu128 命令来自 PyTorch 官方历史版本说明。[PyTorch 2.7.1 安装说明](https://pytorch.org/get-started/previous-versions/#v271)。

`requirements.windows.txt` 包含 NumPy、OpenCV、plyfile、Pillow、SciPy、tqdm、joblib、ninja、setuptools 和 wheel。本教程固定 NumPy 1.26.4、OpenCV 4.11.0.86，以保持这组依赖的兼容性。

也可以使用仓库提供的 YAML 创建环境。

```powershell
conda env create -f .\environment.windows-cu128.yml
conda activate gaussian-splatting
```

手动创建和 YAML 创建任选一种。已有可用环境时直接激活，继续验证或编译步骤。

其他依赖的验证版本如下，供定位环境差异使用。

| 包 | 验证环境版本 |
|---|---|
| plyfile | 1.1.3 |
| SciPy | 1.15.3 |
| Pillow | 12.3.0 |
| tqdm | 4.70.1 |
| joblib | 1.6.0 |
| ninja | 1.13.2 |
| setuptools | 84.2.1 |
| wheel | 0.48.0 |

### 5. 验证 PyTorch GPU 运算

```powershell
python -c "import sys,torch; print(sys.executable); print(torch.__version__); print(torch.version.cuda); print(torch.cuda.get_device_name(0)); x=torch.randn(512,512,device='cuda'); print((x@x).mean().item()); torch.cuda.synchronize(); print('GPU OK')"
```

应输出当前环境的 Python 路径、`2.7.1+cu128`、`12.8`、RTX 5060 Laptop GPU，以及 `GPU OK`。

### 6. 加载 MSVC 14.38 并编译三个 CUDA 扩展

在已激活 `gaussian-splatting` 的同一个 PowerShell 中，通过 VS Installer 自带的 `vswhere` 查找安装目录。

```powershell
$VsWhere = Join-Path ${env:ProgramFiles(x86)} 'Microsoft Visual Studio\Installer\vswhere.exe'
$VsPath = & $VsWhere -version '[17.0,18.0)' -products '*' -requires Microsoft.VisualStudio.Component.VC.14.38.17.8.x86.x64 -property installationPath | Select-Object -First 1
if (-not $VsPath) { throw '请先安装 VS 2022 及 MSVC 14.38 x64/x86 组件' }
Import-Module (Join-Path $VsPath 'Common7\Tools\Microsoft.VisualStudio.DevShell.dll')
Enter-VsDevShell -VsInstallPath $VsPath -SkipAutomaticLocation -DevCmdArguments '-arch=x64 -host_arch=x64 -vcvars_ver=14.38'
cl
```

`cl` 应显示用于 x64 的 `19.38.x` 编译器。接着配置本终端的编译变量。

```powershell
$env:CUDA_HOME = Join-Path $env:ProgramFiles 'NVIDIA GPU Computing Toolkit\CUDA\v12.8'
$env:CUDA_PATH = $env:CUDA_HOME
$env:Path = "$env:CUDA_HOME\bin;$env:Path"
$env:PYTHONUTF8 = '1'
$env:TORCH_CUDA_ARCH_LIST = '12.0'
$env:DISTUTILS_USE_SDK = '1'
$env:MAX_JOBS = '2'
$env:VSLANG = '1033'
```

`12.0` 对应当前显卡的计算能力 `sm_120`。`PYTHONUTF8` 让 Python 以 UTF-8 生成编译文件，适配当前中文项目路径。`MAX_JOBS=2` 限制编译并行数量，降低编译时的内存压力。

逐条执行，每条成功后再执行下一条。

```powershell
python -m pip install --no-deps --no-build-isolation --no-cache-dir -v .\submodules\simple-knn
python -m pip install --no-deps --no-build-isolation --no-cache-dir -v .\submodules\diff-gaussian-rasterization
python -m pip install --no-deps --no-build-isolation --no-cache-dir -v .\submodules\fused-ssim
```

`--no-build-isolation` 让编译过程使用当前环境中已安装的 PyTorch。CUDA 扩展需要与当前 Python、PyTorch、Toolkit 和显卡架构配套。

如果之前生成过 GBK 编码的 `build.ninja`，切换 UTF-8 后读取旧缓存可能失败。可清理这三个自动生成的文件后重试编译。

```powershell
Remove-Item -LiteralPath '.\submodules\simple-knn\build\temp.win-amd64-cpython-310\Release\build.ninja' -ErrorAction SilentlyContinue
Remove-Item -LiteralPath '.\submodules\diff-gaussian-rasterization\build\temp.win-amd64-cpython-310\Release\build.ninja' -ErrorAction SilentlyContinue
Remove-Item -LiteralPath '.\submodules\fused-ssim\build\temp.win-amd64-cpython-310\Release\build.ninja' -ErrorAction SilentlyContinue
```

当前项目也提供了自动配置入口。它会定位名为 `gaussian-splatting` 的 Conda 环境、查找 VS 2022/MSVC 14.38、设置编译变量，并安装和验证扩展。

```powershell
powershell -ExecutionPolicy Bypass -File .\setup_windows.ps1
```

### 7. 验证扩展和依赖

```powershell
python .\scripts\verify_gpu.py
python -m pip check
```

验证脚本会执行 KNN GPU 距离计算、fused SSIM 的前向与反向计算、渲染器的前向与反向计算，并检查抗锯齿开关和训练模块导入。预期最后出现 `ALL GPU CHECKS PASSED`，依赖检查输出 `No broken requirements found.`。

在 VS Code 中执行 `Python: Select Interpreter`，选择 `gaussian-splatting` 环境。可以在已激活的终端查询实际解释器位置。

```powershell
python -c "import sys; print(sys.executable)"
```

日常运行激活该环境即可。重新打开终端后，如果需要重新编译扩展，再执行第 6 步的编译环境加载命令。

### 8. 准备本地外部工具

为视频抽帧、COLMAP 预处理和可选的模型查看准备外部工具。获取工具后，按以下目录放置完整的二进制包及附属库。

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

复制外部工具时需保留整个工具目录，包含 DLL、插件和资源。仓库中的 `utils/local_tools.py` 自动定位这些程序，运行 COLMAP 时设置其库目录和 Qt 插件路径。

`external/` 已被 `.gitignore` 忽略，读者克隆本仓库后需要自行准备这些外部程序。目录名与 `utils/local_tools.py` 中的路径映射对应，更换目录结构时同时调整该映射。

- COLMAP 采用已验证的 3.8 Windows CUDA 版本，保留 `bin`、`lib` 和插件目录。[COLMAP 3.8 下载](https://github.com/colmap/colmap/releases/tag/3.8)。
- FFmpeg 可从官方页面列出的 Windows 预编译包获取，放置后确认存在 `external/ffmpeg/bin/ffmpeg.exe`。[FFmpeg 下载](https://ffmpeg.org/download.html#build-windows)。
- ImageMagick 用于 `convert.py --resize`，按下载版本安装并核对 `magick.exe` 路径。[ImageMagick 下载](https://imagemagick.org/script/download.php#windows)。
- SIBR 用于交互查看，可通过上游提供的 Windows 二进制包准备。预编译程序与最新源码的功能可能有差异。[官方查看器说明](https://github.com/graphdeco-inria/gaussian-splatting#interactive-viewers)。

工具可执行文件与其 DLL、插件、资源应保持配套。另行更换 COLMAP 版本时，需要核对 `convert.py` 使用的命令行选项。

### 9. 训练、评估与模型查看

环境配置完成后，请参阅[训练、评估与工具用法](README_LOCAL.zh-CN.md)，其中包含图片与视频训练、渲染评估、交互查看和普通点云导出的可运行示例。

### 10. 常见问题与已实现的修复

| 现象 | 原因与处理 |
|---|---|
| PowerShell 无法识别 `nvcc` | 确认 Toolkit 安装完成，新开终端，或用第 2 步的完整路径验证 |
| `sm_120 is not compatible` | 核对解释器及 `torch.__version__`，使用本说明中的 Python 3.10、PyTorch 2.7.1/cu128 组合 |
| 找不到 `cl` 或选中了 19.44/更高版本 | 用第 6 步明确加载 MSVC 14.38，确认 `cl` 显示 19.38.x |
| Ninja 提示源文件不存在，但文件实际存在 | 检查中文路径的编译文件编码，设置 `PYTHONUTF8=1` 并清理旧 `build.ninja` |
| `UnicodeDecodeError` 发生在读取 `build.ninja` | 清理旧编码缓存后重新编译 |
| Git 无法连接本地代理端口 | 核对代理软件实际端口，示例使用 7890；按第 3 步对单次命令指定代理 |
| SQLite `unable to open database file` | 本地 `convert.py` 在场景目录内传递相对数据库和图片路径，避开旧 COLMAP 对中文绝对路径的兼容问题 |
| `Could not recognize scene type!` | 检查 `-s` 是否指向含 `images`、`sparse/0` 的具体场景目录 |
| `Tensorboard not available` | 当前环境没有安装 TensorBoard，训练仍可继续；如需该日志功能可安装 `tensorboard` |
| 训练后期突然变慢 | 检查显存和共享内存占用。验证中 502 张图片的实验通过 `--data_device cpu` 缓解图片缓存压力 |
| 最后保存 PLY 时 `MemoryError` | 原保存代码会构造巨大的 Python 元组列表，本地已改成每块 65536 个点写入；百万点模型的输出一致性检查已通过 |
| SIBR 连接后立即掉线 | 本地已修复训练端中文路径发送及 TCP 分包读取；修改后重启训练进程生效 |
| SIBR 显示乱码路径并无法识别数据 | 使用 `python .\SIBR_remote_viewer.py -s .\data\example`，启动器会传递相对路径 |
| LPIPS 下载 VGG16 权重时失败 | 首次评价需下载权重，检查下载网络和缓存完整性；验证过程中已补齐并校验 VGG16 权重，评估脚本会显示具体异常 |

LPIPS 下载后的权重默认缓存在当前用户目录，可以在资源管理器地址栏输入以下路径。

```text
%USERPROFILE%\.cache\torch\hub\checkpoints\
├─ vgg16-397923af.pth
└─ vgg.pth
```

保存修复已使用实际 1407622 个点、约 333MiB 的模型核对，输出与原写法逐字节一致。训练速度、峰值内存和最终指标取决于输入场景及训练参数。项目使用与分发遵循仓库中的 [LICENSE.md](LICENSE.md) 及相应依赖的许可证。
