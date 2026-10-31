"""小贴士系统。

对应原文件：
  data/ac/function/tips/_on.mcfunction
  data/ac/function/tips/_off.mcfunction
  data/ac/function/tips/random.mcfunction
  data/ac/function/tips/announce_tips.mcfunction

文案从 24 个 `execute if score ... matches N run tellraw` 行改为「编号 -> 组件」字典，
新增/删除一条提示只需改表。
"""

from __future__ import annotations


from .. import commands as c
from ..builder import PackWriter
from ..components import Message, open_url, show_text, text
from ..constants import OBJ_TIPS_RANDOM, OBJ_TRIGGER, OBJ_TRIGGER_INT, RANDOM_HOLDER

TIPS: dict[int, Message] = {
    1: text("你知道吗?服务器的名字areocraft其实为拼写错误！", color="aqua"),
    2: text("服务器可以使用skin指令设置皮肤,哪怕你是离线玩家！", color="aqua"),
    3: text("你知道吗?服务器其实有两个服主！", color="aqua"),
    4: text("服务器使用数据包对原版游戏进行了少量修改,具体请查看官网！", color="aqua"),
    5: [
        text("服务器有专门的帮助文档,请点击这里查看:", color="aqua"),
        text(
            "https://docsareocraft.zhangrx.top/zh/help",
            color="aqua",
            hover=show_text("点我打开官方文档库"),
            click=open_url("https://docsareocraft.zhangrx.top/zh/help"),
        ),
    ],
    6: text("你知道吗?我们服务器的周目数大概率是国内生电服最多的 qwq", color="aqua"),
    7: text("你可以使用/trigger trigger set 1,打开控制面板关闭小贴士！", color="aqua"),
    8: text("第一次使用数据包将会自动打开小贴士,这是设定！！！", color="aqua"),
    9: text("小贴士每5分钟会显示一次！", color="aqua"),
    10: [
        text("如果想要为该数据包提出意见(包括小贴士投稿,数据包内容增加),可以前往:", color="aqua"),
        text(
            "https://github.com/misividkoukou/ACPack/issues",
            color="green",
            click=open_url("https://github.com/misividkoukou/ACPack/issues"),
        ),
        text("提交issue", color="aqua"),
    ],
    11: text("PCL的联机功能本质上与RADMIN一致。你下载RADMIN了吗？大家都用它联机!", color="aqua"),
    12: text("再提醒亿次,服务器有特殊的配方和交易！！！", color="aqua"),
    13: text("入服半年以上的玩家可以申请管理组！", color="aqua"),
    14: text(
        "服务器正式玩家可以直接邀请玩家入服,但是惩罚具有连坐机制...不要邀请不认识的人直接入服...",
        color="aqua",
    ),
    15: [
        text("服务器内群为邀请制。", color="aqua"),
        text("内群总有好处的,不是吗?", strikethrough=True),
    ],
    16: text("考核期一般为15天左右,考核期通过后才会成为正式玩家...", color="aqua"),
    17: text("迅捷潜行可以通过猪灵交易获得。别跑图了...", color="aqua"),
    18: text("猪灵交易可以让你获得一些稀有物品...", color="aqua"),
    # 原文故意加了乱码效果
    19: text("尼达斯豆菜布盗着哩斜得势肾癦", color="aqua", obfuscated=True),
    20: text("服务器虽然周目数很多，但不少周目都在存档毕业前就废弃了或者损坏了...", color="aqua"),
    21: text(
        "2026年6月是第25个全国安全生产月，主题是'人人讲安全，个个会应急——排查整治风险隐患'。"
        "安全无小事，防患于未然。让我们在生电生产中，排查机器隐患，守护心态平安。AreoCraft管理组宣",
        color="aqua",
    ),
    # 彩蛋：random value 1..21 永远取不到，保留原样
    114514: text("这条消息永远不会显示在小贴士上！", color="aqua"),
}

RANDOM_RANGE = "1..21"


def build(pack: PackWriter) -> None:
    _toggle(pack, "ac:tips/_on", TRIGGER_INT=2, enabled=True)
    _toggle(pack, "ac:tips/_off", TRIGGER_INT=3, enabled=False)
    _random(pack)
    _announce(pack)


def _toggle(pack: PackWriter, reference: str, *, TRIGGER_INT: int, enabled: bool) -> None:
    function = pack.fn(reference)
    function.add(
        c.sb_reset("@s", OBJ_TRIGGER),
        c.sb_set("@s", OBJ_TRIGGER_INT, TRIGGER_INT),
    )
    if enabled:
        function.add("tag @s add tips_on")
        message = "小提示现在已经打开"
    else:
        function.add("tag @s remove tips_on")
        message = "小提示现在已经关闭"
    function.add(c.tellraw("@s", text(message, color="aqua")))


def _random(pack: PackWriter) -> None:
    function = pack.fn("ac:tips/random")
    # 随机数是全局的：由服务端持有，不放在玩家上下文里
    function.add(
        c.sb_store_result(RANDOM_HOLDER, OBJ_TIPS_RANDOM, c.random_value(RANDOM_RANGE)),
        c.execute(c.as_("@a[tag=tips_on]"), c.call("ac:tips/announce_tips")),
    )


def _announce(pack: PackWriter) -> None:
    function = pack.fn("ac:tips/announce_tips")
    function.add(c.tellraw("@s", text("小贴士( •̀ ω •́ )y", color="aqua")))
    for index, message in TIPS.items():
        function.add(c.if_score(RANDOM_HOLDER, OBJ_TIPS_RANDOM, str(index), c.tellraw("@s", message)))
