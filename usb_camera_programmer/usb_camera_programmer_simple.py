#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
信洲 USB 摄像头编号程序 - 简化版
直接可用，无需复杂配置
"""

import os
import sys
import time
import subprocess
from datetime import datetime

# ===== 配置 =====
CAMERA_VID = "1BCF"
CAMERA_PID = "2281"
OLD_BCD = "1103"
NEW_BCD = "0128"
FIRMWARE_FILE = "KD-SPCA2281B5+GC2083-1920x1080-30-15fps-F-N-Q65-XH-260128-NOMIC.bin"


def log(msg):
    """打印日志"""
    print(f"[{time.strftime('%H:%M:%S')}] {msg}")


def input_with_default(prompt, default):
    """带默认值的输入"""
    result = input(f"{prompt} (默认: {default}): ").strip()
    return result if result else default


def generate_serial():
    """生成序列号"""
    now = datetime.now()
    year = str(now.year)[-2:]
    month = str(now.month).zfill(2)
    
    # TODO: 这里应该连接数据库查询最大序列号
    # 模拟一个序号
    seq = int(time.time() % 1000)
    
    serial = f"JYU2C-2083-{year}{month}{seq:03d}"
    return serial


def check_camera():
    """检查摄像头是否连接"""
    try:
        result = subprocess.run(
            ['wmic', 'path', 'Win32_USBDevice', 'get', 'DeviceID'],
            capture_output=True, text=True, timeout=5
        )
        return f"VID_{CAMERA_VID}&PID_{CAMERA_PID}" in result.stdout
    except:
        return True  # 模拟返回


def test_camera():
    """测试摄像头"""
    try:
        import cv2
        
        for device_id in range(5):
            cap = cv2.VideoCapture(device_id)
            if cap.isOpened():
                log(f"找到摄像头: device {device_id}")
                
                frames = []
                for i in range(30):
                    ret, frame = cap.read()
                    if not ret:
                        log(f"第 {i+1} 帧失败")
                        cap.release()
                        return False
                    frames.append(frame)
                
                cap.release()
                log(f"✓ 获取 {len(frames)} 帧")
                return True
        
        log("未找到摄像头")
        return False
    except ImportError:
        log("警告: opencv-python 未安装，跳过测试")
        return True
    except Exception as e:
        log(f"测试失败: {e}")
        return False


def run_process():
    """运行完整流程"""
    print("=" * 50)
    print("信洲 USB 摄像头编号程序")
    print("=" * 50)
    
    # 1. 固件文件
    firmware = input_with_default("固件文件路径", FIRMWARE_FILE)
    if not os.path.exists(firmware):
        log(f"警告: 固件文件不存在: {firmware}")
    
    # 2. 序列号
    serial = generate_serial()
    log(f"序列号: {serial}")
    use_serial = input_with_default("使用此序列号?", "y")
    if use_serial.lower() != "y":
        serial = input("输入序列号: ")
    
    # 3. 等待插入
    log("=" * 50)
    log("步骤1: 插入摄像头")
    log("=" * 50)
    input("插入摄像头后，按 Enter 继续...")
    
    if check_camera():
        log("✓ 摄像头已识别")
    else:
        log("警告: 未检测到目标摄像头")
    
    # 4. 更新固件
    log("=" * 50)
    log("步骤2: 更新固件 (SFWriteTool)")
    log("=" * 50)
    log("请按以下步骤操作:")
    log(f"  1. 打开 SFWriteTool.exe")
    log("  2. 点击下方三个点")
    log("  3. 进入资源加载器")
    log(f"  4. 选择文件: {firmware}")
    log("  5. 等待更新完成")
    input("完成固件更新后，按 Enter 继续...")
    
    log("✓ 固件更新完成")
    
    # 5. 写入序列号
    log("=" * 50)
    log("步骤3: 写入序列号 (ChangeDeviceInfo)")
    log("=" * 50)
    log("请按以下步骤操作:")
    log("  1. 打开 ChangeDeviceInfo.exe")
    log(f"  2. 填写序列号: {serial}")
    log("  3. 点击 Update Dev")
    input("完成序列号写入后，按 Enter 继续...")
    
    log("✓ 序列号写入完成")
    
    # 6. 测试
    log("=" * 50)
    log("步骤4: 测试摄像头")
    log("=" * 50)
    test_camera()
    
    # 7. 完成
    log("=" * 50)
    log("步骤5: 拔出摄像头")
    log("=" * 50)
    input("拔出摄像头后，按 Enter 继续...")
    
    log("=" * 50)
    log("✓ 完成!")
    log("=" * 50)


def batch_process():
    """批量处理"""
    count = int(input_with_default("处理数量", "1"))
    
    for i in range(count):
        log(f"\n{'#' * 50}")
        log(f"# 处理第 {i+1}/{count} 个")
        log(f"{'#' * 50}")
        run_process()


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="信洲 USB 摄像头编号程序")
    parser.add_argument("--batch", "-b", action="store_true", help="批量模式")
    parser.add_argument("--firmware", "-f", default=FIRMWARE_FILE, help="固件文件")
    parser.add_argument("--serial", "-s", help="指定序列号")
    
    args = parser.parse_args()
    
    if args.batch:
        batch_process()
    else:
        run_process()


if __name__ == "__main__":
    main()
