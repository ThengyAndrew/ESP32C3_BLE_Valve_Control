# ESP32-C3 电磁阀 BLE 对接文档

## 1. 功能概述

ESP32-C3 作为 BLE 外设运行。PC 作为 BLE 中心设备连接 ESP32-C3 后，可以：

- 向命令 Characteristic 写入 `TOGGLE`，翻转 GPIO10 输出电平。
- 读取状态 Characteristic，获取当前 GPIO10 状态：`LOW` 或 `HIGH`。

ESP32-C3 上电后 GPIO10 固定初始化为低电平 `LOW`。

## 2. 蓝牙信息

| 项目 | 值 |
| --- | --- |
| BLE 设备名 | `ESP32C3_VALVE_CTRL` |
| BLE 角色 | Peripheral / GATT Server |
| PC 角色 | Central / GATT Client |
| 控制引脚 | GPIO10 |
| 默认状态 | `LOW` |

ESP32-C3 仅支持 BLE，不支持经典蓝牙 SPP 串口。本方案使用 BLE GATT。

## 3. GATT 定义

### Service

| 项目 | 值 |
| --- | --- |
| Service UUID | `7b7d0001-2f4a-4f3d-9b4a-6a9d7f3c1000` |

### Command Characteristic

| 项目 | 值 |
| --- | --- |
| Characteristic UUID | `7b7d0002-2f4a-4f3d-9b4a-6a9d7f3c1000` |
| 属性 | `Write`, `Write Without Response` |
| 编码 | UTF-8 / ASCII 字符串 |

PC 写入以下命令：

| 写入内容 | 作用 |
| --- | --- |
| `TOGGLE` | 翻转 GPIO10 电平，并保持新状态 |

命令大小写不敏感，首尾空白会被忽略。例如 `toggle`、`TOGGLE\n` 都会被识别。

未定义命令会被忽略，不改变 GPIO10 状态。

### State Characteristic

| 项目 | 值 |
| --- | --- |
| Characteristic UUID | `7b7d0003-2f4a-4f3d-9b4a-6a9d7f3c1000` |
| 属性 | `Read` |
| 编码 | UTF-8 / ASCII 字符串 |

PC 读取结果：

| 读取内容 | 含义 |
| --- | --- |
| `LOW` | GPIO10 当前为低电平 |
| `HIGH` | GPIO10 当前为高电平 |

## 4. 典型 PC 端流程

1. 扫描 BLE 设备，找到设备名 `ESP32C3_VALVE_CTRL`。
2. 连接该设备。
3. 查找 Service UUID `7b7d0001-2f4a-4f3d-9b4a-6a9d7f3c1000`。
4. 如需翻转电磁阀控制电平，向 Command Characteristic 写入字符串 `TOGGLE`。
5. 如需确认当前状态，读取 State Characteristic。
6. 断开连接后，ESP32-C3 会继续广播，允许 PC 再次连接。

## 5. Python 最小示例

仓库内提供 `pc_toggle_valve.py`。该脚本会连接 ESP32-C3，写入一次 `TOGGLE`，然后读取并打印 GPIO10 当前状态。

安装依赖：

```bash
pip install bleak
```

运行：

```bash
python pc_toggle_valve.py
```

## 6. Arduino IDE 使用说明

1. 安装 ESP32 Arduino 开发板支持包。
2. 开发板选择支持 ESP32-C3 的板型，例如 `XIAO_ESP32C3` 或对应实际开发板。
3. 打开 `ESP32C3_BLE_Valve_Control.ino`。
4. 编译并烧录。
5. 上电后 GPIO10 初始输出低电平。

## 7. 硬件注意事项

GPIO10 只能输出逻辑电平，不能直接驱动电磁阀线圈。

建议使用 MOSFET、三极管或继电器模块驱动电磁阀，并在线圈两端加续流二极管。ESP32-C3 与驱动电路需要共地。
