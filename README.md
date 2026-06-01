# BF6 Team Balancer

战地风云6服务器内战分队工具。根据玩家的KD和KPM数据，自动均衡分配阵营和小队，也支持纯随机分配。

## 功能

- 从Excel文件导入玩家数据（昵称、KD、KPM）
- KPM偏移修正（默认系数1.313，可手动调整）
- **两种分配模式：均衡（按实力）/ 随机（纯随机）**
- 支持两种游戏模式：征服（侧重KD）/ 突破（侧重KPM）
- 自定义小队绑定（两人绑定到同一阵营）
- 贪心算法均衡分配阵营（均衡模式）
- 候补队伍自动抽取（首尾ABAB）
- 分队结果 + 均衡性分析报告
- 5 套颜色主题（暗夜灰 / 深海蓝 / 墨绿 / 暗红 / 黑白纯色），选择自动保存

## 使用方法

### 方式一：直接运行exe

1. 打开 `dist\BF6TeamBalancer\BF6TeamBalancer.exe`
2. 按界面提示操作：导入Excel → 选择分配模式 → 设置绑定 → 查看结果

### 方式二：源码运行

```bash
pip install PyQt5 openpyxl
python ui_prototype.py
```

## Excel格式要求

固定三列，无表头或表头行自动跳过：

| 列1 | 列2 | 列3 |
|---|---|---|
| 昵称 | KD | KPM |

示例：
```
阿金    3.47    2.31
叁叁    0.20    0.10
```

## 项目结构

```
bf6-team-balancer/
├── ui_prototype.py      # GUI main (PyQt5)
├── extract.py           # Excel parser
├── history.py           # History & config storage
├── test_algorithm.py    # Algorithm tests (pytest)
├── core/
│   ├── __init__.py
│   └── algorithm.py     # Core allocation algorithm
├── requirements.txt     # Runtime dependencies
├── requirements-dev.txt # Dev dependencies (pyinstaller, pytest)
├── CHANGELOG.md         # Version changelog
├── README.md            # This file
└── TECH_DOC.md          # Technical documentation
```

## 技术栈

- Python 3.9+
- PyQt5（GUI）
- openpyxl（Excel解析）
- PyInstaller（打包）
