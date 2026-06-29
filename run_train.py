"""Training entry point for InstinctLab on Gradmotion platform.

Usage: gm-run InstinctLab2/run_train.py <training args...>
"""

import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent
INSTINCTLAB_SRC = REPO_ROOT / "source" / "instinctlab"
INSTINCT_RL_SRC = REPO_ROOT / "instinct_rl-main"

PIP_MIRROR = "https://pypi.tuna.tsinghua.edu.cn/simple"


def install_package(src_path, description):
    """Install a package using pip with Tsinghua mirror."""
    print(f"[run_train.py] Installing {description} from {src_path} ...")
    cmd = [sys.executable, "-m", "pip", "install", "-e", str(src_path), "-i", PIP_MIRROR]
    subprocess.check_call(
        cmd,
        stdout=sys.stdout,
        stderr=sys.stderr,
    )


def ensure_dependencies():
    """Install all required dependencies."""
    # Disable torch inductor to avoid compilation issues
    os.environ["TORCH_COMPILE_DISABLE"] = "1"
    os.environ["TORCHDYNAMO_DISABLE"] = "1"
    print("[run_train.py] Disabled torch inductor compilation")

    # Install instinct_rl
    install_package(INSTINCT_RL_SRC, "instinct_rl")

    # Install instinctlab
    install_package(INSTINCTLAB_SRC, "instinctlab")


if __name__ == "__main__":
    print(f"[run_train.py] Python: {sys.executable}")
    print(f"[run_train.py] Working directory: {os.getcwd()}")

    ensure_dependencies()

    # Run the actual training script
    train_script = REPO_ROOT / "scripts" / "instinct_rl" / "train.py"
    if not train_script.exists():
        print(f"[run_train.py] Error: Training script not found at {train_script}")
        sys.exit(1)

    # Build the command with all remaining arguments
    cmd = [sys.executable, str(train_script)] + sys.argv[1:]
    print(f"[run_train.py] Running: {' '.join(cmd)}")

    # Execute the training script
    subprocess.check_call(cmd)