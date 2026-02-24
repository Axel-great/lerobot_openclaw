# 信洲 USB 摄像头编号程序

用于 USB 摄像头固件更新和序列号写入的 Python 程序。

## 功能

- 固件更新 (通过 SFWriteTool)
- 序列号生成和写入 (通过 ChangeDeviceInfo)
- 摄像头功能测试
- 支持数据库/无数据库模式
- 批量处理支持

## 依赖

```bash
pip install opencv-python pymysql
```

## 使用方法

### 无数据库模式 (默认)

```bash
python usb_camera_programmer_simple.py
# 或批量
python usb_camera_programmer_simple.py --batch
```

### 数据库模式

```bash
# 使用本地数据库
python usb_camera_programmer_simple.py --db

# 使用远程数据库
python usb_camera_programmer_simple.py --db --host 192.168.1.100 --user root --password 123456
```

### 命令行参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--db` | 启用数据库模式 | 无数据库 |
| `--host` | 数据库地址 | localhost |
| `--port` | 数据库端口 | 3306 |
| `--user` | 数据库用户名 | root |
| `--password` | 数据库密码 | (空) |
| `--database` | 数据库名称 | camera_db |
| `--batch` | 批量模式 | 单个 |
| `--firmware` | 固件文件 | FIRMWARE_FILE |

## 数据库表结构

```sql
CREATE TABLE cameras (
    id INT AUTO_INCREMENT PRIMARY KEY,
    序列号 VARCHAR(50) NOT NULL,
    固件版本 VARCHAR(20),
    创建时间 DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

## 序列号规则

格式: `JYU2C-2083-YYMMNNN`

- YY: 年份后两位
- MM: 月份
- NNN: 当月序列号 (001-999)

### 无数据库模式
使用时间戳生成序号: `JYU2C-2083-YYMM{timestamp%1000}`

### 数据库模式
从数据库查询最大序号+1
