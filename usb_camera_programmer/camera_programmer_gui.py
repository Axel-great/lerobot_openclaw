#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
USB 摄像头编号程序 - GUI 版本
使用 Tkinter 构建图形界面
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
import time
from datetime import datetime
from typing import Optional

# 配置常量
CAMERA_VID = "1BCF"
CAMERA_PID = "2281"
OLD_FIRMWARE_BCD = "1103"
NEW_FIRMWARE_BCD = "0128"


class CameraProgrammerGUI:
    """GUI 应用程序"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("信洲 USB 摄像头编号程序")
        self.root.geometry("800x600")
        
        # 状态变量
        self.is_running = False
        self.current_step = ""
        
        self._create_widgets()
        
    def _create_widgets(self):
        """创建界面组件"""
        
        # 标题
        title_label = tk.Label(
            self.root, 
            text="信洲 USB 摄像头编号程序", 
            font=("Arial", 18, "bold")
        )
        title_label.pack(pady=10)
        
        # 配置区域
        config_frame = ttk.LabelFrame(self.root, text="配置", padding=10)
        config_frame.pack(fill="x", padx=10, pady=5)
        
        # SFWriteTool 路径
        ttk.Label(config_frame, text="SFWriteTool 路径:").grid(row=0, column=0, sticky="w")
        self.sfwrite_path = tk.StringVar(value="SFWriteTool.exe")
        ttk.Entry(config_frame, textvariable=self.sfwrite_path, width=40).grid(row=0, column=1, padx=5)
        
        # ChangeDeviceInfo 路径
        ttk.Label(config_frame, text="ChangeDeviceInfo 路径:").grid(row=1, column=0, sticky="w")
        self.change_device_path = tk.StringVar(value="ChangeDeviceInfo.exe")
        ttk.Entry(config_frame, textvariable=self.change_device_path, width=40).grid(row=1, column=1, padx=5)
        
        # 序列号输入
        ttk.Label(config_frame, text="序列号:").grid(row=2, column=0, sticky="w")
        self.serial_number = tk.StringVar()
        ttk.Entry(config_frame, textvariable=self.serial_number, width=40).grid(row=2, column=1, padx=5)
        ttk.Button(config_frame, text="生成", command=self.generate_serial).grid(row=2, column=2, padx=5)
        
        # 核验信息显示区域
        verify_frame = ttk.LabelFrame(self.root, text="设备信息核验", padding=10)
        verify_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # 设备信息
        info_text = (
            "【目标设备】\n"
            f"  VID: {CAMERA_VID}\n"
            f"  PID: {CAMERA_PID}\n"
            f"  旧固件版本: {OLD_FIRMWARE_BCD}\n"
            f"  新固件版本: {NEW_FIRMWARE_BCD}\n\n"
            "【序列号格式】\n"
            "  JYU2C-2083-YYMMNNN\n"
            "  YY = 年份后两位\n"
            "  MM = 月份\n"
            "  NNN = 当月序列号\n\n"
            "【操作流程】\n"
            "  1. 点击开始后插入摄像头\n"
            "  2. 自动更新固件\n"
            "  3. 自动写入序列号\n"
            "  4. 自动测试摄像头\n"
        )
        self.info_label = tk.Label(verify_frame, text=info_text, justify="left", anchor="nw")
        self.info_label.pack(fill="both", expand=True)
        
        # 日志区域
        log_frame = ttk.LabelFrame(self.root, text="日志", padding=10)
        log_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=10, wrap=tk.WORD)
        self.log_text.pack(fill="both", expand=True)
        
        # 按钮区域
        btn_frame = ttk.Frame(self.root, padding=10)
        btn_frame.pack(fill="x")
        
        self.start_btn = ttk.Button(btn_frame, text="开始", command=self.start_process)
        self.start_btn.pack(side="left", padx=5)
        
        self.stop_btn = ttk.Button(btn_frame, text="停止", command=self.stop_process, state="disabled")
        self.stop_btn.pack(side="left", padx=5)
        
        self.clear_btn = ttk.Button(btn_frame, text="清空日志", command=self.clear_log)
        self.clear_btn.pack(side="left", padx=5)
        
        # 状态栏
        self.status_var = tk.StringVar(value="就绪")
        self.status_label = tk.Label(self.root, textvariable=self.status_var, relief="sunken", anchor="w")
        self.status_label.pack(fill="x")
        
    def log(self, message: str):
        """添加日志"""
        timestamp = time.strftime("%H:%M:%S")
        self.log_text.insert("end", f"[{timestamp}] {message}\n")
        self.log_text.see("end")
        
    def clear_log(self):
        """清空日志"""
        self.log_text.delete("1.0", "end")
        
    def set_status(self, status: str):
        """设置状态"""
        self.status_var.set(status)
        
    def generate_serial(self):
        """生成序列号"""
        now = datetime.now()
        year = str(now.year)[-2:]
        month = str(now.month).zfill(2)
        
        # 实际实现需要查询数据库
        # 这里使用随机数模拟
        import random
        seq = random.randint(1, 999)
        
        serial = f"JYU2C-2083-{year}{month}{seq:03d}"
        self.serial_number.set(serial)
        self.log(f"生成序列号: {serial}")
        
    def start_process(self):
        """开始处理流程"""
        if not self.serial_number.get():
            messagebox.showwarning("警告", "请先生成或输入序列号")
            return
        
        self.is_running = True
        self.start_btn.config(state="disabled")
        self.stop_btn.config(state="normal")
        
        # 在后台线程运行
        thread = threading.Thread(target=self._run_process, daemon=True)
        thread.start()
        
    def stop_process(self):
        """停止处理"""
        self.is_running = False
        self.set_status("已停止")
        self.start_btn.config(state="normal")
        self.stop_btn.config(state="disabled")
        
    def _run_process(self):
        """后台运行处理流程"""
        try:
            # 步骤 1: 等待摄像头插入
            self.set_status("等待摄像头插入...")
            self.log("请插入摄像头...")
            self.log("提示: 在 SFWriteTool 中确认设备信息")
            
            # 模拟等待
            time.sleep(2)
            
            if not self.is_running:
                return
                
            # 步骤 2: 更新固件
            self.set_status("更新固件中...")
            self.log("开始更新固件...")
            
            # 模拟固件更新过程
            for i in range(3, 0, -1):
                if not self.is_running:
                    return
                self.log(f"倒计时: {i}...")
                time.sleep(1)
            
            self.log("固件更新完成")
            self.log(f"固件版本: {OLD_FIRMWARE_BCD} -> {NEW_FIRMWARE_BCD}")
            
            if not self.is_running:
                return
            
            # 步骤 3: 写入序列号
            self.set_status("写入序列号中...")
            self.log(f"写入序列号: {self.serial_number.get()}")
            time.sleep(1)
            
            # 步骤 4: 测试摄像头
            self.set_status("测试摄像头中...")
            self.log("开始测试摄像头...")
            
            # 模拟测试
            for i in range(1, 31):
                if not self.is_running:
                    return
                if i % 10 == 0:
                    self.log(f"已获取 {i} 帧...")
                time.sleep(0.1)
            
            self.log("摄像头测试通过")
            
            # 完成
            self.set_status("完成!")
            self.log("✓ 所有步骤完成!")
            messagebox.showinfo("成功", "摄像头编号完成!")
            
        except Exception as e:
            self.log(f"错误: {e}")
            self.set_status("错误")
            messagebox.showerror("错误", str(e))
            
        finally:
            self.start_btn.config(state="normal")
            self.stop_btn.config(state="disabled")


def main():
    """主函数"""
    root = tk.Tk()
    app = CameraProgrammerGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
