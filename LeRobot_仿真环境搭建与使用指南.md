# LeRobot 仿真环境完全指南

> 文档版本: 1.0  
> 创建时间: 2026-02-24  
> 官方文档: https://huggingface.co/docs/lerobot/envhub

---

## 📑 目录

1. [仿真环境概述](#1-仿真环境概述)
2. [EnvHub 详解](#2-envhub-详解)
3. [内置仿真环境](#3-内置仿真环境)
4. [环境配置与运行](#4-环境配置与运行)
5. [创建自定义仿真环境](#5-创建自定义仿真环境)
6. [评估与测试](#6-评估与测试)
7. [示例代码](#7-示例代码)

---

## 1. 仿真环境概述

### 1.1 什么是仿真环境？

LeRobot 支持在仿真环境中训练和评估机器人策略，无需真实硬件。

### 1.2 支持的仿真平台

| 平台 | 说明 | 支持状态 |
|------|------|----------|
| **EnvHub** | Hugging Face Hub 上的自定义环境 | ✅ |
| **LIBERO** | 长期任务规划 benchmark | ✅ |
| **MetaWorld** | 多任务机械臂 benchmark | ✅ |
| **Gymnasium** | 通用强化学习环境 | ✅ |

---

## 2. EnvHub 详解

### 2.1 什么是 EnvHub？

EnvHub 让你可以直接从 Hugging Face Hub 加载自定义仿真环境，只需一行代码！

### 2.2 快速开始

```python
from lerobot.envs.factory import make_env

# 从 Hub 加载环境
env = make_env("lerobot/cartpole-env", trust_remote_code=True)
```

### 2.3 URL 格式

| 格式 | 说明 | 示例 |
|------|------|------|
| `user/repo` | 从主分支加载 | `lerobot/pusht-env` |
| `user/repo@revision` | 从指定版本加载 | `lerobot/pusht-env@main` |
| `user/repo:path` | 加载自定义文件 | `lerobot/envs:pusht.py` |
| `user/repo@rev:path` | 版本+自定义文件 | `lerobot/envs@v1:pusht.py` |

---

## 3. 内置仿真环境

### 3.1 LIBERO

**LIBERO** 是一个长期任务规划 benchmark，包含多种家务任务。

```python
from lerobot.envs.libero import make_env

# 加载 LIBERO 环境
envs_dict = make_env(
    env_name="libero_object",  # 任务名称
    n_envs=4,                  # 并行环境数
    use_async_envs=True        # 异步环境
)
```

**可用任务**:
| 任务ID | 说明 |
|--------|------|
| `libero_object` | 物体抓取放置 |
| `libero_spatial` | 空间推理 |
| `libero_10` | 10 个任务的子集 |

### 3.2 MetaWorld

**MetaWorld** 是多任务机械臂 benchmark。

```python
from lerobot.envs.metaworld import make_env

# 加载 MetaWorld 环境
envs_dict = make_env(
    env_name="reach_push",  # 任务名称
    n_envs=4,
    use_async_envs=True
)
```

**可用任务**:
| 任务ID | 说明 |
|--------|------|
| `reach_push` | 到达和推动 |
| `pick_place` | 抓取放置 |
| `door_open` | 开门 |
| `drawer_open` | 打开抽屉 |

---

## 4. 环境配置与运行

### 4.1 评估配置文件

```python
# eval_config.py
from dataclasses import dataclass

@dataclass
class EvalConfig:
    # 环境配置
    env_type: str = "libero"          # 环境类型
    env_task: str = "libero_object"   # 任务名称
    n_envs: int = 10                  # 并行环境数
    
    # 评估配置
    n_episodes: int = 100             # 评估 episodes 数量
    max_steps: int = 300              # 每个 episode 最大步数
    
    # 渲染配置
    render_mode: str = "rgb_array"    # 渲染模式
    save_video: bool = True           # 保存视频
    video_dir: str = "./videos"      # 视频保存目录
```

### 4.2 命令行评估

```bash
# 评估策略
lerobot-eval \
  --policy.path=lerobot/pi0_libero_finetuned \
  --env.type=libero \
  --env.task=libero_object \
  --eval.n_episodes=10
```

### 4.3 代码评估

```python
from lerobot.envs.factory import make_env
from lerobot.policies import ACTPolicy

# 加载环境
envs_dict = make_env("lerobot/pusht-env", n_envs=4, trust_remote_code=True)

# 获取环境
suite_name = next(iter(envs_dict))
env = envs_dict[suite_name][0]

# 加载策略
policy = ACTPolicy.from_pretrained("lerobot/act_pusht")

# 评估
obs, info = env.reset()
for step in range(1000):
    action = policy.select_action(obs)
    obs, reward, terminated, truncated, info = env.step(action)
    
    if terminated.all() or truncated.all():
        obs, info = env.reset()

env.close()
```

---

## 5. 创建自定义仿真环境

### 5.1 仓库结构

```
my-env-repo/
├── env.py                 # 主环境定义 (必需)
├── requirements.txt       # 依赖 (可选)
├── README.md             # 文档 (推荐)
└── assets/               # 资源文件 (可选)
    └── demo.gif
```

### 5.2 env.py 模板

```python
# env.py
import gymnasium as gym
import numpy as np

def make_env(n_envs: int = 1, use_async_envs: bool = False):
    """
    创建向量化环境
    
    Args:
        n_envs: 并行环境数量
        use_async_envs: 是否使用异步环境
    
    Returns:
        gym.vector.VectorEnv
    """
    
    def _make_single_env():
        # 创建单个环境
        return MyCustomEnv()
    
    # 选择向量化环境类型
    if use_async_envs:
        env_cls = gym.vector.AsyncVectorEnv
    else:
        env_cls = gym.vector.SyncVectorEnv
    
    # 创建向量化环境
    vec_env = env_cls([_make_single_env for _ in range(n_envs)])
    
    return vec_env


class MyCustomEnv(gym.Env):
    """自定义机器人仿真环境"""
    
    def __init__(self):
        super().__init__()
        
        # 定义观察空间 (相机图像 + 关节状态)
        self.observation_space = gym.spaces.Dict({
            "image": gym.spaces.Box(low=0, high=255, shape=(64, 64, 3), dtype=np.uint8),
            "state": gym.spaces.Box(low=-1, high=1, shape=(7,), dtype=np.float32)
        })
        
        # 定义动作空间 (7个关节位置)
        self.action_space = gym.spaces.Box(low=-1, high=1, shape=(7,), dtype=np.float32)
        
        # 仿真器
        self.sim = None
        self.step_count = 0
    
    def reset(self, seed=None, options=None):
        """重置环境"""
        super().reset(seed=seed)
        
        # 重置仿真状态
        self.sim.reset()
        self.step_count = 0
        
        # 返回初始观察
        obs = self._get_obs()
        info = {}
        
        return obs, info
    
    def step(self, action):
        """执行一步"""
        # 应用动作到仿真器
        self.sim.set_joint_positions(action)
        self.sim.step()
        
        # 获取观察和奖励
        obs = self._get_obs()
        reward = self._compute_reward()
        self.step_count += 1
        
        # 检查是否结束
        terminated = self._is_done()
        truncated = self.step_count >= self.max_steps
        
        info = {"success": terminated}
        
        return obs, reward, terminated, truncated, info
    
    def _get_obs(self):
        """获取观察"""
        return {
            "image": self.sim.render(),      # 相机图像
            "state": self.sim.get_joints()   # 关节状态
        }
    
    def _compute_reward(self):
        """计算奖励"""
        return 1.0 if self._is_done() else 0.0
    
    def _is_done(self):
        """检查是否完成"""
        return self.sim.is_goal_reached()
    
    def render(self):
        """渲染"""
        return self.sim.render()
```

### 5.3 本地测试

```python
# 测试自定义环境
from lerobot.envs.utils import _load_module_from_path, _call_make_env

# 加载模块
module = _load_module_from_path("./env.py")

# 测试 make_env
result = _call_make_env(module, n_envs=2, use_async_envs=False)

# 验证
env = result[0]
obs, info = env.reset()
print(f"观察形状: {obs['image'].shape}")
env.close()
```

### 5.4 上传到 Hub

```bash
# 登录 Hugging Face
huggingface-cli login

# 创建仓库
huggingface-cli repo create my-custom-env --type space

# 初始化并推送
git init
git add .
git commit -m "Initial environment"
git remote add origin https://huggingface.co/your_username/my-custom-env
git push -u origin main
```

---

## 6. 评估与测试

### 6.1 评估脚本

```python
# eval_my_env.py
import argparse
from lerobot.envs.factory import make_env

def evaluate(policy, env, n_episodes=10, max_steps=300):
    """评估策略"""
    rewards = []
    
    for episode in range(n_episodes):
        obs, info = env.reset()
        episode_reward = 0
        
        for step in range(max_steps):
            action = policy.select_action(obs)
            obs, reward, terminated, truncated, info = env.step(action)
            episode_reward += reward
            
            if terminated or truncated:
                break
        
        rewards.append(episode_reward)
        print(f"Episode {episode+1}: {episode_reward:.2f}")
    
    avg_reward = sum(rewards) / len(rewards)
    print(f"\n平均奖励: {avg_reward:.2f}")
    return avg_reward

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--env", type=str, default="my-env")
    parser.add_argument("--policy", type=str, required=True)
    args = parser.parse_args()
    
    # 加载环境和策略
    envs_dict = make_env(args.env, n_envs=1, trust_remote_code=True)
    env = envs_dict[next(iter(envs_dict))][0]
    policy = load_policy(args.policy)
    
    # 评估
    evaluate(policy, env)
```

### 6.2 运行评估

```bash
python eval_my_env.py \
  --env lerobot/pusht-env \
  --policy lerobot/act_pusht
```

---

## 7. 示例代码

### 7.1 CartPole 示例

```python
from lerobot.envs.factory import make_env
import numpy as np

# 加载 CartPole 环境
envs_dict = make_env("lerobot/cartpole-env", n_envs=4, trust_remote_code=True)
suite_name = next(iter(envs_dict))
env = envs_dict[suite_name][0]

# 运行简单 episode
obs, info = env.reset()
done = np.zeros(env.num_envs, dtype=bool)
total_reward = np.zeros(env.num_envs)

while not done.all():
    action = env.action_space.sample()  # 随机策略
    obs, reward, terminated, truncated, info = env.step(action)
    total_reward += reward
    done = terminated | truncated

print(f"平均奖励: {total_reward.mean():.2f}")
env.close()
```

### 7.2 LIBERO 示例

```python
from lerobot.envs.libero import make_env

# 加载 LIBERO 物体放置任务
envs_dict = make_env(
    env_name="libero_object",
    n_envs=10,
    use_async_envs=True
)

suite_name = next(iter(envs_dict))
env = envs_dict[suite_name][0]

# 评估
obs, info = env.reset()
for _ in range(300):
    action = env.action_space.sample()
    obs, reward, terminated, truncated, info = env.step(action)
    
    if terminated.all():
        obs, info = env.reset()

env.close()
```

### 7.3 自定义机器人环境

```python
# my_robot_env.py
import gymnasium as gym
from gymnasium import spaces
import numpy as np

class RobotEnv(gym.Env):
    """自定义机器人环境"""
    
    def __init__(self):
        super().__init__()
        
        # 观察空间: 图像 + 关节状态
        self.observation_space = spaces.Dict({
            "image": spaces.Box(0, 255, (64, 64, 3), dtype=np.uint8),
            "position": spaces.Box(-1, 1, (6,), dtype=np.float32),
            "velocity": spaces.Box(-1, 1, (6,), dtype=np.float32)
        })
        
        # 动作空间: 6 个关节位置
        self.action_space = spaces.Box(-1, 1, (6,), dtype=np.float32)
        
        self.max_steps = 500
        self.step_count = 0
    
    def reset(self, seed=None, options=None):
        self.step_count = 0
        obs = self._get_obs()
        info = {}
        return obs, info
    
    def step(self, action):
        # 执行动作
        self._apply_action(action)
        self.step_count += 1
        
        # 获取观察和奖励
        obs = self._get_obs()
        reward = self._compute_reward()
        
        # 检查结束条件
        terminated = self._is_terminated()
        truncated = self.step_count >= self.max_steps
        
        return obs, reward, terminated, truncated, {}
    
    def _get_obs(self):
        # 获取仿真器输出
        return {
            "image": np.random.randint(0, 255, (64, 64, 3), dtype=np.uint8),
            "position": np.random.randn(6).astype(np.float32),
            "velocity": np.random.randn(6).astype(np.float32)
        }
    
    def _apply_action(self, action):
        pass  # 实现你的仿真器调用
    
    def _compute_reward(self):
        return 0.0
    
    def _is_terminated(self):
        return False


def make_env(n_envs=1, use_async_envs=False):
    def _make():
        return RobotEnv()
    
    if use_async_envs:
        return gym.vector.AsyncVectorEnv([_make for _ in range(n_envs)])
    else:
        return gym.vector.SyncVectorEnv([_make for _ in range(n_envs)])
```

---

## 📚 参考资源

- [EnvHub 官方文档](https://huggingface.co/docs/lerobot/envhub)
- [Gymnasium 文档](https://gymnasium.farama.org/)
- [LIBERO 论文](https://arxiv.org/abs/2306.16610)
- [MetaWorld 论文](https://arxiv.org/abs/1907.04613)

---

*文档最后更新: 2026-02-24*
