# LeRobot 仿真学习完全指南

> 文档版本: 1.0  
> 创建时间: 2026-02-24  
> 官方文档: https://huggingface.co/lerobot

---

## 📑 目录

1. [LeRobot 简介](#1-lerobot-简介)
2. [安装与环境配置](#2-安装与环境配置)
3. [核心概念](#3-核心概念)
4. [机器人控制](#4-机器人控制)
5. [数据集系统](#5-数据集系统)
6. [模型与训练](#6-模型与训练)
7. [仿真环境](#7-仿真环境)
8. [构建自己的机器人](#8-构建自己的机器人)
9. [代码结构解析](#9-代码结构解析)
10. [常见问题](#10-常见问题)

---

## 1. LeRobot 简介

### 1.1 什么是 LeRobot？

LeRobot 是 Hugging Face 开发的开源机器人学习库，旨在降低机器人 AI 的入门门槛，让每个人都能参与和受益于共享数据集与预训练模型。

### 1.2 核心特性

| 特性 | 说明 |
|------|------|
| **多平台支持** | 从低成本 ARM (SO-100) 到人形机器人 |
| **统一接口** | 标准化的 `Robot` 类，解耦控制逻辑与硬件 |
| **LeRobot Dataset** | 标准化数据集格式 (Parquet + MP4) |
| **预训练模型** | 模仿学习、强化学习、VLA 模型 |
| **仿真支持** | LIBERO、MetaWorld 等 benchmark |

### 1.3 支持的硬件

- SO-100 (机械臂)
- LeKick (腿部机器人)
- Koch (机械臂)
- HopeJim (机械臂)
- ALOHA 系列
- Unitree 机器人
- 键盘/手机/遥操作设备

---

## 2. 安装与环境配置

### 2.1 基本安装

```bash
# 安装 LeRobot
pip install lerobot
lerobot-info
```

### 2.2 WSL 用户注意 (2026-02-23 新增)

```bash
# WSL 用户需要安装 evdev
sudo apt-get install python3-evdev
```

### 2.3 Hugging Face 认证

```bash
# 登录 Hugging Face
huggingface-cli login

# 设置环境变量
export HF_USER=$(huggingface-cli whoami -t)
```

---

## 3. 核心概念

### 3.1 机器人控制 (Robot Class)

```python
from lerobot.robots.my_robot import MyRobot

# 连接机器人
robot = MyRobot(config=...)
robot.connect()

# 获取观察和执行动作
obs = robot.get_observation()
action = model.select_action(obs)
robot.send_action(action)
```

### 3.2 LeRobot Dataset 格式

```python
from lerobot.datasets.lerobot_dataset import LeRobotDataset

# 加载数据集
dataset = LeRobotDataset("lerobot/aloha_mobile_cabinet")

# 访问数据 (自动处理视频解码)
episode_index = 0
print(f"{dataset[episode_index]['action'].shape}")
```

**数据结构**:
- **MP4 文件**: 同步视频 (用于视觉)
- **Parquet 文件**: 状态/动作数据 (Parquet + MP4)

### 3.3 训练策略

```bash
# 训练策略
lerobot-train \
  --policy=act \
  --dataset.repo_id=lerobot/aloha_mobile_cabinet
```

支持的策略:
| 类别 | 模型 |
|------|------|
| 模仿学习 | ACT, Diffuser, VQ-BeT |
| 强化学习 | HIL-SERL, TDMPC |
| VLA 模型 | Pi0, Pi0.5, GR00T N1.5, SmooVLA, XVLA |

---

## 4. 机器人控制

### 4.1 MyRobot 类

```python
class MyRobot:
    def __init__(self, config):
        self.config = config
    
    def connect(self):
        """建立与机器人的连接"""
        pass
    
    def get_observation(self) -> dict:
        """获取观察数据 (视觉 + 状态)"""
        return {
            "observation": ...,  # 传感器数据
            "state": ...        # 关节位置/速度
        }
    
    def send_action(self, action: dict):
        """发送动作到机器人"""
        pass
```

### 4.2 电机驱动 (2026-02-23 新增: RobStride CAN)

LeRobot 支持多种电机驱动:

- **DAMiao** (CAN 总线)
- **RobStride** (CAN 总线) - *新增*
- **标准伺服电机**

```python
# RobStride 电机配置示例
from lerobot.motors import RobStrideMotor

motor = RobStrideMotor(
    bus_id=0,
    motor_id=1,
    baudrate=1000000
)
```

---

## 5. 数据集系统

### 5.1 数据集创建

```bash
# 创建数据集
python -m lerobot.scripts.record \
  --robot.type=my_robot \
  --dataset.repo_id=my_dataset \
  --dataset.tags='["my_robot", "teleoperation"]'
```

### 5.2 数据集处理工具 (2026-02-23 新增: metadata_buffer_size)

- 删除片段 (episodes)
- 按索引/片段分割
- 添加/移除特征
- 合并多个数据集

### 5.3 流式视频编码 (2026-02-23 重大更新)

新增流式视频编码和硬件加速支持:

```bash
# 启用流式编码
python -m lerobot.scripts.record \
  --dataset.streaming_encoding=true \
  --dataset.vcodec=h264_nvenc  # NVIDIA 硬件编码
```

**优势**:
- 使用 GPU/NPU 硬件加速
- 多线程处理避免帧延迟
- 可配置编码器 (h264, h265, vp9)

---

## 6. 模型与训练

### 6.1 训练命令

```bash
# 训练模型
lerobot-train \
  --policy=act \
  --dataset.repo_id=lerobot/aloha_mobile_cabinet
```

### 6.2 评估

```bash
# 在 LIBERO benchmark 上评估
lerobot-eval \
  --policy.path=lerobot/pi0_libero_finetuned \
  --env.type=libero \
  --env.task=libero_object \
  --eval.n_episodes=10
```

### 6.3 发布模型到 HF Hub

```bash
# 推送训练好的模型
lerobot-push-to-hub \
  --policy.path=./output/policy \
  --repo_id=your_username/my_robot_policy
```

---

## 7. 仿真环境

### 7.1 支持的 Benchmark

| Benchmark | 说明 |
|-----------|------|
| **LIBERO** | 长期任务规划 |
| **MetaWorld** | 多任务机械臂 |
| **Gymnasium** | 通用环境 |

### 7.2 创建自定义仿真环境

```python
# 参考 EnvHub 文档创建自定义环境
# 详见: https://huggingface.co/docs/lerobot/envhub
```

### 7.3 gym-hil 集成 (2026-02-19 修复)

修复了 gym-hil 与新 LeRobot pipeline 的集成问题:

- 新增 `GymHILAdapterProcessorStep`
- 修复遥操作为 None 时的动作特征问题
- 修复夹爪的中性动作

---

## 8. 构建自己的机器人

### 8.1 步骤概述

1. **实现 Robot 接口**
2. **配置电机驱动**
3. **设置传感器**
4. **创建数据集**
5. **训练策略**
6. **部署与评估**

### 8.2 代码模板

```python
# lerobot/robots/my_robot.py
from lerobot.robots import Robot

class MyRobot(Robot):
    """自定义机器人"""
    
    def __init__(self, config: dict):
        super().__init__(config)
        # 初始化电机、相机等
        self.motors = ...
        self.cameras = [...]
    
    def connect(self):
        """连接机器人硬件"""
        for motor in self.motors:
            motor.connect()
    
    def get_observation(self) -> dict:
        """获取观察"""
        return {
            "image": self.cameras[0].read(),
            "state": self.read_motor_states()
        }
    
    def send_action(self, action: torch.Tensor):
        """发送动作"""
        self.motors.set_positions(action)
    
    def disconnect(self):
        """断开连接"""
        for motor in self.motors:
            motor.disconnect()
```

### 8.3 配置示例

```yaml
# config/my_robot.yaml
robot:
  type: my_robot
  motors:
    - name: joint_1
      id: 1
      type: RobStride
    - name: joint_2
      id: 2
      type: RobStride
  cameras:
    - name: wrist_camera
      type: realsense
```

---

## 9. 代码结构解析

### 9.1 目录结构

```
lerobot/
├── lerobot/
│   ├── robots/           # 机器人接口和实现
│   │   ├── my_robot.py   # 自定义机器人模板
│   │   ├── koch.py      # Koch 机械臂
│   │   └── ...
│   ├── motors/           # 电机驱动
│   │   ├── damiao.py     # DAMiao 电机
│   │   ├── robstride.py  # RobStride 电机 (新增)
│   │   └── ...
│   ├── datasets/          # 数据集处理
│   │   ├── lerobot_dataset.py
│   │   └── ...
│   ├── policies/         # 策略模型
│   │   ├── act/
│   │   ├── pi0/
│   │   └── ...
│   ├── envs/             # 仿真环境
│   └── scripts/          # 命令行工具
│       ├── record.py     # 数据采集
│       ├── train.py     # 训练
│       └── eval.py      # 评估
├── docs/                 # 文档
└── tests/                # 测试
```

### 9.2 关键文件说明

| 文件 | 用途 |
|------|------|
| `robots/robot.py` | 基础 Robot 类定义 |
| `motors/motor.py` | 电机接口 |
| `datasets/dataset.py` | 数据集加载 |
| `policies/policy.py` | 策略基类 |

---

## 10. 常见问题

### Q1: WSL 安装失败?

```bash
# 安装 evdev
sudo apt-get install python3-evdev
```

### Q2: 视频采集卡顿?

启用流式视频编码:
```bash
--dataset.streaming_encoding=true
--dataset.vcodec=h264_nvenc
```

### Q3: 如何添加新电机?

参考 `motors/robstride.py` 实现:

1. 继承 `Motor` 基类
2. 实现 `read()` 和 `write()` 方法
3. 添加到电机注册表

---

## 📚 参考资源

- [官方文档](https://huggingface.co/docs/lerobot)
- [GitHub 仓库](https://github.com/huggingface/lerobot)
- [中文教程](https://zihao-ai.feiinit.cn/wiki/space/7589642043471924447)
- [Discord 社区](https://discord.gg/s3KuuzsPFb)

---

*文档最后更新: 2026-02-24*
