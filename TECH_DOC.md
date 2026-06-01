# BF6 Team Balancer - 技术文档

## 1. 系统架构

```
┌─────────────┐     ┌──────────────┐     ┌───────────────┐
│  Excel文件   │────▶│  extract.py  │────▶│  ui_prototype  │
│ (昵称/KD/KPM)│     │  解析+偏移    │     │  用户交互      │
└─────────────┘     └──────────────┘     └───────┬───────┘
                                                  │
                                                  ▼
┌─────────────┐     ┌──────────────┐     ┌───────────────┐
│  分队结果    │◀────│ algorithm.py │◀────│  history.py    │
│  均衡报告    │     │ 均衡/随机分配 │     │  历史记录存储   │
└─────────────┘     └──────────────┘     └───────────────┘
```

注: UI 直接将 extract_players() 的结果传给 load_players()，不经过 JSON 文件。
extract.py 的 CLI 模式可独立运行，输出 players.json。

## 2. 数据模型

### Player

| 字段 | 类型 | 说明 |
|---|---|---|
| name | str | 玩家昵称 |
| kd | float | K/D比（直接使用，无偏移） |
| kpm | float | 每分钟击杀数（已应用偏移） |
| _weighted_score | float | 加权得分（运行时计算） |

### Squad

| 字段 | 类型 | 说明 |
|---|---|---|
| members | list[Player] | 小队成员（最多4人） |
| avg_kd | property | 小队平均KD |
| avg_kpm | property | 小队平均KPM |

### Team

| 字段 | 类型 | 说明 |
|---|---|---|
| name | str | 阵营名称 |
| squads | list[Squad] | 已编成的小队列表 |
| _buffer | list[Player] | 待编组的临时缓冲区 |
| avg_kd | property | 阵营平均KD |
| avg_kpm | property | 阵营平均KPM |
| score | property | 阵营总加权分 |

## 3. 核心算法

### 3.1 加权得分

根据游戏模式对KD和KPM加权求和：

```
征服模式: score = KD × 0.7 + KPM × 0.3
突破模式: score = KD × 0.3 + KPM × 0.7
```

### 3.2 KPM偏移修正

小黑盒平台的KPM数据偏低，通过偏移系数修正：

```
KPM_adjusted = KPM_raw × offset (默认1.313)
```

推荐值1.313基于5组样本数据的平均偏差得出，用户可手动调整。

### 3.3 分配模式

系统支持两种分配模式：

#### 均衡模式（allocate_teams）

按实力加权的贪心分配：

```
1. 加载玩家 → 计算加权分
2. 处理自定义小队绑定（两人视为超级玩家，得分取均值）
3. 独立玩家按得分降序排列
4. ABAB抽取候补（首尾交替，自定义小队成员不参与）
5. 贪心分配阵营（每次把当前最弱的队塞最强的人）
6. 小队编成（每4人一组，不满的强制编队）
7. 生成均衡性报告
```

#### 随机模式（random_allocate）

纯随机打乱分配：

```
1. 加载玩家
2. 处理自定义小队绑定（仍生效，不能拆散）
3. 独立玩家随机打乱（random.shuffle）
4. 随机抽取候补（自定义小队成员不参与）
5. 剩余玩家与自定义小队混排后再次打乱
6. 轮流分配到两阵营（AABB交替）
7. 小队编成（每4人一组，不满的强制编队）
8. 生成均衡性报告（仅供参考）
```

### 3.4 候补抽取规则

- 均衡模式：从排序后的独立玩家首尾ABAB交替抽取
- 随机模式：从打乱后的独立玩家中按序抽取
- 自定义小队成员不参与抽取（不能拆散）
- 目标：双方人数相等且为4的倍数
- 最大候补数8人
- 计算公式：
  ```
  max_per_team = (total // 2 // 4) × 4
  active = max_per_team × 2
  reserves = total - active
  ```

### 3.5 贪心分配（均衡模式）

将自定义小队视为"得分=成员均分、占2槽位"的原子单位，与独立玩家混排后按得分降序处理：

```
for item in sorted_items:
    target = 当前总分更低的阵营
    if item是玩家:
        target.add_player(item)
    else:  # 自定义小队
        if target有足够槽位:
            target.add_players(item)
        else:
            另一个阵营.add_players(item)
```

### 3.6 小队编成

Player进入Team后暂存buffer，buffer满4人时自动编成Squad：

```
Team.add_player(player):
    buffer.append(player)
    if len(buffer) >= 4:
        squads.append(Squad(buffer))
        buffer.clear()
```

最后调用`flush_buffer()`将不满4人的buffer强制编队。

## 4. UI设计

### 4.1 页面流程

| 页面 | 功能 | 控件 | 跳过条件 |
|---|---|---|---|
| 1. 导入 | 选择Excel，预览数据 | 文件选择、偏移系数、数据表格 | - |
| 2. 分配模式 | 选择均衡/随机 | 两张大卡片（单选） | - |
| 3. 游戏模式 | 选择征服/突破 | 两张大卡片（单选） | 随机模式自动跳过 |
| 4. 自定义小队 | 绑定玩家对 | 下拉框选择、添加/删除 | - |
| 5. 结果 | 查看分队和分析 | 左右分栏表格、候补表格、告警 | - |
| 6. 历史记录 | 浏览过往分队记录 | 记录列表表格、详情区（左右分栏） | 未点击历史记录按钮时跳过 |
| 7. 操作 | 重新导入/分配/退出 | 三个大按钮 | - |

### 4.2 步骤指示器

- 6个圆形步骤指示器，对应6个主要步骤（历史页为中间页，无指示器）
- 已完成步骤：绿色
- 当前步骤：蓝色高亮
- 未来步骤：灰色
- 被跳过的步骤（随机模式下的游戏模式）：暗色 + 删除线

### 4.3 样式

- 5 套可选颜色主题（暗夜灰 / 深海蓝 / 墨绿 / 暗红 / 黑白纯色）
- 主题配置存储于 `%USERPROFILE%\Documents\BF6TeamBalancer\config.json`
- 全局样式表由 `build_stylesheet(theme)` 动态生成
- 字体：Microsoft YaHei UI（圆滑中文）
- 基础字号16px，标题26px
- 小队颜色区分：不同小队用不同灰度背景（跟随主题）

## 5. 打包

使用PyInstaller `--onedir`模式：

```bash
pyinstaller --noconfirm --onedir --noconsole \
    --name 'BF6TeamBalancer' \
    --add-data 'core;core' \
    --add-data 'extract.py;.' \
    ui_prototype.py
```

输出在`dist/BF6TeamBalancer/`目录，双击exe即可运行。

## 6. 边界情况处理

| 情况 | 处理方式 |
|---|---|
| 玩家数据缺失(mrli) | kd和kpm记为0，参与分配但权重低 |
| 人数非4倍数 | 候补人数自动调整，保证上场人数为4的倍数 |
| 自定义小队约束冲突 | UI层检测，提示"玩家已被绑定"或"不能绑定同一人" |
| 候补满8人 | 停止抽取，多余的人留在主力队伍 |
| 玩家数超过模式上限 | 征服最多64人(16队)，突破最多48人(12队) |

## 7. 已知限制

- 偏移系数推荐值基于5组样本，精度有限
- 贪心算法是局部最优，非全局最优解（均衡模式）
- 历史记录最多保存5条，自动淘汰最早的（详见 `history.py`）
- 打包体积较大（~200MB），因Anaconda环境包含冗余依赖
