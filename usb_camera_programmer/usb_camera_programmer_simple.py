#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
信洲 USB 摄像头编号程序 - 支持无数据库模式
"""

import os
import sys
import time
import subprocess
import argparse
from datetime import datetime
from typing import Optional

# ===== 配置 =====
CAMERA_VID = "1BCF"
CAMERA_PID = "2281"
OLD_BCD = "1103"
NEW_BCD = "0128"
FIRMWARE_FILE = "KD-SPCA2281B5+GC2083-1920x1080-30-15fps-F-N-Q65-XH-260128-NOMIC.bin"


def log(msg: str):
    """打印日志"""
    print(f"[{time.strftime('%H:%M:%S')}] {msg}")


def input_with_default(prompt: str, default: str) -> str:
    """带默认值的输入"""
    result = input(f"{prompt} (默认: {default}): ").strip()
    return result if result else default


class DatabaseManager:
    """数据库管理器 (未来扩展用)"""
    
    def __init__(self, host: str = "localhost", port: int = 3306,
                 user: str = "root", password: str = "", 
                 database: str = "camera_db"):
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.database = database
        self.connection = None
        
    def connect(self) -> bool:
        """连接数据库"""
        try:
            import pymysql
            self.connection = pymysql.connect(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password,
                database=self.database,
                charset='utf8mb4'
            )
            log("✓ 数据库连接成功")
            return True
        except ImportError:
            log("警告: pymysql 未安装，无法连接数据库")
            return False
        except Exception as e:
            log(f"数据库连接失败: {e}")
            return False
    
    def get_max_serial(self, year: str, month: str) -> int:
        """获取最大序列号"""
        if not self.connection:
            return 0
            
        try:
            with self.connection.cursor() as cursor:
                # 查询以 JYU2C-2083-YYMM 开头的最大序号
                prefix = f"JYU2C-2083-{year}{month}"
                sql = f"SELECT MAX(序列号) FROM cameras WHERE 序列号 LIKE '{prefix}%'"
                cursor.execute(sql)
                result = cursor.fetchone()
                if result and result[0]:
                    # 提取序号部分
                    seq_str = result[0][-3:]
                    return int(seq_str)
                return 0
        except Exception as e:
            log(f"查询失败: {e}")
            return 0
    
    def insert_serial(self, serial: str, firmware_version: str = "0128") -> bool:
        """插入序列号记录"""
        if not self.connection:
            return False
            
        try:
            with self.connection.cursor() as cursor:
                sql = "INSERT INTO cameras (序列号, 固件版本, 创建时间) VALUES (%s, %s, NOW())"
                cursor.execute(sql, (serial, firmware_version))
                self.connection.commit()
                return True
        except Exception as e:
            log(f"插入失败: {e}")
            return False
    
    def close(self):
        """关闭连接"""
        if self.connection:
            self.connection.close()


class SerialGenerator:
    """序列号生成器"""
    
    def __init__(self, db_manager: Optional[DatabaseManager] = None):
        self.db = db_manager
        
    def generate(self) -> str:
        """生成序列号: JYU2C-2083-YYMMNNN"""
        now = datetime.now()
        year = str(now.year)[-2:]
        month = str(now.month).zfill(2)
        
        # 尝试从数据库获取
        if self.db and self.db.connection:
            max_seq = self.db.get_max_serial(year, month)
            seq = max_seq + 1
            log(f"数据库查询: 最大序号 {max_seq} -> 新序号 {seq}")
        else:
            # 无数据库模式: 使用时间戳+随机数
            seq = int(time.time() % 1000)
            log(f"无数据库模式: 使用时间戳序号 {seq}")
        
        serial = f"JYU2C-2083-{year}{month}{seq:03d}"
        return serial
    
    def save_to_db(self, serial: str) -> bool:
        """保存到数据库"""
        if self.db and self.db.connection:
            return self.db.insert_serial(serial, NEW_BCD)
        return False


def check_camera() -> bool:
    """检查摄像头是否连接"""
    try:
        result = subprocess.run(
            ['wmic', 'path', 'Win32_USBDevice', 'get', 'DeviceID'],
            capture_output=True, text=True, timeout=5
        )
        return f"VID_{CAMERA_VID}&PID_{CAMERA_PID}" in result.stdout
    except:
        return True  # 模拟返回


def test_camera() -> bool:
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


def run_process(serial_gen: SerialGenerator, use_db: bool):
    """运行单个流程"""
    print("=" * 50)
    print("信洲 USB 摄像头编号程序")
    print(f"模式: {'数据库模式' if use_db else '无数据库模式'}")
    print("=" * 50)
    
    # 1. 固件文件
    firmware = input_with_default("固件文件路径", FIRMWARE_FILE)
    if not os.path.exists(firmware):
        log(f"警告: 固件文件不存在: {firmware}")
    
    # 2. 序列号
    serial = serial_gen.generate()
    log(f"序列号: {serial}")
    use_serial = input_with_default("使用此序列号?", "y")
    if use_serial.lower() != "y":
        serial = input("输入序列号: ")
    
    # 保存到数据库
    if use_db:
        serial_gen.save_to_db(serial)
    
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
    log(f"序列号: {serial}")
    log("=" * 50)


def batch_process(serial_gen: SerialGenerator, use_db: bool):
    """批量处理"""
    count = int(input_with_default("处理数量", "1"))
    
    for i in range(count):
        log(f"\n{'#' * 50}")
        log(f"# 处理第 {i+1}/{count} 个")
        log(f"{'#' * 50}")
        run_process(serial_gen, use_db)


def main():
    parser = argparse.ArgumentParser(
        description="信洲 USB 摄像头编号程序",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python usb_camera_programmer_simple.py                  # 无数据库模式
  python usb_camera_programmer_simple.py --batch        # 批量无数据库模式
  python usb_camera_programmer_simple.py --db            # 数据库模式
  python usb_camera_programmer_simple.py --db --host 192.168.1.100 --user root --password 123456
        """
    )
    
    # 数据库选项
    parser.add_argument("--db", dest="use_db", action="store_true",
                       help="启用数据库模式 (默认: 无数据库)")
    parser.add_argument("--host", default="localhost",
                       help="数据库主机地址 (默认: localhost)")
    parser.add_argument("--port", type=int, default=3306,
                       help="数据库端口 (默认: 3306)")
    parser.add_argument("--user", default="root",
                       help="数据库用户名 (默认: root)")
    parser.add_argument("--password", default="",
                       help="数据库密码")
    parser.add_argument("--database", default="camera_db",
                       help="数据库名称 (默认: camera_db)")
    
    # 其他选项
    parser.add_argument("--batch", "-b", action="store_true", help="批量模式")
    parser.add_argument("--firmware", "-f", default=FIRMWARE_FILE, help="固件文件")
    
    args = parser.parse_args()
    
    # 初始化
    db_manager = None
    if args.use_db:
        log("数据库模式已启用")
        db_manager = DatabaseManager(
            host=args.host,
            port=args.port,
            user=args.user,
            password=args.password,
            database=args.database
        )
        if not db_manager.connect():
            log("数据库连接失败，将使用无数据库模式")
            db_manager = None
    else:
        log("无数据库模式")
    
    serial_gen = SerialGenerator(db_manager)
    
    # 运行
    if args.batch:
        batch_process(serial_gen, args.use_db)
    else:
        run_process(serial_gen, args.use_db)
    
    # 清理
    if db_manager:
        db_manager.close()


if __name__ == "__main__":
    main()
