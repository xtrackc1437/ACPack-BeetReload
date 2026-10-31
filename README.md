# ACPack · beet 工程

原 `E:/DevSpace/ACPack/ACPack-26.3` 数据包（v1.0.8.4，目标 MC 26.3）的 beet 重写版：
**全部逻辑由 Python 生成**，仓库内不保留任何 `.mcfunction` 源文件，构建期由 beet + mecha
解析、校验并输出标准数据包。

原项目目录保持原样、未被本工程修改；本目录可独立构建、独立发布。

---

## 1. 环境准备

需要 Python 3.14（beet 0.121 的硬性要求）。

```bash
cd acpack-beet

# 建虚拟环境
python -m venv .venv
.venv\Scripts\activate            # Windows PowerShell: .venv\Scripts\Activate.ps1

# 安装依赖（beet 已锁定 0.121.2；mecha 是管线里的指令解析/校验阶段）
pip install "beet==0.121.2" mecha

# 可选：把工程本身装成可编辑包，方便 IDE 跳转
pip install -e .
```

> 不执行 `pip install -e .` 也能正常构建：beet 会把工程根目录加入 `sys.path`，
> `acpack` 包可被直接导入（已在其他工作目录下用 `beet -p <工程目录> build` 验证过）。

## 2. 常用命令

```bash
beet build                      # 构建到 build/ACPack/
beet build --link "World"       # 直接软链到存档的 datapacks 目录
beet watch                      # 监听 Python 改动并自动重建
beet build -s output=out        # 临时覆盖输出目录

python tools/parity.py          # 与原始数据包对拍（见第 5 节）
python tools/parity.py --diff   # 打印逐行差异
pytest                          # 对拍 + 结构校验测试
```

产物 `build/ACPack/` 即为可直接放进 `world/datapacks/` 的数据包目录（含 `pack.mcmeta`）。
目录名由 `beet.yaml` 的 `data_pack.name` 固定，不随版本号变化。

## 3. 目录结构

```
acpack-beet/
├── beet.yaml                   # beet 工程配置：输出目录、包格式、构建管线
├── pyproject.toml              # 依赖与包声明（beet==0.121.2）
├── .gitignore                  # 忽略 .venv/ build/ __pycache__ 等（整个目录另被根 .gitignore 忽略）
├── README.md                   # 本文
├── MIGRATION.md                # 与原项目的逐项差异记录（改动原因与方案）
├── acpack/                     # 全部逻辑（Python）
│   ├── constants.py            # ★ 唯一真相源：版本号、目标 MC、计分板名、队伍、trigger 编码
│   ├── commands.py             # 指令字符串构造器（scoreboard/execute/tellraw/schedule/particle…）
│   ├── components.py           # 聊天文本组件构造器（按钮、悬停、点击、分数）
│   ├── builder.py              # FunctionBuilder / PackWriter：把指令行登记成 beet 资源
│   ├── validation.py           # 构建期断言：悬空函数引用、未声明计分板
│   ├── pipeline.py             # beet 入口：assemble → mecha → finalize
│   ├── features/               # 一个功能一个模块
│   │   ├── boot.py             #   ac:load（初始化）+ ac:info（启动横幅）
│   │   ├── timers.py           #   全部 schedule 循环（表驱动）
│   │   ├── dispatch.py         #   trigger → 功能 的分发表
│   │   ├── panel.py            #   控制面板 / 显示设置 / 显示模式切换
│   │   ├── tips.py             #   小贴士（文案表）
│   │   ├── sweeper.py          #   扫地机（冻结模块，行为与原实现完全一致）
│   │   ├── particles.py        #   粒子装饰（模式表）
│   │   ├── first_join.py       #   首次加入引导
│   │   ├── kill.py             #   自杀 / 脱离卡死
│   │   └── statistics/         #   统计命名空间
│   │       ├── objectives.py   #     计分板声明
│   │       ├── counters.py     #     挖掘/锄头/死亡/容器/交易 的判定与合并
│   │       ├── session.py      #     游戏时长、加入次数
│   │       ├── display.py      #     侧边栏模式、轮播、录屏板
│   │       ├── placement.py    #     放置统计（advancement 驱动）
│   │       ├── maintenance.py  #     假人统计清理
│   │       └── names.py        #     统计模块内部名字常量
│   └── content/
│       ├── recipes.py          #   7 个配方
│       └── loot_tables.py      #   猪灵交易覆写
├── tests/
│   ├── test_parity.py          # 构建 → 对拍 → 断言差异集合符合预期
│   └── test_validation.py      # 校验护栏自身的单元测试
└── tools/
    └── parity.py               # 对拍命令行工具
```

## 4. 构建管线

`beet.yaml` 中声明了三段式管线：

| 阶段 | 组件 | 作用 |
|---|---|---|
| 1 | `acpack.pipeline.build` | 调用各 feature 模块生成函数、配方、战利品表、进度；写完做构建期校验 |
| 2 | `mecha` | 解析全部 `.mcfunction`，语法错误直接让构建失败；同时规范化输出 |
| 3 | `acpack.pipeline.finalize` | 写回与原包逐字段一致的 `pack.mcmeta` |

生成流程：`feature.build(pack)` → `pack.fn("ns:path")` 拿到指令累积器 → `flush()` 写入
`ctx.data` → beet 落盘。

## 5. 与原项目的关系 / 对拍

原数据包目录（`../data`、`../pack.mcmeta`）**没有任何改动**，仅作为对拍基准。

`tools/parity.py` 会比较两边：

- 函数：去注释、去空行后逐条经 mecha 解析再序列化，比较**指令序列**（不受空白、引号、
  JSON 键序影响）；
- 配方 / 战利品表 / 进度：解析后结构化深比较；
- 文件集合：缺失或多出的文件都会被报出来。

预期差异（本次迁移有意修正的缺陷）记录在 `MIGRATION.md`，并由 `tests/test_parity.py`
以「允许差异集合」的形式固化为断言：**集合之外出现任何差异，测试即失败**。

## 6. 如何扩展

| 想做的事 | 改哪里 |
|---|---|
| 加一条小贴士 | `features/tips.py` 的 `TIPS` 字典 |
| 加一种粒子 | `features/particles.py` 的 `PARTICLE_MODES` |
| 加一个显示模式 | `features/panel.py` 的 `MODE_OPTIONS` + `PANEL_ROWS`（面板按钮、分支、图例自动同步） |
| 加一项统计 | `statistics/objectives.py` 的 `OBJECTIVES` + `statistics/counters.py` 的 `COUNTER_GROUPS` |
| 加一个 trigger 入口 | `constants.py` 的 `TRIG_*` + `features/dispatch.py` 的 `DISPATCH_TABLE` |
| 加一条周期性任务 | `features/timers.py` 的 `LOOPS` |
| 改版本号 / 目标 MC | `constants.py`（`PACK_VERSION`、`MC_TARGET`、`PACK_FORMAT`） |

## 7. 许可

沿用原项目：Mozilla Public License 2.0。
