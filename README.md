# ACPack

重写自上游仓库[misividkoukou/ACPack](https://github.com/misividkoukou/ACPack)，依靠Beet数据包框架，完全由Python重写。

![Minecraft](https://img.shields.io/badge/Minecraft-26.3-3C8527)
![Python](https://img.shields.io/badge/Python-3.14-3776AB?logo=python&logoColor=white)
![Beet](https://img.shields.io/badge/beet-0.121.2-6E4AFF)
![License](https://img.shields.io/badge/license-MPL--2.0-blueviolet)

> 纯服务端数据包：玩家无需安装任何模组或客户端资源包，进服即生效。

---

## 特性

| 模块 | 说明 |
|---|---|
| **玩家统计** | 死亡、挖掘、锄头、容器、交易、时长、加入次数、放置数量八类数据，带全局汇总与侧边栏轮播 |
| **控制面板** | 一条指令打开的功能中枢，按钮式操作，支持计分板显示模式、小贴士开关、扫地机、粒子菜单 |
| **小贴士** | 多条随机提示，每 5 分钟向开启的玩家播报一条，可按玩家独立开关 |
| **扫地机** | 玩家自助启停的掉落物清扫，15 秒倒计时、全员播报、中途可取消 |
| **新手引导** | 首次进入自动播报欢迎与使用指引，并初始化个人设置 |
| **粒子装饰** | 7 种脚下粒子效果，普通效果人人可用，特殊效果按队伍/白名单解锁 |
| **配方与战利品** | 7 个自定义配方 + 猪灵以物易物重制（附魔书、重锤核心、风弹等） |

## 玩家指令

所有功能通过 `/trigger` 触发，无需权限等级：

| 指令 | 作用 |
|---|---|
| `/trigger trigger set 1` | 打开功能控制面板 |
| `/trigger trigger set 2` | 开启小贴士 |
| `/trigger trigger set 3` | 关闭小贴士 |
| `/trigger trigger set 4` | 取消即将出击的扫地机 |
| `/trigger trigger set 5` | 启动扫地机（15 秒后清扫） |
| `/trigger trigger set 6` | 打开计分板显示设置 |
| `/trigger trigger set 7` | 自杀 / 脱离卡死（不计入死亡统计） |
| `/trigger trigger set 8` | 打开粒子效果菜单 |
| `/trigger trigger set 10`–`20` | 切换计分板显示模式 |

### 计分板显示模式

| 值 | 模式 | 值 | 模式 |
|---|---|---|---|
| 0 | 关闭 | 6 | 固定：村民交易次数 |
| 1 | 普通轮播（默认） | 7 | 固定：游戏时长 |
| 2 | 固定：死亡量 | 8 | 录屏模式（固定服务器信息） |
| 3 | 固定：挖掘量 | 9 | 固定：加入次数 |
| 4 | 固定：锄头使用量 | 10 | 固定：放置数量 |
| 5 | 固定：容器打开次数 | | |

### 粒子效果

| 值 | 效果 | 解锁条件 |
|---|---|---|
| 1 | 水流 | 需管理员授予 `particle_water` 标签 |
| 2 | 火焰 | 需管理员授予 `particle_flame` 标签 |
| 3 | 音符 | 需管理员授予 `particle_note` 标签 |
| 100 / 103 | 樱花 / 心形 | 特定玩家 |
| 101 | 心形 | `special` 队伍 |
| 102 | 铜火 | `ops` 队伍 |

管理员可在控制面板的「管理便利面板」中直接复制授权指令。

## 快速开始

需要 **Python 3.14**（beet 0.121 的硬性要求）。

```bash
# 1. 准备环境
python -m venv .venv
.venv\Scripts\activate          # macOS / Linux: source .venv/bin/activate

# 2. 安装依赖（beet 负责打包，mecha 负责指令解析与校验）
pip install "beet==0.121.2" mecha

# 可选：把工程装成可编辑包，便于 IDE 跳转；不装也能构建
pip install -e .

# 3. 构建
beet build                      # 产物在 build/ACPack/
```

把 `build/ACPack/` 整个目录放进存档的 `datapacks/` 下即可；也可以直接软链：

```bash
beet build --link "World"       # 自动链接到存档
beet watch                      # 开发时监听改动并自动重建
```

### 运行测试

```bash
pytest                          # 校验护栏 + 与原实现的逐指令对拍
python tools/parity.py --diff   # 单独查看与原实现的差异
```

> 对拍的基准是仓库根目录下的 **`original.zip`**——即迁移前 mcfunction 版数据包的标准压缩包（根内含 `pack.mcmeta` 与 `data/`）。也可以用 `--original` 指向其他 `.zip` 或解包目录，
> 或用环境变量 `ACPACK_ORIGINAL` 指定。找不到基准包时对拍测试会自动跳过，构建与校验测试仍会执行。

## 目录结构

```
acpack-beet/
├── beet.yaml                   # 工程配置：输出目录、包格式、构建管线
├── pyproject.toml              # 依赖声明（beet / mecha）
├── acpack/                     # 全部逻辑（Python，仓库内无 .mcfunction）
│   ├── constants.py            #   版本号、目标 MC、计分板名、队伍、trigger 编码
│   ├── commands.py             #   指令构造器
│   ├── components.py           #   聊天文本组件构造器（按钮 / 悬停 / 点击 / 分数）
│   ├── builder.py              #   指令行 → beet 资源
│   ├── validation.py           #   构建期校验（悬空引用、未声明计分板）
│   ├── pipeline.py             #   beet 入口：assemble → mecha → finalize
│   ├── features/               #   一个功能一个模块
│   └── content/                #   配方、战利品表
├── tests/                      # 对拍闸门 + 校验护栏单测
├── tools/parity.py             # 对拍命令行工具
└── .github/workflows/build.yml # CI：构建 + 产物结构检查 + 测试 + 上传产物
```

## 构建管线

| 阶段 | 组件 | 作用 |
|---|---|---|
| 1 | `acpack.pipeline.build` | 由 Python 生成函数、配方、战利品表、进度，并做构建期校验 |
| 2 | `mecha` | 解析全部 `.mcfunction`，语法错误直接让构建失败，同时规范化输出 |
| 3 | `acpack.pipeline.finalize` | 写回 `pack.mcmeta`（描述、`min_format` / `max_format`） |

## 常见开发任务

| 想做的事 | 改哪里 |
|---|---|
| 加一条小贴士 | `acpack/features/tips.py` 的 `TIPS` 字典 |
| 加一种粒子效果 | `acpack/features/particles.py` 的 `PARTICLE_MODES` |
| 加一个显示模式 | `acpack/features/panel.py` 的 `MODE_OPTIONS`（面板按钮、切换分支、图例自动同步） |
| 加一项统计 | `statistics/objectives.py` 的 `OBJECTIVES` + `statistics/counters.py` 的 `COUNTER_GROUPS` |
| 加一个 `/trigger` 入口 | `constants.py` 的 `TRIG_*` + `dispatch.py` 的 `DISPATCH_TABLE` |
| 加一条周期任务 | `features/timers.py` 的 `LOOPS` |
| 改版本号 / 目标版本 | `constants.py`（`PACK_VERSION`、`MC_TARGET`、`PACK_FORMAT`） |

## 质量保障

- **构建期校验**：所有 `function` / `schedule` 目标必须存在，所有引用的计分板必须已声明，否则构建直接失败。
- **逐指令对拍**：`tools/parity.py` 用 mecha 把两侧指令解析成 AST 后比较，配合 `tests/test_parity.py`
  断言「与原实现的差异集合恒定」，防止后续改动静默引入偏差。
- **CI**：`.github/workflows/build.yml` 在 Python 3.14 上构建、检查产物结构（`pack.mcmeta`、
  关键函数/标签/战利品表、函数数量）、运行测试并上传构建产物。

## 兼容性

- 目标版本：**Minecraft 26.3**，`pack_format` = 121
- 纯数据包，无资源包、无客户端依赖
- 语言：中文（简体）

## 关于本仓库

本工程是 ACPack 的 beet + Python 重写版，与原始 mcfunction 实现的行为差异逐项记录在
[MIGRATION.md](MIGRATION.md)。它当前位于 ACPack 主仓库的 `acpack-beet/` 子目录并在主仓库中
被忽略；作为独立仓库推送后，内置的 CI 会自动生效。

**AIGC使用声明**：本项目重写基础基本全部由AI大模型生成。

## 许可

沿用原项目：[Mozilla Public License 2.0](https://www.mozilla.org/en-US/MPL/2.0/)。
任何使用本项目内容的二次开发成果均须注明来源，所使用的项目文件需开源，作者不对二次开发背书。

---

## English

ACPack is a server-side Minecraft datapack built for the **AreoCraft** server, targeting
Minecraft 26.3. It adds player statistics with a sidebar, an in-game control panel, rotating
tips, a player-triggered item sweeper, particle effects, and tweaked recipes and piglin
bartering — all without any client-side mods.

The whole pack is authored in **Python** and compiled with [beet](https://mcbeet.dev/):
every function is generated programmatically, validated against the command grammar with
`mecha`, and checked instruction-by-instruction against the original `.mcfunction`
implementation.

```bash
pip install "beet==0.121.2" mecha
beet build          # → build/ACPack/
pytest              # build guard + parity tests
```

Licensed under the Mozilla Public License 2.0.
