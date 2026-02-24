# 信洲 USB 摄像头编号程序

用于 USB 摄像头固件更新和序列号写入的 Python 程序。

## 功能

- 固件更新 (通过 SFWriteTool)
- 序列号生成和写入 (通过 ChangeDeviceInfo)
- 摄像头功能测试
- 批量处理支持

## 依赖

```bash
pip install pyserial opencv-python pyusb pyautogui pywin32
```

## 使用方法

### 增强版 (推荐)

```bash
# 指定固件文件
python camera_programmer_enhanced.py -f "KD-SPCA2281B5+GC2083-1920x1080-30-15fps-F-N-Q65-XH-260128-NOMIC.bin"

# 批量处理
python camera_programmer_enhanced.py --count 10
```

### GUI 版本

```bash
python camera_programmer_gui.py
```

### 命令行版本

```bash
python camera_programmer.py --mode single
```

## SFWriteTool 操作流程

根据文档，SFWriteTool 需要按以下步骤操作：

1. **打开 SFWriteTool.exe**
2. **点击下方三个点** (菜单按钮)
3. **进入资源加载器**
4. **选择固件文件**:
   ```
   KD-SPCA2281B5+GC2083-1920x1080-30-15fps-F-N-Q65-XH-260128-NOMIC.bin
   ```
5. 等待固件更新完成

## 序列号规则

格式: `JYU2C-2083-YYMMNNN`

- YY: 年份后两位
- MM: 月份
- NNN: 当月序列号 (001-999)

## 操作流程

1. 启动程序
2. 插入摄像头
3. 程序自动:
   - 识别设备
   - 更新固件
   - 写入序列号
   - 测试功能
4. 拔出摄像头
5. 重复步骤 2-4

## 核验项

### 固件更新
- [x] Device 显示 "USB 2.0 Camera"
- [x] VID: 1BCF, PID: 2281
- [x] Log 显示 "Download complete"
- [x] Bcd 从 1103 变为 0128

### 序列号写入
- [x] Log 显示 "Update success"
- [x] iManufacturer = "JoyandAI"
- [x] iProduct = "JYU2C-2083"
- [x] iSerialNumber = 新序列号

### 功能测试
- [x] 支持 YUY2/MJPG 格式
- [x] 30 帧图像正常
- [x] 非全黑/全白

## 文件说明

```
usb_camera_programmer/
├── camera_programmer.py           # 命令行版本
├── camera_programmer_enhanced.py # 增强版 (推荐)
├── camera_programmer_gui.py      # GUI 版本
└── README.md                     # 说明文档
```

## 固件文件

```
KD-SPCA2281B5+GC2083-1920x1080-30-15fps-F-N-Q65-XH-260128-NOMIC.bin
```

## 注意事项

1. 需要 Windows 系统
2. 需要安装 SFWriteTool 和 ChangeDeviceInfo 工具
3. 需要管理员权限运行
4. 批量处理时需要数据库支持序列号查询
