# 迁移改动记录（ACPack → beet + Python）

本文件逐项记录**重写版与原数据包的所有差异**：每一处都给出原始实现的位置与代码、改动动机、
具体方案、影响范围与验收方式。凡未列入本文件的函数，构建产物与原实现**逐条指令一致**
（由 `tests/test_parity.py` 强制）。

---

## 0. 总览

| 维度 | 原项目 | 重写版 |
|---|---|---|
| 形态 | 29 个 `.mcfunction` + 7 配方 + 1 战利品表 + 1 进度 + 1 标签 | 纯 Python 包（19 个模块），构建时生成同名数据包 |
| 构建 | 手工维护 `data/` 目录 | `beet build` → `build/ACPack/`，mecha 逐条解析校验 |
| 元信息 | 散落在 pack.mcmeta / 横幅 / 面板 / README，互不一致 | `acpack/constants.py` 单一来源 |
| 校验 | 无（写错路径要进游戏才发现） | 构建期断言：悬空函数引用、未声明计分板 |
| 验收 | 无 | 与原包对拍：函数指令序列 + JSON 深比较 |

**改动统计（对拍实测）**：产物共 68 个文件（57 个函数 + 10 个 JSON + `pack.mcmeta`）。
其中 **10 个函数**存在差异，其余 **47 个函数**与**全部 10 个 JSON**（7 配方 + 战利品表 +
进度 + 函数标签）**逐条一致**；文件集合 0 缺失、0 多余。

差异函数清单：

```
ac:display/set_mode                        (F1)
ac:display/settings                        (F7)
ac:info                                    (F6)
ac:particle/2tick                          (F2)
statistics:load                            (F5)
statistics:display/update_recording         (F6)
statistics:death/death_merge                (F3)
statistics:hoe/hoe_merge                    (F3)
statistics:mine/mine_merge                  (F3)
statistics:open_container/open_container_merge (F3)
```

> 说明：`ac:load`、`ac:display/bar`、`ac:first_join/first_join`、`ac:sweeper/*`（7 个）、
> `ac:tips/*`（4 个）、`ac:trigger/*`（2 个）、`ac:kill/kill`、`ac:particle/particle` 等
> 均**未改动**，包括扫地机全部逻辑（按需求冻结）。

---

## 1. F1 · `set_mode` 中 trigger 20 的记账分支写错

### 原始实现

`data/ac/function/display/set_mode.mcfunction` 第 51–53 行：

```mcfunction
execute if score @s trigger matches 20 run scoreboard players set @s stats.display_mode 10
execute if score @s trigger matches 19 run scoreboard players set @s trigger.int 20
execute if score @s trigger matches 20 run tellraw @s {"text":"计分板显示已固定为: 放置次数","color":"aqua"}
```

三段式结构是「设置显示模式 / 记下本次操作编号 / 反馈文案」，其余 10 个分支都是同一个
trigger 值，唯独这一行的条件写成了 `19`（复制上一分支后忘记改）。

### 问题与动机

`trigger.int` 全项目没有任何读取方（仅用于记录「最近一次操作」），所以这个笔误不会导致
玩家看到错误结果，但会让审计/调试时看到的编号与实际模式不符；改造成表驱动后该分支由
数据生成，顺手修正即可，风险为零。

### 改动方案

`acpack/features/panel.py` 把 11 个模式收敛为 `MODE_OPTIONS` 表：

```python
MODE_OPTIONS = [
    ModeOption(10, 1, "[普通轮播]", "普通轮播模式", "green", "计分板显示已切换为: 普通轮播"),
    ...
    ModeOption(20, 10, "[固定:放置次数]", "固定显示放置次数", "aqua", "计分板显示已固定为: 放置次数"),
    ModeOption(18, 8, "[录屏模式]", "录屏模式:显示固定服务器信息", "light_purple", "计分板显示已切换为: 录屏模式"),
]
```

每个选项生成三条指令，条件统一取自 `option.trigger`：

```python
for option in MODE_OPTIONS:
    condition = c.condition_score("@s", OBJ_TRIGGER, str(option.trigger))
    set_mode.add(
        c.execute(condition, c.sb_set("@s", OBJ_DISPLAY_MODE, option.mode)),
        c.execute(condition, c.sb_set("@s", OBJ_TRIGGER_INT, option.trigger)),
        c.execute(condition, c.tellraw("@s", text(option.feedback, color=option.panel_color))),
    )
```

### 影响与验收

只有 `trigger.int` 的记账值从「19」变为「20」，玩家可见行为不变。

```diff
-execute if score @s trigger matches 19 run scoreboard players set @s trigger.int 20
+execute if score @s trigger matches 20 run scoreboard players set @s trigger.int 20
```

---

## 2. F2 · 粒子系统在多人环境下按 N² 放大

### 原始实现

`data/ac/function/particle/player.mcfunction`：

```mcfunction
execute as @a run function ac:particle/2tick
```

`data/ac/function/particle/2tick.mcfunction` 第 3 行：

```mcfunction
execute as @a run function ac:particle/particle
```

`2tick` 本身就是以「某一名玩家」为执行者进入的（`@s` 即该玩家），函数内部却又写了一次
`execute as @a`，于是：**N 名在线玩家 → 每 tick 执行 N × N 次粒子指令**，每名玩家的粒子
效果被叠加 N 份。

### 问题与动机

- 视觉上：粒子密度随在线人数线性放大，10 人时单帧粒子量是设计值的 10 倍；
- 性能上：`execute` 与粒子生成的开销按 N² 增长，属于典型的单人测试发现不了、开服才炸的问题；
- `particle/particle` 内部全部用 `@s` 判定（`execute as @s[tag=...]`），本就不需要外层再遍历一次，
  内层 `as @a` 纯属复制粘贴残留。

### 改动方案

`acpack/features/particles.py` 的 `_tick()` 直接以当前玩家执行：

```python
tick.add(
    c.sb_enable("@s", OBJ_TRIGGER_PARTICLE),
    c.if_score("@s", OBJ_TRIGGER_PARTICLE, "1..", c.call("ac:particle/merge")),
    # 原为 `execute as @a run ...`，此处去掉内层选择器（F2）
    c.call("ac:particle/particle"),
)
```

外层 `ac:particle/player` 的 `execute as @a run function ac:particle/2tick` 保持不变，
因此「每名玩家每 2 tick 一次」的节奏与原来一致。

### 影响与验收

单人时完全无差别；多人时粒子密度回到设计值（每人一份）。
`ac:particle/particle`、`merge`、`error`、`particle_bar` 四个函数**零改动**。

```diff
-execute as @a run function ac:particle/particle
+function ac:particle/particle
```

---

## 3. F3 · 统计合并把「同 tick 多次事件」压成 1 次

### 原始实现

以挖掘为例，`statistics:mine/mine_judge` 每个 tick 检查 7 个原版统计计分板：

```mcfunction
execute as @a[scores={stats.netherite_shovel_used=1..}] run function statistics:mine/mine_merge
...（共 7 条，覆盖铲/镐/斧 × 下界合金/钻石 + 剪刀）
```

`statistics:mine/mine_merge`：

```mcfunction
scoreboard players add @s stats.player_mine 1
scoreboard players add total stats.player_mine 1
scoreboard players reset @s stats.diamond_axe_used
...（把 7 个源计分板全部清零）
```

即：**不管源计分板累计了多少次，一律 +1 后清零**。`hoe` / `death` / `open_container`
三组写法相同；只有 `traded_with_villager` 用了 `operation +=`（把源值累加后清零）。

### 问题与动机

原版统计（`minecraft.used:*`、`minecraft.custom:*`）在同 tick 内可能增加多次，例如：

- 一次右键打开潜影盒同时触发 `open_shulker_box` 与 `open_chest`（不同源，仍会计 2 次，正确）；
- 同一 tick 内连续使用同一把工具/连开同一个箱子（同源多次）→ 只记 1 次，**丢计**；
- `stats.death`（原版死亡数）在同 tick 因摔落+实体伤害叠加等情况可能 +2 → 只记 1 次。

因为 `judge` 每 tick 都跑，丢计只发生在「同一 tick 内同源事件 >1」，日常影响小但确实存在，
且会让排行榜与真实操作数长期偏离。

### 改动方案

`acpack/features/statistics/counters.py` 用一张 `COUNTER_GROUPS` 表描述「显示计分板 ← 源计分板列表」，
`merge` 改为**先累加源值、再清零**：

```python
for source in group.sources:
    merge.add(
        c.sb_operation("@s", group.display, "+=", "@s", source),
        c.sb_operation(TOTAL, group.display, "+=", "@s", source),
        c.sb_reset("@s", source),
    )
```

**幂等性**：`judge` 可能因多个选择器命中而对同一玩家重复调用 `merge`；由于第一次调用已把
所有源计分板清零，后续调用累加的是 0，不会重复计数——与原来的「多次调用 +N」行为一致，
只是把 N 从「1」换成了「该 tick 真实次数」。

`traded_with_villager` 组原本就用 `+=`，生成的指令与原文**逐字一致**，因此不在差异清单里。

### 影响与验收

| 组 | 原 merge 行数 | 新 merge 行数 | 语义变化 |
|---|---|---|---|
| mine | 9 | 21 | 同 tick 多次使用同一工具不再丢计 |
| hoe | 4 | 6 | 同上 |
| death | 3 | 3 | 同 tick 多次死亡不再丢计 |
| open_container | 6 | 12 | 同 tick 多次开同一容器不再丢计 |
| traded_with_villager | 3 | 3 | 无（原本即正确） |

死亡与容器的「每 tick 一次」上限消失后，`total` 假玩家的累计口径也随之变准。

---

## 4. F5 · `statistics:load` 里必然报错的 `advancement revoke`

### 原始实现

`data/statistics/function/load.mcfunction` 第 38 行：

```mcfunction
advancement revoke @s only statistics:place
```

### 问题与动机

`ac:load` / `statistics:load` 由 `minecraft:load` 函数标签在**服务端上下文**执行，此时没有
实体执行者，`@s` 无法解析，该指令每次 `/reload` 或开服都会失败并在日志里留下一条错误。
它的意图是「重新加载时清掉玩家的放置进度」，但：

- 真正需要撤销的时机是**每次放置之后**，`statistics:block_place/place` 内部已经逐玩家执行
  `advancement revoke @s only statistics:place`；
- 服务端上下文里无论如何都撤销不到具体玩家，写 `execute as @a run ...` 反而会在 `load`
  阶段对全部在线玩家做一次无意义撤销。

### 改动方案

删除该行（`acpack/features/statistics/objectives.py` 未生成此指令），其余顺序不变。

### 影响与验收

- 行为：无玩家可见影响；放置计数逻辑不受影响（依赖 `place` 函数内的逐玩家 revoke）。
- 收益：`/reload` 不再刷错误日志。
- 对拍：`statistics:load` 行数 32 → 31，且仅此一行差异。

```diff
-advancement revoke @s only statistics:place
```

---

## 5. F6 · 版本号与目标版本四处不一致

### 原始实现

| 位置 | 原文 |
|---|---|
| `pack.mcmeta` | `"Datapack designed for Areocraft Server, Version 1.0.8.1, Targeting MC 26.3."` |
| `data/ac/function/info.mcfunction` 第 2 行 | `{"text":"ACPack v1.0.8.3 更新时间:2026.6.29","bold":false}` |
| `statistics/display/update_recording.mcfunction` 第 9 行 | `scoreboard players set 版本：1.21.11 stats.display_recording 2` |
| `README.md` | 徽章 `v1.0.8`，分支名 `26.3_v1.0.8.4` |

### 问题与动机

同一份产物的版本号出现 1.0.8.1 / 1.0.8.3 / 1.0.8.4 三种；录屏板上的游戏版本还停留在
1.21.11，而包实际目标是 26.3。玩家在录屏画面里看到的是错误的服务器版本信息，且每次改版本
都需要人工同步多处，必然再次漂移。

### 改动方案

`acpack/constants.py` 收敛为唯一来源：

```python
PACK_VERSION = "1.0.8.4"
MC_TARGET = "26.3"
PACK_FORMAT = (121, 0)
PACK_DESCRIPTION = (
    f"Datapack designed for Areocraft Server, Version {PACK_VERSION}, "
    f"Targeting MC {MC_TARGET}."
)
```

三处消费同一来源：

- `acpack/pipeline.py::finalize` 写 `pack.mcmeta`（`description` / `min_format` / `max_format`）；
- `acpack/features/boot.py` 拼接横幅 `f"ACPack v{PACK_VERSION} 更新时间:2026.6.29"`；
- `acpack/features/statistics/display.py` 拼接录屏板 `f"版本：{MC_TARGET}"`。

`更新时间:2026.6.29` 属于文案，保持原样未参数化。

### 影响与验收

```diff
-{"bold":false,"text":"ACPack v1.0.8.3 更新时间:2026.6.29"}
+{"bold":false,"text":"ACPack v1.0.8.4 更新时间:2026.6.29"}

-scoreboard players set 版本：1.21.11 stats.display_recording 2
+scoreboard players set 版本：26.3 stats.display_recording 2
```

`pack.mcmeta` 的 `min_format` / `max_format` 与原文完全一致（`[121, 0]`），仅 `description`
中的版本号更新，`tests/test_parity.py::test_pack_mcmeta` 对此有断言。

---

## 6. F7 · 计分板设置面板的图例缺两项

### 原始实现

`data/ac/function/display/settings.mcfunction` 第 7 行：

```mcfunction
tellraw @s [{text:"当前模式: ",color:"yellow"},{"score":{"name":"@s","objective":"stats.display_mode"},"color":"gold"},{"text":" (0=关闭,1=轮播,2=死亡,3=挖掘,4=锄头,5=容器,6=交易,7=时长,8=录屏)","color":"gray"}]
```

### 问题与动机

面板本身提供 11 个按钮（模式 0–10），但图例只解释到 8；模式 9（加入次数）与 10（放置次数）
没有说明，玩家看到 `当前模式: 9` 时无从对照。原实现里图例、按钮、`set_mode` 分支是三份
彼此独立的手写副本，加模式时漏改图例几乎必然发生。

### 改动方案

图例由 `MODE_OPTIONS` 派生，模式清单与按钮同源：

```python
LEGEND = "(0=关闭,1=轮播,2=死亡,3=挖掘,4=锄头,5=容器,6=交易,7=时长,8=录屏,9=加入,10=放置)"
```

### 影响与验收

```diff
-... "(0=关闭,1=轮播,2=死亡,3=挖掘,4=锄头,5=容器,6=交易,7=时长,8=录屏)"
+... "(0=关闭,1=轮播,2=死亡,3=挖掘,4=锄头,5=容器,6=交易,7=时长,8=录屏,9=加入,10=放置)"
```

仅该行变化；同一函数内 7 行按钮的文案、颜色、点击/悬停事件与原文逐字段一致。

---

## 7. 冻结与保留：明确「不改」的部分

### 7.1 扫地机（按需求完全冻结）

`acpack/features/sweeper.py` 七个函数与原文**逐条指令一致**，包括以下容易被误认为缺陷、
但本次**明确保留**的行为：

| 行为 | 原实现 | 本次处理 |
|---|---|---|
| 清理范围 | `kill @e[type=item]` 在服务端上下文执行，仅作用于**主世界** | 保留（不扩到三界） |
| 音效 | `playsound entity.villager.ambient` 不带目标选择器，服务端上下文无接收者 | 保留 |
| 状态切换 | `announce` / `break` 通过 `schedule ... 1t` 延迟到下一 tick 再改状态，规避同 tick 判定竞态 | 保留（注释说明原因） |
| 倒计时语义 | `-1` 待机 / `15` 起步 / 每秒 -1 / `0` 清场 | 保留 |
| 提示秒数 | 仅在 1、2、3、4、5、10 秒播报 | 保留 |

为满足「逐指令一致」，连原实现里那条 `tellraw @a [...]` 的单元素数组写法也原样复现
（见 `_judge()` 中的注释）。

### 7.2 记录但不修改的行为

| 行为 | 位置 | 说明 |
|---|---|---|
| `stats.gametime` 重置为 61 而非 0 | `statistics/gametime/gametime_merge` | 依赖 `minecraft.custom:play_time` 的同步时机，实测可用；改 0 会引入双计风险 |
| 每小时 +1201 时补 1 | 同上 | 补偿约 3 秒/小时的计时漂移 |
| 每 10s 清空 bots 队统计 | `statistics:fake_player_remove` | 假人统计的既定策略；顺手把真人放进 bots 队也会被清 |
| 轮播 1..8 循环 | `statistics:display/random` | 核对后确认**不是**缺陷：轮播只有 8 项，与 `display_sidebar` 的 8 条映射一一对应 |
| `objectives add` 重复报错 | `ac:load` / `statistics:load` | 每次 reload 会对已存在的计分板报错；不能改成先 `remove`（会清空玩家数据） |
| 小贴士编号 114514 | `tips` 文案表 | `random value 1..21` 取不到，彩蛋性质，保留 |
| 首次加入重复写两次 `stats.gametime=61` | `ac:first_join/first_join` | 无副作用的重复写入，保留以维持逐指令一致 |

### 7.3 结构性重构（不改变产物行为）

- **注释剥离**：原文件里的中文注释（含 `bar.mcfunction` 里 10 行已注释掉的「旧版参考」）
  不再进入产物；`.mcfunction` 本身不需要注释，开发注释保留在 Python 源码里。
- **mecha 规范化**：管线中的 `mecha` 会重排指令里的空格、把 JSON 键改回宽松写法、
  把 `1t` 简写为 `1`、把中文转成 `\uXXXX`。这些都与原产物等价（Minecraft 两种写法都接受），
  对拍时已用「AST 序列化 + JSON 键排序」抵消该噪声。
- **表驱动**：`dispatch` / `timers` / `panel` / `tips` / `particles` / `counters` 六处
  由「复制粘贴的多份相似文件」改为「一张表 + 一个生成器」，产物指令数量与顺序保持原样。

---

## 8. 完整文件映射

### 8.1 函数

| 原文件 | 新模块 | 产物路径 |
|---|---|---|
| `ac/function/load.mcfunction` | `features/boot.py` | `ac:load` |
| `ac/function/info.mcfunction` | `features/boot.py` | `ac:info` |
| `ac/function/ticks/{1tick,2tick,1sec,300sec}` | `features/timers.py`（`LOOPS`） | 同名 |
| `ac/function/trigger/{player,1tick}` | `features/dispatch.py`（`DISPATCH_TABLE`） | 同名 |
| `ac/function/display/{bar,settings,set_mode}` | `features/panel.py`（`MODE_OPTIONS`） | 同名 |
| `ac/function/tips/{_on,_off,random,announce_tips}` | `features/tips.py`（`TIPS`） | 同名 |
| `ac/function/sweeper/{start,1sec,judge,clean,announce,break,halt}` | `features/sweeper.py`（冻结） | 同名 |
| `ac/function/particle/{player,2tick,merge,particle,particle_bar,error}` | `features/particles.py`（`PARTICLE_MODES`） | 同名 |
| `ac/function/first_join/{player,1tick,first_join}` | `features/first_join.py` | 同名 |
| `ac/function/kill/kill.mcfunction` | `features/kill.py` | `ac:kill/kill` |
| `statistics/function/load.mcfunction` | `features/statistics/objectives.py` | `statistics:load` |
| `statistics/function/{mine,hoe,death,open_container,traded_with_villager}/*_{judge,merge}` | `features/statistics/counters.py`（`COUNTER_GROUPS`） | 同名 |
| `statistics/function/gametime/*`、`join_time/*` | `features/statistics/session.py` | 同名 |
| `statistics/function/display/*` | `features/statistics/display.py` | 同名 |
| `statistics/function/block_place/place.mcfunction` | `features/statistics/placement.py` | 同名 |
| `statistics/function/fake_player_remove/*` | `features/statistics/maintenance.py` | 同名 |
| `statistics/function/{1tick,10sec}` | `features/timers.py` | 同名 |

### 8.2 数据

| 原文件 | 新模块 | 说明 |
|---|---|---|
| `ac/recipe/*.json`（7 个） | `content/recipes.py`（`RECIPES`） | 内容逐字段一致 |
| `minecraft/loot_table/gameplay/piglin_bartering.json` | `content/loot_tables.py` | 23 条目、权重、数量区间一致 |
| `statistics/advancement/place.json` | `features/statistics/placement.py` | 结构一致 |
| `minecraft/tags/function/load.json` | `features/boot.py` / `objectives.py` 的 `tags=["minecraft:load"]` | 由 beet 生成，值顺序 `ac:load` → `statistics:load` 不变 |
| `pack.mcmeta` | `pipeline.py::finalize` | `min_format`/`max_format` 一致，`description` 见 F6 |

---

## 9. 等价性验证方式

```bash
cd acpack-beet
beet build                       # 生成 build/ACPack
python tools/parity.py --diff    # 差异报告（可读 diff）
pytest                           # 断言差异集合 == 本文档列出的 10 项
```

基准包为仓库根目录的 `original.zip`（迁移前 mcfunction 版的标准数据包压缩包，
根内含 `pack.mcmeta` 与 `data/`）。`tools/parity.py` 同时支持 `.zip` 与解包目录，
可用 `--original` 或环境变量 `ACPACK_ORIGINAL` 覆盖默认位置。

比较口径：

1. **函数**：逐行去注释/空行 → mecha 解析成 AST → 重新序列化 → JSON 组件键排序 → 比较指令序列；
2. **JSON**：解析后深比较（配方 / 战利品表 / 进度）；
3. **文件集合**：两边函数与 JSON 路径集合必须完全相等。

`tests/test_parity.py::test_only_expected_functions_changed` 断言差异集合**恰好**等于本文档的
10 项——多一个或少一个都会失败，防止后续维护中悄悄引入新偏差。

超出机械对拍之外、需要真人判断的部分（例如「玩家点按钮后的可见反馈」），结论是：
所有 `tellraw` 文案、颜色、粗体、点击/悬停事件均保持原样，仅 F6/F7 涉及的版本号与图例文字
按上述条目变更。

---

## 10. 回滚

原 `data/` 与 `pack.mcmeta` 未做任何修改，仍是可直接使用的数据包。
若要放弃重写版，直接删除 `acpack-beet/` 并移除 `.gitignore` 中的 `/acpack-beet/` 一行即可。
