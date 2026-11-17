"""视频抽帧 -> COLMAP 预处理 -> 训练并评估。

修改下面的配置后，可在 VS Code 直接运行，或执行 python video_train_eval.py。
相对路径均相对于本脚本所在的项目目录。
"""
import math
from pathlib import Path
import subprocess

from utils.local_tools import PROJECT_ROOT, resolve_tool, run_checked, run_python, validate_dataset


# ==================== 在这里修改 ====================
VIDEO_PATH = r"data\my_video.mp4"              # 视频路径，也可以填写绝对路径
FPS = 2.0                                 # 每秒提取多少张图片，例如 1、2、4
DATA_DIR = r"data/my_video"               # 抽帧和 COLMAP 结果统一保存在此目录
MODEL_DIR = r"output/my_video_eval"       # 模型、渲染图和评价指标保存目录
TRAIN_ITERATIONS = 30000                   # 正式训练默认 30000 轮
DATA_DEVICE = "cpu"                       # 图片缓存位置 cpu/cuda；模型始终使用 GPU 训练
IMAGE_RESOLUTION = -1                      # -1 保持官方默认；2 将图片宽高减半以降低显存占用

# 同一个视频已有中间结果时，可以跳过已完成的步骤，继续执行。
# 更换视频或 FPS 时，请同时修改 DATA_DIR 和 MODEL_DIR，建立新的实验目录。
SKIP_EXTRACTION = False                    # 已经成功抽帧时改为 True
SKIP_COLMAP = False                        # 已经成功完成 COLMAP 时改为 True
# ====================================================


def main():
    video = (PROJECT_ROOT / Path(VIDEO_PATH).expanduser()).resolve()
    source = (PROJECT_ROOT / Path(DATA_DIR).expanduser()).resolve()
    model = (PROJECT_ROOT / Path(MODEL_DIR).expanduser()).resolve()
    images = source / "input"
    if not math.isfinite(FPS) or FPS <= 0:
        raise ValueError("FPS 必须是大于 0 的有限数值")
    if not isinstance(TRAIN_ITERATIONS, int) or TRAIN_ITERATIONS <= 0:
        raise ValueError("TRAIN_ITERATIONS 必须是正整数")
    if DATA_DEVICE not in ("cpu", "cuda"):
        raise ValueError("DATA_DEVICE 只能填写 cpu 或 cuda")
    if SKIP_COLMAP and not SKIP_EXTRACTION:
        raise ValueError("复用 COLMAP 结果时，请同时将 SKIP_EXTRACTION 设为 True")
    if not SKIP_EXTRACTION:
        if not video.is_file():
            raise FileNotFoundError(f"找不到视频文件 {video}")
        if images.is_dir() and any(p.suffix.lower() in (".jpg", ".jpeg", ".png") for p in images.iterdir()):
            raise FileExistsError(
                f"{images} 已有图片。同一视频继续运行可设置 SKIP_EXTRACTION=True，"
                "新视频请修改 DATA_DIR 和 MODEL_DIR。"
            )
        if (source / "distorted/database.db").exists() or (source / "sparse/0").exists():
            raise FileExistsError("DATA_DIR 已有重建结果，请复用原图片或更换实验目录")
        ffmpeg = resolve_tool("ffmpeg")
    if not SKIP_COLMAP:
        resolve_tool("colmap")

    print(f"视频文件 {video}", flush=True)
    print(f"抽帧频率 {FPS} fps", flush=True)
    print(f"数据目录 {source}", flush=True)
    print(f"模型目录 {model}", flush=True)

    print("\n[1/3] 视频抽帧", flush=True)
    if SKIP_EXTRACTION:
        print("复用已提取的图片", flush=True)
    else:
        images.mkdir(parents=True, exist_ok=True)
        run_checked([
            ffmpeg, "-nostdin", "-n", "-i", video,
            "-vf", f"fps={FPS}", "-q:v", "1", images / "%04d.jpg",
        ])
    if not images.is_dir() or not any(p.suffix.lower() in (".jpg", ".jpeg", ".png") for p in images.iterdir()):
        raise FileNotFoundError(f"抽帧目录中没有图片 {images}")

    print("\n[2/3] COLMAP 预处理", flush=True)
    if SKIP_COLMAP:
        print("复用已完成的 COLMAP 数据", flush=True)
    else:
        run_python("convert.py", ["-s", str(source)])
    validate_dataset(source)

    print("\n[3/3] 训练并评估", flush=True)
    run_python("train.py", [
        "-s", str(source), "-m", str(model), "--eval",
        "--iterations", str(TRAIN_ITERATIONS),
        "--data_device", DATA_DEVICE, "-r", str(IMAGE_RESOLUTION),
    ])
    print("\n生成测试视角的渲染图", flush=True)
    run_python("render.py", [
        "-m", str(model), "--iteration", str(TRAIN_ITERATIONS), "--skip_train",
    ])
    print("\n计算 PSNR、SSIM、LPIPS", flush=True)
    run_python("metrics.py", ["-m", str(model)])

    print("\n训练和评估全部完成", flush=True)
    print(f"模型文件 {model / 'point_cloud' / f'iteration_{TRAIN_ITERATIONS}' / 'point_cloud.ply'}")
    print(f"平均指标 {model / 'results.json'}")
    print(f"逐图指标 {model / 'per_view.json'}")


if __name__ == "__main__":
    try:
        main()
    except subprocess.CalledProcessError as error:
        print(f"\n流程停止，子进程退出码为 {error.returncode}，请检查上方错误信息。", flush=True)
        raise SystemExit(1) from error
    except (ValueError, FileNotFoundError, FileExistsError) as error:
        print(f"\n流程停止，{error}", flush=True)
        raise SystemExit(1) from error
