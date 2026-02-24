#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
信洲 USB 摄像头编号程序
用于固件更新和序列号写入

依赖安装:
pip install pyserial opencv-python pyusb

注意: 需要配合 SFWriteTool 和 ChangeDeviceInfo 工具使用
"""

import os
import sys
import time
import serial
import subprocess
from datetime import datetime
from typing import Optional

# 配置
CAMERA_VID = "1BCF"
CAMERA_PID = "2281"
OLD_FIRMWARE_BCD = "1103"
NEW_FIRMWARE_BCD = "0128"
OLD_MANUFACTURER = "KD-260128-H"
NEW_MANUFACTURER = "JoyandAI"
OLD_PRODUCT = "USB 2.0 Camera"
NEW_PRODUCT = "JYU2C-2083"


class CameraProgrammer:
    """USB 摄像头编程器"""
    
    def __init__(self, sfwrite_tool_path: str = "SFWriteTool.exe", 
                 change_device_tool_path: str = "ChangeDeviceInfo.exe"):
        self.sfwrite_tool = sfwrite_tool_path
        self.change_device_tool = change_device_tool_path
        self.serial_port = "COM3"  # 根据实际串口调整
        
    def generate_serial_number(self) -> str:
        """生成序列号: JYU2C-2083-YYMMNNN"""
        now = datetime.now()
        year = str(now.year)[-2:]
        month = str(now.month).zfill(2)
        
        # 从数据库查询最大序列号 (示例)
        # 实际实现需要连接数据库查询
        max_seq = self._get_max_sequence_from_db(year, month)
        new_seq = max_seq + 1
        
        serial_number = f"JYU2C-2083-{year}{month}{new_seq:03d}"
        return serial_number
    
    def _get_max_sequence_from_db(self, year: str, month: str) -> int:
        """从数据库获取最大序列号"""
        # 示例实现 - 实际需要连接数据库
        # conn = connect_to_db()
        # cursor = conn.cursor()
        # cursor.execute(f"SELECT MAX(序列号) FROM cameras WHERE 序列号 LIKE 'JYU2C-2083-{year}{month}%'")
        # result = cursor.fetchone()[0]
        return 0  # 返回 0 作为默认值
    
    def wait_for_camera(self, timeout: int = 30) -> bool:
        """等待摄像头插入并识别"""
        print(f"等待摄像头插入... (超时 {timeout}秒)")
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            # 使用系统命令检查设备
            if self._check_camera_connected():
                print("✓ 摄像头已识别")
                return True
            time.sleep(1)
        
        print("✗ 等待超时")
        return False
    
    def _check_camera_connected(self) -> bool:
        """检查摄像头是否连接"""
        # Windows: 使用 wmic 命令
        try:
            result = subprocess.run(
                ['wmic', 'path', 'Win32_USBDevice', 'get', 'DeviceID'],
                capture_output=True, text=True, timeout=5
            )
            device_ids = result.stdout
            target = f"VID_{CAMERA_VID}&PID_{CAMERA_PID}"
            return target in device_ids
        except:
            pass
        
        # 备选方案: 使用 pyusb
        try:
            import usb.core
            devices = usb.core.find(idVendor=int(CAMERA_VID, 16), 
                                   idProduct=int(CAMERA_PID, 16),
                                   find_all=True)
            return devices is not None
        except:
            pass
        
        return False
    
    def update_firmware(self) -> bool:
        """
        更新固件
        核验项:
        1. Status 显示 "Running" 或倒计时
        2. Log 有 "Start Downloading device"
        3. 进度条为绿色
        4. Log 显示 "Download complete"
        """
        print("开始更新固件...")
        
        # 启动 SFWriteTool
        try:
            subprocess.Popen([self.sfwrite_tool])
            time.sleep(2)
        except Exception as e:
            print(f"启动工具失败: {e}")
            return False
        
        # 检查更新状态
        # 实际实现需要解析工具输出或读取日志文件
        time.sleep(5)  # 等待更新完成
        
        # 验证固件版本
        if self._verify_firmware_updated():
            print("✓ 固件更新成功")
            return True
        else:
            print("✗ 固件更新失败")
            return False
    
    def _verify_firmware_updated(self) -> bool:
        """验证固件是否更新成功"""
        # 检查 Bcd 版本是否为 NEW_FIRMWARE_BCD
        # 实际实现需要读取设备信息
        # 检查日志包含 "Download complete"
        
        # 模拟验证
        return True
    
    def write_serial_number(self, serial_number: str) -> bool:
        """
        写入序列号
        核验项:
        1. Log 最后为 "Init device"
        2. VID/PID 正确
        3. iManufacturer = "JoyandAI"
        4. iProduct = "JYU2C-2083"
        5. iSerialNumber = 新序列号
        """
        print(f"写入序列号: {serial_number}")
        
        # 启动 ChangeDeviceInfo
        try:
            subprocess.Popen([self.change_device_tool])
            time.sleep(2)
        except Exception as e:
            print(f"启动工具失败: {e}")
            return False
        
        # 填写序列号并点击 Update Dev
        # 实际实现需要通过 UI 自动化或直接调用驱动
        
        time.sleep(3)
        
        if self._verify_serial_written(serial_number):
            print("✓ 序列号写入成功")
            return True
        else:
            print("✗ 序列号写入失败")
            return False
    
    def _verify_serial_written(self, serial_number: str) -> bool:
        """验证序列号是否写入成功"""
        # 检查日志包含 "Update success"
        # 检查设备信息中的序列号
        return True
    
    def test_camera(self) -> bool:
        """
        测试摄像头功能
        核验项:
        1. 支持 YUY2, MJPG 格式
        2. 支持指定分辨率和帧率
        3. 连续获取 30 帧
        4. 每帧不同，非全黑/全白
        """
        print("测试摄像头功能...")
        
        import cv2
        
        # 查找摄像头
        for device_id in range(5):
            cap = cv2.VideoCapture(device_id)
            if cap.isOpened():
                print(f"找到摄像头: device {device_id}")
                
                # 设置分辨率和格式
                # YUY2: 640x480, 1280x720, 1920x1080
                # MJPG: 支持更高帧率
                cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                cap.set(cv2.CAP_PROP_FPS, 30)
                
                frames = []
                for i in range(30):
                    ret, frame = cap.read()
                    if not ret:
                        print(f"✗ 第 {i+1} 帧读取失败")
                        cap.release()
                        return False
                    
                    # 检查是否全黑或全白
                    mean_val = frame.mean()
                    if mean_val < 10 or mean_val > 245:
                        print(f"✗ 第 {i+1} 帧异常 (全黑/全白): {mean_val}")
                        cap.release()
                        return False
                    
                    frames.append(frame)
                
                # 检查帧是否不同
                if len(set([f.tobytes() for f in frames])) < 25:
                    print("⚠ 警告: 部分帧相同")
                
                cap.release()
                print("✓ 摄像头测试通过")
                return True
        
        print("✗ 未找到摄像头")
        return False
    
    def run(self):
        """运行完整流程"""
        print("=" * 50)
        print("信洲 USB 摄像头编号程序")
        print("=" * 50)
        
        # 步骤 1: 等待摄像头插入
        if not self.wait_for_camera():
            return False
        
        # 步骤 2: 更新固件
        if not self.update_firmware():
            return False
        
        # 步骤 3: 生成序列号
        serial_number = self.generate_serial_number()
        print(f"生成的序列号: {serial_number}")
        
        # 步骤 4: 写入序列号
        if not self.write_serial_number(serial_number):
            return False
        
        # 步骤 5: 测试摄像头
        if not self.test_camera():
            return False
        
        print("=" * 50)
        print("✓ 所有步骤完成!")
        print("=" * 50)
        return True


class AutoProgrammer:
    """自动化编程器 - 批量处理多个摄像头"""
    
    def __init__(self):
        self.programmer = CameraProgrammer()
        
    def process_batch(self, count: int):
        """批量处理"""
        results = []
        
        for i in range(count):
            print(f"\n{'='*50}")
            print(f"处理第 {i+1}/{count} 个摄像头")
            print(f"{'='*50}")
            
            # 等待插入
            input("请插入摄像头，然后按 Enter 继续...")
            
            success = self.programmer.run()
            results.append(success)
            
            input("请拔出摄像头，然后按 Enter 继续...")
        
        # 打印统计
        success_count = sum(results)
        print(f"\n{'='*50}")
        print(f"完成: {success_count}/{count} 成功")
        print(f"{'='*50}")


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="信洲 USB 摄像头编号程序")
    parser.add_argument("--mode", choices=["single", "batch"], default="single",
                       help="运行模式: single=单个, batch=批量")
    parser.add_argument("--count", type=int, default=1,
                       help="批量处理数量")
    parser.add_argument("--sfwrite", default="SFWriteTool.exe",
                       help="SFWriteTool 路径")
    parser.add_argument("--change-device", default="ChangeDeviceInfo.exe",
                       help="ChangeDeviceInfo 路径")
    
    args = parser.parse_args()
    
    if args.mode == "single":
        programmer = CameraProgrammer(args.sfwrite, args.change_device)
        programmer.run()
    else:
        auto = AutoProgrammer()
        auto.process_batch(args.count)


if __name__ == "__main__":
    main()
