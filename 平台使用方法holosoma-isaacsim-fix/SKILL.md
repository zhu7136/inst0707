# Holosoma IsaacSim 5.1 修复 Skill

## 问题描述

在 IsaacSim 5.1 环境中运行 Holosoma 训练任务时，会遇到以下错误：

```
ModuleNotFoundError: No module named 'torch._vendor.packaging._structures'
```

这是因为 IsaacSim 5.1 内置的 PyTorch 使用了 vendored packaging，但该 packaging 模块不完整，缺少 `_structures.py` 文件。

## 错误原因分析

1. **IsaacSim 5.1 的 torch 使用 vendored packaging**：IsaacSim 5.1 将 PyTorch 打包在 `_isaac_sim/exts/omni.isaac.ml_archive/pip_prebundle/torch/` 目录下
2. **vendored packaging 缺少 `_structures.py`**：`torch._vendor.packaging.version` 需要从 `_structures` 导入 `Infinity`, `InfinityType`, `NegativeInfinity`, `NegativeInfinityType`
3. **文件系统只读**：IsaacSim 的文件系统可能是只读的或有特殊权限限制，无法直接创建或修改文件

## 修复方案

### 方案 1：通过 `sys.modules` 注入模块（推荐）

在 `run_train.py` 中，在导入 torch 之前，通过 `sys.modules` 注入缺失的模块：

```python
import types
import sys

def fix_isaacsim_torch_vendored_packaging():
    """Fix IsaacSim's torch vendored packaging missing _structures.py."""
    
    # Create the _structures module with required classes
    class InfinityType:
        """Infinity type for packaging version."""
        def __repr__(self):
            return "Infinity"
        def __hash__(self):
            return hash("Infinity")
        def __lt__(self, other):
            return False
        def __le__(self, other):
            return isinstance(other, InfinityType)
        def __gt__(self, other):
            return not isinstance(other, InfinityType)
        def __ge__(self, other):
            return True
        def __eq__(self, other):
            return isinstance(other, InfinityType)
        def __ne__(self, other):
            return not isinstance(other, InfinityType)
    
    class NegativeInfinityType:
        """Negative infinity type for packaging version."""
        def __repr__(self):
            return "-Infinity"
        def __hash__(self):
            return hash("-Infinity")
        def __lt__(self, other):
            return True
        def __le__(self, other):
            return True
        def __gt__(self, other):
            return False
        def __ge__(self, other):
            return not isinstance(other, NegativeInfinityType)
        def __eq__(self, other):
            return isinstance(other, NegativeInfinityType)
        def __ne__(self, other):
            return not isinstance(other, NegativeInfinityType)
    
    # Create the module
    structures_module = types.ModuleType("torch._vendor.packaging._structures")
    structures_module.InfinityType = InfinityType
    structures_module.NegativeInfinityType = NegativeInfinityType
    structures_module.Infinity = InfinityType()
    structures_module.NegativeInfinity = NegativeInfinityType()
    
    # Register the module in sys.modules
    sys.modules["torch._vendor.packaging._structures"] = structures_module
    print("[run_train.py] Injected torch._vendor.packaging._structures module")

# 在导入 torch 之前调用
fix_isaacsim_torch_vendored_packaging()
```

### 方案 2：禁用 Torch Inductor（可选）

IsaacSim 5.1 的 torch inductor 编译器可能导致额外问题，建议在代码中禁用：

```python
import os

# Disable torch inductor to avoid compilation issues
os.environ["TORCH_COMPILE_DISABLE"] = "1"
os.environ["TORCHDYNAMO_DISABLE"] = "1"
```

### 方案 3：修改 `pyproject.toml` 依赖

在 `src/holosoma/pyproject.toml` 中指定 packaging 版本：

```toml
dependencies = [
    "packaging>=21.3,<24",  # pin for IsaacSim torch compatibility
    # ... 其他依赖
]
```

## 完整的 run_train.py 修复示例

```python
"""Training entry point for Gradmotion platform.

Usage: gm-run hshud3838840-public/run_train.py <training args...>
"""

import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent
HOLOSOMA_SRC = REPO_ROOT / "src" / "holosoma"


def fix_isaacsim_torch_vendored_packaging():
    """Fix IsaacSim's torch vendored packaging missing _structures.py."""
    import types
    
    class InfinityType:
        """Infinity type for packaging version."""
        def __repr__(self):
            return "Infinity"
        def __hash__(self):
            return hash("Infinity")
        def __lt__(self, other):
            return False
        def __le__(self, other):
            return isinstance(other, InfinityType)
        def __gt__(self, other):
            return not isinstance(other, InfinityType)
        def __ge__(self, other):
            return True
        def __eq__(self, other):
            return isinstance(other, InfinityType)
        def __ne__(self, other):
            return not isinstance(other, InfinityType)
    
    class NegativeInfinityType:
        """Negative infinity type for packaging version."""
        def __repr__(self):
            return "-Infinity"
        def __hash__(self):
            return hash("-Infinity")
        def __lt__(self, other):
            return True
        def __le__(self, other):
            return True
        def __gt__(self, other):
            return False
        def __ge__(self, other):
            return not isinstance(other, NegativeInfinityType)
        def __eq__(self, other):
            return isinstance(other, NegativeInfinityType)
        def __ne__(self, other):
            return not isinstance(other, NegativeInfinityType)
    
    structures_module = types.ModuleType("torch._vendor.packaging._structures")
    structures_module.InfinityType = InfinityType
    structures_module.NegativeInfinityType = NegativeInfinityType
    structures_module.Infinity = InfinityType()
    structures_module.NegativeInfinity = NegativeInfinityType()
    
    sys.modules["torch._vendor.packaging._structures"] = structures_module
    print("[run_train.py] Injected torch._vendor.packaging._structures module")


def ensure_holosoma():
    """Install holosoma and all its dependencies."""
    print(f"[run_train.py] Installing holosoma from {HOLOSOMA_SRC} ...")
    cmd = [sys.executable, "-m", "pip", "install", str(HOLOSOMA_SRC)]
    pip_mirror = "https://pypi.tuna.tsinghua.edu.cn/simple"
    cmd.extend(["-i", pip_mirror])
    subprocess.check_call(
        cmd,
        stdout=sys.stdout,
        stderr=sys.stderr,
    )


if __name__ == "__main__":
    print(f"[run_train.py] Python: {sys.executable}")
    
    # Disable torch inductor to avoid compilation issues
    os.environ["TORCH_COMPILE_DISABLE"] = "1"
    os.environ["TORCHDYNAMO_DISABLE"] = "1"
    print("[run_train.py] Disabled torch inductor compilation")
    
    ensure_holosoma()
    
    # Fix IsaacSim torch vendored packaging before importing torch
    fix_isaacsim_torch_vendored_packaging()

    from holosoma.train_agent import main
    main()
```

## 失败的方案（不推荐）

### 方案 A：尝试复制系统 packaging 的 `_structures.py`

```python
import shutil
shutil.copy2(source_structures, structures_file)
```

**失败原因**：IsaacSim 的文件系统可能是只读的，即使创建目录成功也无法写入文件。

### 方案 B：使用 `--force-reinstall` 或 `--ignore-installed` 安装 packaging

```bash
pip install packaging<24 --force-reinstall
pip install packaging<24 --ignore-installed
```

**失败原因**：这会破坏 pip 自身的依赖，导致 `ModuleNotFoundError: No module named 'pip._vendor.packaging._structures'`。

## 测试验证

修复后，训练任务应该能够正常启动并运行：

```bash
# 创建任务
flux task create --file ./create-train.json

# 启动任务
flux task run --task-id "TASK_xxx"

# 查看日志
flux task logs --task-id "TASK_xxx" --follow
```

成功的日志应该包含：
```
[run_train.py] Injected torch._vendor.packaging._structures module
[run_train.py] Disabled torch inductor compilation
```

然后训练应该正常进行，显示训练进度和奖励指标。

## 相关文件

- `run_train.py` - 训练入口脚本
- `src/holosoma/pyproject.toml` - 项目依赖配置
- `.codex/skills/holosoma-isaacsim-fix/SKILL.md` - 本 skill 文件

## 参考链接

- IsaacSim 5.1 镜像：`BJX00000170` (IsaacSim:5.1 | IsaacLab:2.3.1)
- IsaacSim 5.1 镜像：`BJX00000178` (IsaacSim:5.1 | IsaacLab:2.3.2)
- Isaac GYM 镜像：`BJX00000001` (Isaac GYM:preview-4)
