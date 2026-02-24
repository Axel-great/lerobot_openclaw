# LeRobot 项目代码结构详解与自定义机器人开发指南

> 文档版本: 1.0  
> 创建时间: 2026-02-24  
> 项目地址: https://github.com/huggingface/lerobot

---

## 📑 目录

1. [项目整体结构](#1-项目整体结构)
2. [核心模块详解](#2-核心模块详解)
3. [机器人注册机制](#3-机器人注册机制)
4. [创建自定义机器人 (手把手教学)](#4-创建自定义机器人-手把手教学)
5. [代码模板与示例](#5-代码模板与示例)
6. [常见问题与调试](#6-常见问题与调试)

---

## 1. 项目整体结构

```
lerobot/
├── src/lerobot/              # 主要源代码
│   ├── robots/               # 🤖 机器人实现 (重点!)
│   │   ├── __init__.py       # 机器人注册入口
│   │   ├── robot.py          # Robot 基类 (抽象类)
│   │   ├── config.py         # RobotConfig 基类
│   │   ├── utils.py          # 机器人工具函数
│   │   ├── koch_follower/    # 示例: Koch 机械臂
│   │   ├── so_follower/      # SO-100 机械臂
│   │   ├── unitree_g1/       # Unitree G1 人形机器人
│   │   ├── reachy2/          # Reachy2 机器人
│   │   └── ...
│   ├── motors/               # 🔌 电机驱动
│   │   ├── motors_bus.py     # 电机基类和总线
│   │   ├── dynamixel.py      # Dynamixel 电机
│   │   ├── feetech.py        # Feetech 电机
│   │   ├── damiao.py         # DAMiao 电机
│   │   └── robstride.py      # RobStride 电机 (新增)
│   ├── cameras/              # 📷 相机驱动
│   │   ├── camera.py         # 相机基类
│   │   ├── realsense/        # Intel RealSense
│   │   ├── opencv/           # OpenCV 通用相机
│   │   └── zmq/              # 网络相机
│   ├── teleoperators/        # 🎮 遥操作设备
│   │   ├── keyboard/         # 键盘
│   │   ├── gamepad/          # 手柄
│   │   ├── phone/            # 手机
│   │   └── so_leader/        # SO-100 遥操作臂
│   ├── datasets/             # 📊 数据集处理
│   ├── policies/             # 🧠 策略模型
│   ├── configs/              # ⚙️ 配置管理
│   └── scripts/              # 📜 命令行工具
├── tests/                    # 单元测试
├── docs/                    # 文档
└── examples/                # 示例
```

---

## 2. 核心模块详解

### 2.1 robots/ 机器人模块

#### 2.1.1 robot.py - Robot 基类

**文件位置**: `src/lerobot/robots/robot.py`

**作用**: 所有机器人的抽象基类，定义了机器人接口规范。

**核心方法**:

| 方法 | 必选 | 说明 |
|------|------|------|
| `observation_features` | ✅ | 定义观察数据的特征 (属性) |
| `action_features` | ✅ | 定义动作数据的特征 (属性) |
| `is_connected` | ✅ | 检查连接状态 |
| `connect()` | ✅ | 连接机器人 |
| `is_calibrated` | ✅ | 检查校准状态 |
| `calibrate()` | ✅ | 校准机器人 |
| `configure()` | ✅ | 配置机器人参数 |
| `get_observation()` | ✅ | 获取观察数据 |
| `send_action()` | ✅ | 发送动作指令 |
| `disconnect()` | ✅ | 断开连接 |

**代码结构**:
```python
class Robot(abc.ABC):
    # 子类必须设置
    config_class: builtins.type[RobotConfig]  # 配置类
    name: str                                  # 机器人名称
    
    def __init__(self, config: RobotConfig):
        # 初始化校准目录
        self.calibration_dir = ...
        self.calibration = {}
    
    # 抽象属性和方法 (子类必须实现)
    @property
    @abc.abstractmethod
    def observation_features(self) -> dict:
        """返回观察特征: {"motor.pos": float, "camera": (height, width, 3)}"""
        pass
    
    @property
    @abc.abstractmethod
    def action_features(self) -> dict:
        """返回动作特征: {"motor.pos": float}"""
        pass
    
    @abc.abstractmethod
    def connect(self, calibrate: bool = True) -> None:
        pass
    
    # ... 其他抽象方法
```

#### 2.1.2 config.py - 配置基类

**文件位置**: `src/lerobot/robots/config.py`

**作用**: 机器人配置的基类，使用 draccus 库实现配置管理。

**核心代码**:
```python
@dataclass(kw_only=True)
class RobotConfig(draccus.ChoiceRegistry, abc.ABC):
    # 机器人唯一标识
    id: str | None = None
    # 校准文件目录
    calibration_dir: Path | None = None
    
    @property
    def type(self) -> str:
        return self.get_choice_name(self.__class__)
```

**关键特性**: 
- 使用 `@RobotConfig.register_subclass("name")` 注册子类
- 支持配置验证

---

### 2.2 motors/ 电机模块

#### 2.2.1 电机驱动架构

```
motors/
├── motors_bus.py          # Motor, MotorCalibration, MotorNormMode
├── dynamixel.py           # Dynamixel 电机 (RS485)
├── feetech.py             # Feetech 电机 (TTL)
├── damiao.py              # DAMiao 电机 (CAN)
└── robstride.py           # RobStride 电机 (CAN) - 新增
```

#### 2.2.2 Motor 类

**定义**:
```python
@dataclass
class Motor:
    id: int                      # 电机 ID
    model: str                   # 电机型号
    norm_mode: MotorNormMode     # 归一化模式
```

**归一化模式**:
| 模式 | 说明 | 范围 |
|------|------|------|
| `RANGE_M100_100` | 百分比模式 | -100 ~ 100 |
| `RANGE_0_100` | 0-100模式 | 0 ~ 100 |
| `DEGREES` | 角度模式 | 度数 |

#### 2.2.3 MotorsBus 总线

**作用**: 管理多个电机的通信

```python
class DynamixelMotorsBus(MotorsBusBase):
    def __init__(self, port: str, motors: dict[str, Motor], calibration=None):
        self.port = port
        self.motors = motors  # {"motor_name": Motor(...)}
    
    def sync_read(self, data_name: str, motors=None) -> dict[str, Value]:
        """同步读取多个电机数据"""
    
    def sync_write(self, data_name: str, values: dict[str, Value]) -> None:
        """同步写入多个电机数据"""
```

---

### 2.3 cameras/ 相机模块

#### 2.3.1 相机配置

```python
@dataclass
class CameraConfig(draccus.ChoiceRegistry):
    type: str              # 相机类型
    width: int | None = None   # 宽度
    height: int | None = None  # 高度
    fps: int | None = None     # 帧率
```

#### 2.3.2 支持的相机

| 相机类型 | 说明 |
|----------|------|
| `realsense` | Intel RealSense D435i |
| `opencv` | OpenCV 兼容 USB 相机 |
| `zmq` | 网络相机 (ZMQ) |
| `reachy2_camera` | Reachy2 专用相机 |

---

## 3. 机器人注册机制

### 3.1 注册流程

机器人通过 `RobotConfig.register_subclass("type_name")` 装饰器注册：

```python
# koch_follower/config_koch_follower.py
@RobotConfig.register_subclass("koch_follower")
@dataclass
class KochFollowerConfig(RobotConfig):
    port: str
    cameras: dict[str, CameraConfig] = field(default_factory=dict)
```

### 3.2 工厂函数

**文件**: `src/lerobot/robots/utils.py`

```python
def make_robot_from_config(config: RobotConfig) -> Robot:
    """根据配置创建机器人实例"""
    
    if config.type == "koch_follower":
        from .koch_follower import KochFollower
        return KochFollower(config)
    elif config.type == "so100_follower":
        from .so_follower import SO100Follower
        return SO100Follower(config)
    # ... 其他机器人类型
    else:
        # 尝试通用方式创建
        return cast(Robot, make_device_from_device_class(config))
```

**注意**: 如果新增机器人类型，需要在 `utils.py` 的 `make_robot_from_config` 函数中添加对应的导入和创建逻辑！

---

## 4. 创建自定义机器人 (手把手教学)

### 4.1 步骤概述

```
创建自定义机器人需要以下文件:
├── my_robot/
│   ├── __init__.py           # 导出 Robot 和 Config
│   ├── config_my_robot.py    # 配置类
│   └── my_robot.py           # 机器人实现
```

### 4.2 第一步: 创建配置文件

**文件**: `src/lerobot/robots/my_robot/config_my_robot.py`

```python
# Copyright 2024 The HuggingFace Inc. team.
# License: Apache 2.0

from dataclasses import dataclass, field

from lerobot.cameras import CameraConfig
from lerobot.robots import RobotConfig


@RobotConfig.register_subclass("my_robot")  # 🔑 注册机器人类型
@dataclass
class MyRobotConfig(RobotConfig):
    """
    自定义机器人配置
    
    属性说明:
        port: 串口/CAN 总线端口
        n_motors: 电机数量
        motor_type: 电机型号 (dynamixel/feetech/damiao/robstride)
        disable_torque_on_disconnect: 断开时禁用扭矩
        cameras: 相机配置字典
    """
    
    # 🔌 通信端口 (串口或 CAN)
    port: str = "/dev/ttyUSB0"
    
    # 🤖 电机配置
    n_motors: int = 6
    motor_type: str = "dynamixel"  # 电机类型
    
    # ⚙️ 安全设置
    disable_torque_on_disconnect: bool = True
    max_relative_target: float | dict[str, float] | None = None
    
    # 📷 相机配置
    cameras: dict[str, CameraConfig] = field(default_factory=dict)
    
    # 🔧 调试模式
    simulation: bool = False  # 是否为模拟模式
```

### 4.3 第二步: 创建机器人实现

**文件**: `src/lerobot/robots/my_robot/my_robot.py`

```python
# Copyright 2024 The HuggingFace Inc. team.
# License: Apache 2.0

import logging
import time
from functools import cached_property

from lerobot.cameras.utils import make_cameras_from_configs
from lerobot.motors import Motor, MotorCalibration, MotorNormMode
from lerobot.motors.dynamixel import (
    DynamixelMotorsBus,
    OperatingMode,
)
from lerobot.processor import RobotAction, RobotObservation
from lerobot.utils.decorators import check_if_already_connected, check_if_not_connected

from ..robot import Robot
from ..utils import ensure_safe_goal_position
from .config_my_robot import MyRobotConfig

logger = logging.getLogger(__name__)


class MyRobot(Robot):
    """
    自定义机器人实现示例
    
    这个类实现了 Robot 抽象基类的所有方法。
    你需要根据你的硬件修改连接、观察和动作的实现。
    
    机器人特性:
        - 支持 6 个 Dynamixel 电机
        - 支持多个相机
        - 支持校准
        - 安全位置限制
    """
    
    # 🔑 关键: 设置配置类和名称
    config_class = MyRobotConfig
    name = "my_robot"
    
    def __init__(self, config: MyRobotConfig):
        """初始化机器人"""
        super().__init__(config)  # 必须调用父类初始化
        self.config = config
        
        # 🏗️ 根据配置创建电机总线
        # 这里以 Dynamixel 电机为例
        motor_configs = self._create_motor_configs()
        
        self.bus = DynamixelMotorsBus(
            port=self.config.port,
            motors=motor_configs,
            calibration=self.calibration,
        )
        
        # 📷 创建相机
        self.cameras = make_cameras_from_configs(config.cameras)
    
    def _create_motor_configs(self) -> dict[str, Motor]:
        """创建电机配置"""
        motors = {}
        
        # 定义电机名称和参数
        motor_names = [
            "joint_1",   # 关节 1
            "joint_2",   # 关节 2
            "joint_3",   # 关节 3
            "joint_4",   # 关节 4
            "joint_5",   # 关节 5
            "gripper",   # 夹爪
        ]
        
        # 电机型号 (根据你的硬件选择)
        motor_model = "xl430-w250"  # 可选: xl330-m288, xm430-w350 等
        norm_mode = MotorNormMode.RANGE_M100_100
        gripper_norm_mode = MotorNormMode.RANGE_0_100
        
        for i, motor_name in enumerate(motor_names):
            is_gripper = motor_name == "gripper"
            motors[motor_name] = Motor(
                id=i + 1,  # 电机 ID (1-6)
                model=motor_model,
                norm_mode=gripper_norm_mode if is_gripper else norm_mode,
            )
        
        return motors
    
    # ==================== 观察特征 ====================
    
    @property
    def _motors_ft(self) -> dict[str, type]:
        """电机特征: 每个电机位置为浮点数"""
        return {f"{motor}.pos": float for motor in self.bus.motors}
    
    @property
    def _cameras_ft(self) -> dict[str, tuple]:
        """相机特征: 每个相机返回 (height, width, 3)"""
        return {
            cam: (self.config.cameras[cam].height, 
                  self.config.cameras[cam].width, 3) 
            for cam in self.cameras
        }
    
    @cached_property
    def observation_features(self) -> dict[str, type | tuple]:
        """
        观察特征 (必须实现)
        
        返回格式:
        {
            "joint_1.pos": float,
            "joint_2.pos": float,
            ...
            "camera_name": (height, width, 3)
        }
        """
        return {**self._motors_ft, **self._cameras_ft}
    
    @cached_property
    def action_features(self) -> dict[str, type]:
        """
        动作特征 (必须实现)
        
        返回格式:
        {
            "joint_1.pos": float,
            "joint_2.pos": float,
            ...
        }
        """
        return self._motors_ft
    
    # ==================== 连接与断开 ====================
    
    @property
    def is_connected(self) -> bool:
        """检查是否已连接"""
        return self.bus.is_connected and all(
            cam.is_connected for cam in self.cameras.values()
        )
    
    @check_if_already_connected
    def connect(self, calibrate: bool = True) -> None:
        """
        连接机器人 (必须实现)
        
        步骤:
        1. 连接电机总线
        2. 校准 (可选)
        3. 连接相机
        4. 配置机器人参数
        """
        logger.info(f"Connecting to {self}...")
        
        # 1. 连接电机
        self.bus.connect()
        
        # 2. 校准
        if not self.is_calibrated and calibrate:
            logger.info("Running calibration...")
            self.calibrate()
        
        # 3. 连接相机
        for cam_name, cam in self.cameras.items():
            cam.connect()
        
        # 4. 配置
        self.configure()
        
        logger.info(f"{self} connected successfully!")
    
    # ==================== 校准 ====================
    
    @property
    def is_calibrated(self) -> bool:
        """检查是否已校准"""
        return self.bus.is_calibrated
    
    def calibrate(self) -> None:
        """
        校准机器人 (必须实现)
        
        校准过程:
        1. 禁用扭矩
        2. 移动到中间位置
        3. 记录零位偏移
        4. 记录关节范围
        5. 保存校准文件
        """
        self.bus.disable_torque()
        
        if self.calibration:
            # 使用已有校准文件
            user_input = input(
                f"Press ENTER to use existing calibration, "
                f"or type 'c' to run new calibration: "
            )
            if user_input.strip().lower() != "c":
                self.bus.write_calibration(self.calibration)
                return
        
        logger.info(f"\n=== Running calibration for {self} ===")
        
        # 设置为扩展位置模式
        for motor in self.bus.motors:
            self.bus.write("Operating_Mode", motor, OperatingMode.EXTENDED_POSITION.value)
        
        # 提示用户移动到中间位置
        input("Move robot to middle position and press ENTER...")
        
        # 记录零位偏移
        homing_offsets = self.bus.set_half_turn_homings()
        
        # 提示用户移动关节
        input("Move each joint through full range, then press ENTER...")
        
        # 记录关节范围
        range_mins, range_maxes = self.bus.record_ranges_of_motion(
            list(self.bus.motors.keys())
        )
        
        # 创建校准数据
        self.calibration = {}
        for motor_name, motor in self.bus.motors.items():
            self.calibration[motor_name] = MotorCalibration(
                id=motor.id,
                drive_mode=0,
                homing_offset=homing_offsets[motor_name],
                range_min=range_mins[motor_name],
                range_max=range_maxes[motor_name],
            )
        
        # 保存校准
        self.bus.write_calibration(self.calibration)
        self._save_calibration()
        logger.info(f"Calibration saved to {self.calibration_fpath}")
    
    # ==================== 配置 ====================
    
    def configure(self) -> None:
        """
        配置机器人参数 (必须实现)
        
        在这里设置:
        - 电机控制模式
        - PID 参数
        - 其他运行时配置
        """
        with self.bus.torque_disabled():
            # 配置所有电机为扩展位置模式
            for motor in self.bus.motors:
                if motor != "gripper":
                    self.bus.write("Operating_Mode", motor, OperatingMode.EXTENDED_POSITION.value)
            
            # 夹爪使用电流控制模式
            self.bus.write("Operating_Mode", "gripper", OperatingMode.CURRENT_POSITION.value)
            
            # 设置 PID (可选)
            self.bus.write("Position_P_Gain", "joint_3", 1500)
            self.bus.write("Position_D_Gain", "joint_3", 600)
    
    # ==================== 观察与动作 ====================
    
    @check_if_not_connected
    def get_observation(self) -> RobotObservation:
        """
        获取观察 (必须实现)
        
        返回当前机器人状态:
        - 电机位置
        - 相机图像
        
        返回格式需匹配 observation_features
        """
        start = time.perf_counter()
        
        # 读取电机位置
        obs_dict = self.bus.sync_read("Present_Position")
        obs_dict = {f"{motor}.pos": val for motor, val in obs_dict.items()}
        
        dt_ms = (time.perf_counter() - start) * 1e3
        logger.debug(f"{self} read state: {dt_ms:.1f}ms")
        
        # 读取相机图像
        for cam_key, cam in self.cameras.items():
            obs_dict[cam_key] = cam.read_latest()
        
        return obs_dict
    
    @check_if_not_connected
    def send_action(self, action: RobotAction) -> RobotAction:
        """
        发送动作 (必须实现)
        
        接收目标位置，发送到电机
        
        参数:
            action: 目标位置字典 {"motor.pos": value, ...}
            
        返回:
            实际发送的位置 (可能被裁剪)
        """
        # 提取电机位置 (去除 .pos 后缀)
        goal_pos = {
            key.removesuffix(".pos"): val 
            for key, val in action.items() 
            if key.endswith(".pos")
        }
        
        # 安全限制: 限制相对移动距离
        if self.config.max_relative_target is not None:
            present_pos = self.bus.sync_read("Present_Position")
            goal_present_pos = {
                key: (g_pos, present_pos[key]) 
                for key, g_pos in goal_pos.items()
            }
            goal_pos = ensure_safe_goal_position(
                goal_present_pos, 
                self.config.max_relative_target
            )
        
        # 发送到电机
        self.bus.sync_write("Goal_Position", goal_pos)
        
        return {f"{motor}.pos": val for motor, val in goal_pos.items()}
    
    # ==================== 断开连接 ====================
    
    @check_if_not_connected
    def disconnect(self) -> None:
        """断开连接 (必须实现)"""
        # 断开电机
        self.bus.disconnect(self.config.disable_torque_on_disconnect)
        
        # 断开相机
        for cam in self.cameras.values():
            cam.disconnect()
        
        logger.info(f"{self} disconnected.")
```

### 4.4 第三步: 创建 __init__.py

**文件**: `src/lerobot/robots/my_robot/__init__.py`

```python
# Copyright 2024 The HuggingFace Inc. team.
# License: Apache 2.0

from .config_my_robot import MyRobotConfig
from .my_robot import MyRobot

__all__ = ["MyRobot", "MyRobotConfig"]
```

### 4.5 第四步: 注册到工厂函数

**修改文件**: `src/lerobot/robots/utils.py`

在 `make_robot_from_config` 函数中添加:

```python
def make_robot_from_config(config: RobotConfig) -> Robot:
    if config.type == "my_robot":  # ← 添加这段
        from .my_robot import MyRobot
        return MyRobot(config)
    elif config.type == "koch_follower":
        from .koch_follower import KochFollower
        return KochFollower(config)
    # ... 其他机器人
```

---

## 5. 代码模板与示例

### 5.1 最小模板 (模拟机器人)

如果你只想快速测试，不需要真实硬件，可以使用 MockRobot:

```python
# 直接使用 MockRobot (已内置)
from lerobot.robots import RobotConfig
from lerobot.robots.utils import make_robot_from_config
from lerobot.cameras import CameraConfig

# 创建配置
config = RobotConfig.from_dict({
    "type": "mock_robot",
    "id": "test_robot",
    "n_motors": 6,
})

# 创建机器人
robot = make_robot_from_config(config)

# 使用
robot.connect()
obs = robot.get_observation()
robot.send_action({"motor_1.pos": 50.0})
robot.disconnect()
```

### 5.2 完整使用示例

```python
# 完整使用示例
from lerobot.robots import RobotConfig
from lerobot.robots.utils import make_robot_from_config
from lerobot.cameras import CameraConfig

# 1. 创建配置
config = RobotConfig.from_dict({
    "type": "my_robot",
    "id": "my_robot_01",
    "port": "/dev/ttyUSB0",
    "n_motors": 6,
    "motor_type": "dynamixel",
    "cameras": {
        "front_camera": {
            "type": "opencv",
            "width": 640,
            "height": 480,
            "fps": 30,
        }
    }
})

# 2. 创建机器人
robot = make_robot_from_config(config)

# 3. 连接
robot.connect(calibrate=True)

# 4. 循环操作
for _ in range(100):
    # 获取观察
    obs = robot.get_observation()
    
    # 假设从模型获取动作
    action = {"joint_1.pos": 50.0, "joint_2.pos": 30.0, ...}
    
    # 发送动作
    robot.send_action(action)

# 5. 断开
robot.disconnect()
```

---

## 6. 常见问题与调试

### Q1: 如何选择电机型号?

| 型号 | 通信协议 | 扭矩 | 价格 |
|------|----------|------|------|
| XL-330 | RS485 | 低 | $ |
| XL-430 | RS485 | 中 | $$ |
| XM-430 | RS485 | 中高 | $$ |
| RH-P12-RN | CAN | 高 | $$$ |

### Q2: 校准失败怎么办?

1. 检查电机 ID 是否正确
2. 检查串口权限: `sudo chmod 666 /dev/ttyUSB0`
3. 确认电机供电正常

### Q3: 如何调试?

```python
# 启用调试日志
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Q4: 支持哪些相机?

```python
# 方式 1: OpenCV USB 相机
CameraConfig(type="opencv", width=640, height=480, fps=30)

# 方式 2: RealSense
CameraConfig(type="realsense", width=640, height=480, fps=30)

# 方式 3: 网络相机 (ZMQ)
CameraConfig(type="zmq", ...)
```

---

## 📚 参考资源

- [GitHub 仓库](https://github.com/huggingface/lerobot)
- [官方文档](https://huggingface.co/docs/lerobot)
- [Koch 机械臂](https://github.com/AlexanderKoch-Koch/low_cost_robot)
- [Dynamixel 电机文档](https://emanual.robotis.com/)

---

*文档最后更新: 2026-02-24*
