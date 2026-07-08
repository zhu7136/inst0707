# Holosoma 训练平台使用指南

## 一、环境准备

### 1.1 API Key 配置

```bash
# 安装 flux-cli
npm install -g @limxdynamics/flux-cli

# 配置服务地址
flux config set base_url "https://internal.limxdynamics.com/dev-api"

# 登录
flux auth login --api-key "gm_sk_xxxxxxxxxxxxxxxx"

# 验证
flux auth status
flux auth whoami
```

### 1.2 镜像选择

| 镜像ID | 名称 | Python | PyTorch | 备注 |
|--------|------|--------|---------|------|
| BJX00000170 | IsaacSim:5.1 \| IsaacLab:2.3.1 | 3.11 | 2.7.0 | 需要修复 packaging 问题 |
| BJX00000178 | IsaacSim:5.1 \| IsaacLab:2.3.2 | 3.11 | 2.7.0 | 需要修复 packaging 问题 |
| BJX00000001 | Isaac GYM:preview-4 | 3.8 | 2.4.1 | 旧版本，不支持 IsaacSim |

### 1.3 算力资源

| 资源ID | 名称 | 价格 | 备注 |
|--------|------|------|------|
| ESKU000001 | 1×4090D×24G | 5.4元/小时 | 推荐 |
| ESKU000011 | 1×4090×24G | 2.63元/小时 | 不可挂载数据，可能繁忙 |

---

## 二、代码准备

### 2.1 GitHub 仓库配置

确保代码仓库包含以下文件：

```
run_train.py              # 训练入口脚本
src/holosoma/pyproject.toml  # 项目依赖配置
```

### 2.2 run_train.py 完整示例

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

### 2.3 pyproject.toml 依赖配置

```toml
dependencies = [
    "packaging>=21.3,<24",  # pin for IsaacSim torch compatibility
    # ... 其他依赖
]
```

---

## 三、任务创建与运行

### 3.1 创建任务 JSON

```json
{
  "taskBaseInfo": {
    "projectId": "PRO_xxx",
    "taskType": "1",
    "trainType": "1",
    "taskName": "g1-29dof-wbt-fast-sac-climb14-4096",
    "taskDescription": "G1 29DOF WBT fast SAC terrain climb 14",
    "taskTag": [],
    "goodsId": "ESKU000001",
    "imageId": "BJX00000170",
    "imageVersion": "V000212",
    "personalDataPath": ""
  },
  "taskCodeInfo": {
    "codeType": "2",
    "codeUrl": "[{\"codeUrl\":\"https://github.com/your-org/your-repo.git\",\"versionType\":\"1\",\"versionName\":\"main\"}]",
    "mainCodeUri": "",
    "hparamsPath": null,
    "startScript": "gm-run your-repo/run_train.py exp:g1-29dof-wbt-fast-sac-climb terrain:terrain-load-obj --training.num_envs=4096 --training.headless=True --terrain.terrain-term.obj-file-path=holosoma/data/motions/g1_29dof/whole_body_tracking/terrain_climb_14_50cm.obj --command.setup_terms.motion_command.params.motion_config.motion_file=holosoma/data/motions/g1_29dof/whole_body_tracking/climb_14_mj_fps50_no_obj.npz --simulator.config.scene.env_spacing=0.0",
    "isOpen": "1"
  },
  "runtimeReminderConfig": {
    "enableRuntimeReminder": false,
    "reminderDurations": []
  }
}
```

### 3.2 创建并启动任务

```bash
# 创建任务
flux task create --file ./create-train.json

# 启动任务
flux task run --task-id "TASK_xxx"

# 查看任务状态
flux task info --task-id "TASK_xxx"

# 查看日志
flux task logs --task-id "TASK_xxx" --follow
```

### 3.3 停止任务

```bash
# 停止任务（Agent 必须加 --yes）
flux --yes task stop --task-id "TASK_xxx"
```

---

## 四、常见问题与解决方案

### 4.1 packaging 版本冲突

**错误信息：**
```
ModuleNotFoundError: No module named 'torch._vendor.packaging._structures'
```

**原因：** IsaacSim 5.1 内置的 PyTorch vendored packaging 缺少 `_structures.py` 文件

**解决方案：** 在 `run_train.py` 中通过 `sys.modules` 注入模块（见第二章代码）

### 4.2 Torch Inductor 编译失败

**错误信息：**
```
torch._dynamo.exc.BackendCompilerFailed: backend='inductor' raised:
AssertionError
```

**原因：** PyTorch inductor 编译器在 IsaacSim 环境中有兼容性问题

**解决方案：** 在 `run_train.py` 中设置环境变量禁用 inductor

```python
os.environ["TORCH_COMPILE_DISABLE"] = "1"
os.environ["TORCHDYNAMO_DISABLE"] = "1"
```

### 4.3 gm-run 不支持 env 命令

**错误信息：**
```
/workspace/isaaclab/_isaac_sim/kit/python/bin/python3: can't open file '/workspace/isaaclab/env': [Errno 2] No such file or directory
```

**原因：** `gm-run` 不支持 `env VAR=value command` 语法

**解决方案：** 在 Python 代码中设置环境变量，而不是在 startScript 中

### 4.4 任务状态为 failed 无法重启

**原因：** 任务停止后状态变为 6（failed），需要修改为 0（created）才能重新运行

**解决方案：**
```bash
# 获取任务信息
flux task info --task-id "TASK_xxx"

# 修改任务状态
flux task edit --file ./edit-task.json
```

### 4.5 算力资源繁忙

**错误信息：**
```
系统算力资源繁忙，请稍后再试！
```

**解决方案：**
1. 等待一段时间后重试
2. 更换算力资源（如从 ESKU000011 换到 ESKU000001）

---

## 五、修复过程详解

### 第 1 步：诊断问题

- 检查任务日志，发现是 IsaacSim 5.1 内置的 PyTorch vendored packaging 缺少 `_structures.py` 文件
- 该文件包含 `Infinity`, `NegativeInfinity` 等类，是 packaging 23.0+ 版本的一部分

### 第 2 步：尝试方案 A - 复制系统 packaging 文件

```python
shutil.copy2(source_structures, structures_file)
```

**结果：** 失败 - IsaacSim 文件系统只读，无法写入文件

### 第 3 步：尝试方案 B - 修改 startScript 设置环境变量

```bash
gm-run env TORCH_COMPILE_DISABLE=1 ...
```

**结果：** 失败 - `gm-run` 不支持 `env` 命令语法

### 第 4 步：成功方案 - 通过 sys.modules 注入模块

```python
import types
import sys

structures_module = types.ModuleType("torch._vendor.packaging._structures")
structures_module.Infinity = InfinityType()
structures_module.NegativeInfinity = NegativeInfinityType()
sys.modules["torch._vendor.packaging._structures"] = structures_module
```

**结果：** 成功 - 绕过了文件系统限制

### 第 5 步：解决 inductor 问题

训练启动后遇到 `torch._dynamo.exc.BackendCompilerFailed` 错误

**解决方案：** 在 `run_train.py` 中设置环境变量

```python
os.environ["TORCH_COMPILE_DISABLE"] = "1"
os.environ["TORCHDYNAMO_DISABLE"] = "1"
```

---

## 六、成功验证

训练任务成功运行的日志应该包含：

```
[run_train.py] Disabled torch inductor compilation
[run_train.py] Installing holosoma from /workspace/isaaclab/hshud3838840-public/src/holosoma ...
[run_train.py] Injected torch._vendor.packaging._structures module
```

然后训练应该正常进行，显示训练进度和奖励指标：

```
| Learning iteration 100/400000 |
| Mean reward: 0.10             |
| Total timesteps: 409600       |
```

---

## 七、常用命令速查

```bash
# 任务管理
flux task list --page 1 --limit 10           # 查看任务列表
flux task info --task-id "TASK_xxx"          # 查看任务详情
flux task logs --task-id "TASK_xxx" --follow # 查看日志
flux task run --task-id "TASK_xxx"           # 启动任务
flux --yes task stop --task-id "TASK_xxx"    # 停止任务

# 项目管理
flux project list --page 1 --limit 10        # 查看项目列表
flux project create --file ./project.json    # 创建项目

# 资源查看
flux task resource list --goods-back-category 3 --page 1 --limit 10  # 查看算力资源
flux task image official                     # 查看官方镜像
```
