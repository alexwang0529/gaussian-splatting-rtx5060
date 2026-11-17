# 3D Gaussian Splatting · Windows / RTX 5060 Laptop

**English** · [简体中文](README-CN.md)

This project runs GraphDeco's 3D Gaussian Splatting training and rendering code on Windows with an RTX 5060 Laptop GPU. It documents the compiler and CUDA setup and adds scripts for preparing scenes, training, evaluation, viewing, and point-cloud export. Bring your own images or video and install the external tools listed below.

## Changes from GraphDeco

The comparison is against the pinned GraphDeco baseline, `54c035f`. [Upstream README](https://github.com/graphdeco-inria/gaussian-splatting/blob/54c035f7834b564019656c3e3fcc3646292f727d/README.md)

| Files | What changed and why |
| --- | --- |
| [`environment.windows-cu128.yml`](environment.windows-cu128.yml), [`requirements.windows.txt`](requirements.windows.txt), [`setup_windows.ps1`](setup_windows.ps1), [`scripts/verify_gpu.py`](scripts/verify_gpu.py) | The upstream environment pins Python 3.7.13 and PyTorch 1.12.1 with CUDA 11.6. This project uses Python 3.10 and PyTorch 2.7.1/cu128, loads MSVC 14.38, compiles for `sm_120`, and checks the CUDA extensions on the GPU. |
| [`train_images.py`](train_images.py), [`train_video.py`](train_video.py), [`video_train_eval.py`](video_train_eval.py) | Adds entry points for image training, video training, and video-to-evaluation. They use the current Python interpreter and stop if a subprocess fails. |
| [`convert.py`](convert.py), [`utils/local_tools.py`](utils/local_tools.py) | Resolves local tools or executables on `PATH`. COLMAP runs from the scene directory with relative database and image paths, which helps COLMAP 3.8 on Windows paths containing Chinese characters. |
| [`SIBR_viewer.py`](SIBR_viewer.py), [`SIBR_remote_viewer.py`](SIBR_remote_viewer.py), [`gaussian_renderer/network_gui.py`](gaussian_renderer/network_gui.py), [`train.py`](train.py) | Adds local and live viewer launchers. The training server reads complete TCP messages, sends UTF-8 paths with byte lengths, and reports disconnect errors. The remote launcher can supply an ASCII relative scene path to the legacy viewer. |
| [`scene/gaussian_model.py`](scene/gaussian_model.py) | Writes PLY in chunks of 65,536 Gaussians to reduce peak host-memory use. The completed temporary file replaces the destination after the write succeeds. |
| [`metrics.py`](metrics.py) | Reuses a single VGG LPIPS network, runs without gradients, and returns a nonzero exit status when evaluation fails. It uses the upstream PSNR, SSIM, and LPIPS definitions. |
| [`resize_images.py`](resize_images.py), [`export_point_cloud.py`](export_point_cloud.py) | Adds aspect-ratio-preserving resize and image sampling, plus export of Gaussian centers and approximate RGB colors to a standard PLY cloud. |

## Windows setup

### 1. Install the prerequisites

The following configuration was tested on Windows. Use Git for Windows with submodule support and a Conda installation available in PowerShell. If needed, run `conda init powershell` and reopen the terminal.

| Component | Tested configuration |
| --- | --- |
| Machine / GPU | Lenovo Legion R7000P ADR10 (83LT), NVIDIA GeForce RTX 5060 Laptop GPU (8 GB, `sm_120`) |
| NVIDIA driver | 592.01 |
| Python | 3.10.22 (Conda) |
| PyTorch / torchvision | 2.7.1+cu128 / 0.22.1+cu128 |
| CUDA Toolkit | 12.8 Update 1 (`nvcc V12.8.93`) |
| Windows compiler | Visual Studio 2022 / MSVC 14.38.33130 (`cl 19.38.x`) |
| NumPy / OpenCV | 1.26.4 / 4.11.0.86 |

1. In Visual Studio Installer, select **Desktop development with C++** for Visual Studio 2022 or Build Tools 2022. In **Individual components**, include **MSVC v143 x64/x86 build tools (v14.38–17.8)** and a Windows 10 or 11 SDK.
2. Install CUDA Toolkit 12.8 Update 1 for Windows x86-64. The setup script expects the default path under `C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.8`.
3. Open PowerShell and run `nvidia-smi` and `nvcc --version`. The former reports the driver's CUDA support. Use `nvcc` to check the installed Toolkit for compilation.

[Visual Studio](https://visualstudio.microsoft.com/vs/older-downloads/) · [MSVC / CUDA 12.8](https://docs.nvidia.com/cuda/archive/12.8.1/cuda-installation-guide-microsoft-windows/index.html#system-requirements) · [CUDA Toolkit 12.8.1](https://developer.nvidia.com/cuda-12-8-1-download-archive) · [Miniconda](https://www.anaconda.com/docs/getting-started/miniconda/main) · [PyTorch 2.7.1](https://pytorch.org/get-started/previous-versions/#v271)

### 2. Clone, create the environment, and build the extensions

Run these commands in PowerShell. If the `gaussian-splatting` environment already exists, activate it and continue with the setup script.

```powershell
git clone --recurse-submodules https://github.com/alexwang0529/gaussian-splatting-rtx5060.git
Set-Location .\gaussian-splatting-rtx5060
conda env create -f .\environment.windows-cu128.yml
conda activate gaussian-splatting
powershell -ExecutionPolicy Bypass -File .\setup_windows.ps1
```

The script loads the x64 MSVC 14.38 toolset, installs the cu128 wheels and Python dependencies, builds `simple-knn`, `diff-gaussian-rasterization`, and `fused-ssim`, and checks the installation. Pass `-Python` followed by the full path to `python.exe` if you want to select a specific environment.

If cloning was interrupted, run the following in the repository root. Git checks out the revisions recorded by the project.

```powershell
git submodule update --init --recursive
git submodule status --recursive
```

| Source | Commit |
| --- | --- |
| GraphDeco baseline | `54c035f7834b564019656c3e3fcc3646292f727d` |
| simple-knn | `86710c2d4b46680c02301765dd79e465819c8f19` |
| diff-gaussian-rasterization | `9c5c2028f6fbee2be239bc4c9421ff894fe4fbe0` |
| fused-ssim | `1272e21a282342e89537159e4bad508b19b34157` |
| GLM | `5c46b9c07008ae65cb81ab79cd677ecc1934b903` |
| SIBR_viewers | `d8856f60c5384cc1975439193bb627d77d917d77` |

### 3. Verify the installation

Run these checks from the activated environment. The GPU script tests KNN, fused SSIM, rasterizer forward and backward passes with and without antialiasing, and the training import. Look for `ALL GPU CHECKS PASSED` and `No broken requirements found.`

```powershell
python .\scripts\verify_gpu.py
python -m pip check
```

### 4. Install external tools

COLMAP is required to preprocess raw images, FFmpeg is used by the video scripts, ImageMagick is used by `convert.py --resize`, and SIBR provides the two viewers. Keep each package's DLLs and plugins with its executable. The scripts look under `external/` and can also resolve executables on `PATH`. This project was tested with the COLMAP 3.8 Windows CUDA distribution.

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

### Manual setup and extension build

For a manual build in a new environment, execute the commands below instead of creating the same environment from YAML. If the Conda environment is already set up, start from the compiler commands.

```powershell
conda create -n gaussian-splatting python=3.10 pip -y
conda activate gaussian-splatting
python -m pip install torch==2.7.1 torchvision==0.22.1 --index-url https://download.pytorch.org/whl/cu128
python -m pip install -r .\requirements.windows.txt
```

In the activated PowerShell, load MSVC 14.38 and set the build variables. `cl` should identify itself as 19.38.x for x64. Adjust `CUDA_HOME` here if you installed the Toolkit at a custom path. `TORCH_CUDA_ARCH_LIST=12.0` targets the tested RTX 5060 Laptop GPU, and `MAX_JOBS=2` limits build parallelism.

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

Run the installs one at a time. `--no-build-isolation` makes the extension builds use the PyTorch already installed in this environment. Repeat the GPU and dependency checks after all three succeed.

```powershell
python -m pip install --no-deps --no-build-isolation --no-cache-dir -v .\submodules\simple-knn
python -m pip install --no-deps --no-build-isolation --no-cache-dir -v .\submodules\diff-gaussian-rasterization
python -m pip install --no-deps --no-build-isolation --no-cache-dir -v .\submodules\fused-ssim
```

## Training and tools

Run the examples from the repository root in the activated Conda environment. In training commands, `-s` points to a scene and `-m` to a model output directory. With the default 30,000 iterations, the trained Gaussian model is saved under `point_cloud/iteration_30000/point_cloud.ply` within the model directory.

### Train from images or video

Place raw images in `data/my_scene/input/` to train from photos. For video, place the file at `data/my_video.mp4` or pass its path to `--video`. The video example extracts two frames per second. Both scripts forward additional options such as `--iterations`, `--eval`, and `-r` to `train.py`.

```powershell
python .\train_images.py -s .\data\my_scene -m .\output\my_scene
python .\train_video.py --video .\data\my_video.mp4 -s .\data\video_scene -m .\output\video_scene --fps 2
```

- Use `--skip_extraction` to reuse extracted frames. Add `--skip_conversion` when the same frames already have a COLMAP reconstruction. For `train_images.py`, `--skip_conversion` alone reuses an existing COLMAP scene.
- Use a fresh scene directory when changing video or frame rate. The video launcher checks for existing frames and reconstructions before extracting.
- `--no_gpu` runs COLMAP feature extraction and matching on the CPU. Training still uses CUDA. On an 8 GB GPU, `-r 2 --data_device cpu` halves the input width and height and stores the image cache in system memory.

### Run COLMAP on its own

Put the raw images in the scene's `input/` directory. The converter writes undistorted images to `images/` and the camera and sparse point model to `sparse/0/`. With `--resize`, ImageMagick also writes `images_2/`, `images_4/`, and `images_8/`. The `--colmap_executable` and `--magick_executable` flags accept custom executable paths.

```powershell
python .\convert.py -s .\data\my_scene
```

### Train, render, and evaluate

With an existing COLMAP scene, use `--eval` during training to hold out test views. Render those views and compute PSNR, SSIM, and LPIPS. The first LPIPS run downloads the VGG16 and LPIPS weights. Scene averages go to `results.json` and per-view scores to `per_view.json` in the model directory.

```powershell
python .\train.py -s .\data\my_scene -m .\output\my_scene_eval --eval
python .\render.py -m .\output\my_scene_eval --skip_train
python .\metrics.py -m .\output\my_scene_eval
```

### Run the video-to-evaluation pipeline

Edit the constants at the top of `video_train_eval.py`. Set `VIDEO_PATH` and `FPS` for the input, `DATA_DIR` for frames and COLMAP files, and `MODEL_DIR` for the model, renders, and scores. Set `TRAIN_ITERATIONS`, `DATA_DEVICE`, and `IMAGE_RESOLUTION` for the training run. Image caching defaults to CPU. The relative paths in this script are resolved from the repository root.

For a fresh run, keep `SKIP_EXTRACTION` and `SKIP_COLMAP` set to `False`. Set `SKIP_EXTRACTION=True` to reuse frames, and also set `SKIP_COLMAP=True` to reuse their reconstruction. The pipeline runs FFmpeg, COLMAP, training with `--eval`, test-view rendering, and all three metrics.

```powershell
python .\video_train_eval.py
```

### View saved models or live training

Once SIBR is installed, pass the trained model directory containing `point_cloud/` to `SIBR_viewer.py`. To view live training, start training with the viewer enabled and open a second PowerShell. Pass the same scene to `SIBR_remote_viewer.py`. The default address is `127.0.0.1:6009`. Supply the same `--ip` and `--port` on both sides if you change them. Use an ASCII scene directory under the project when using the legacy Windows viewer.

```powershell
python .\SIBR_viewer.py -m .\output\my_scene_eval
python .\SIBR_remote_viewer.py -s .\data\my_scene
```

### Resize input images

`resize_images.py` keeps the aspect ratio and writes to a separate folder. Use `--height` to bound the height or `--skip 2` to keep every second image in filename order. Run COLMAP again on the resized image set.

```powershell
python .\resize_images.py -s .\data\my_scene\input -o .\data\my_scene_small\input --width 1280
```

### Export a standard RGB PLY

`export_point_cloud.py` converts the trained Gaussian PLY into a standard XYZ/RGB point cloud. Colors are approximated from the zero-order spherical harmonics. The output is useful in point-cloud software and contains just the centers and colors. Add `--ascii` for text PLY.

```powershell
python .\export_point_cloud.py -i .\output\my_scene_eval\point_cloud\iteration_30000\point_cloud.ply -o .\output\my_scene_eval\point_cloud_rgb.ply
```

## Troubleshooting

| Symptom | What to check |
| --- | --- |
| `nvcc` is missing | Reopen PowerShell and check the Toolkit's `bin\nvcc.exe` directly. Confirm that it reports release 12.8. |
| `sm_120 is not compatible` | Check the active Python interpreter and `torch.__version__`. The tested wheel reports `2.7.1+cu128`. |
| `cl` is missing or the wrong version | Load MSVC 14.38 using the manual build commands and check for `19.38.x` and x64. |
| Ninja can't find a source under a non-ASCII path or reports a `UnicodeDecodeError` | Enable `PYTHONUTF8=1` and remove the affected extension's generated `build/temp.win-amd64-cpython-310/Release/build.ninja` before recompiling. The setup script clears that file for each extension. |
| The submodule download stops | Check Git connection and proxy settings with `git config --show-origin --get-regexp 'http.*proxy'`, then rerun the recursive submodule update. |
| COLMAP reports `unable to open database file` | Run this repository's `convert.py`, which passes scene-relative paths to COLMAP 3.8. Check that the scene directory is writable. |
| `Could not recognize scene type!` | For a COLMAP scene, check that `-s` points to the directory containing `images/` and `sparse/0/`. |
| Image caching consumes too much VRAM | Use `--data_device cpu` or reduce input resolution with `-r 2`. |
| SIBR disconnects or shows a garbled scene path | Restart training using this repository's `train.py` and use the remote launcher with an ASCII relative scene path. |
| The first LPIPS evaluation fails to download weights | Check the connection and the VGG16 and LPIPS files in the PyTorch Hub cache. The default Windows location is `%USERPROFILE%\.cache\torch\hub\checkpoints`. |

## Validation

The tested setup passed the CUDA extension checks, a short video-to-training run, and held-out image evaluation. The chunked writer was also compared with the original PLY writer on a 1,407,622-Gaussian model (about 333 MiB), and the resulting files were byte-identical.

## Credits and license

The reference implementation is by Bernhard Kerbl, Georgios Kopanas, Thomas Leimkühler, and George Drettakis. Cite their 2023 ACM Transactions on Graphics paper when using 3D Gaussian Splatting in research. [Paper and citation](https://repo-sam.inria.fr/fungraph/3d-gaussian-splatting/) · [GraphDeco source](https://github.com/graphdeco-inria/gaussian-splatting)

The GraphDeco license restricts use to non-commercial research and evaluation. Dependencies carry their own licenses. [Gaussian Splatting license](LICENSE.md) · [LPIPS license](lpipsPyTorch/LICENSE)
