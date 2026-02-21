import discord
from discord.ext import commands, tasks
from discord import app_commands
from discord import ui
from datetime import datetime, timedelta
import asyncio
import time
from collections import Counter
from utils.error_handler import safe_execute


# 役職一覧
ROLE_DATA = {
    "villager":{
        "name": "村人",             # 日本語役職名
        "team": "human",            # 陣営
        "selected_score" : 0,       # 選択役職に付随する得点（能力得点）
        "confirmed_score" : 0,      # 確定役職に付随する得点
        "night_action": None,       # 夜能力 # none:なし # target:対象セレクト # agent:工作員専用
        "night_message": "村人は、夜の行動は特にありません。", # 夜のメッセージ
        "order": 0,                 # 夜処理順
        "is_expansion": False,      # 拡張役職
    },
    "werewolf":{
        "name": "人狼",
        "team": "monster",
        "selected_score" : 0,
        "confirmed_score" : 0,
        "night_action": None,
        "night_message": "人狼は、夜の行動は特にありません。",
        "order": 0,
        "is_expansion": False,
    },
    "seer":{
        "name": "占い師",
        "team": "human",
        "selected_score" : 0,
        "confirmed_score" : 0,
        "night_action": {"type": "target"},
        "night_message": "占い師は、占う相手を決めてください。\n占い結果は『人間側』/『モンスター』と出ます。\n※判定結果は**確定役職**の結果です。",
        "order": 100,
        "is_expansion": False,
    },
    "hunter":{
        "name": "狩人",
        "team": "human",
        "selected_score" : 0,
        "confirmed_score" : 0,
        "night_action": None,
        "night_message": "狩人は、夜の行動は特にありません。\n投票終了後に任意で1人を処刑することができます。",
        "order": 0,
        "is_expansion": False,
    },
    "death_seeker":{
        "name": "死にたがり",
        "team": "human",
        "selected_score" : 0,
        "confirmed_score" : 0,
        "night_action": None,
        "night_message": "死にたがりは、夜の行動は特にありません。",
        "order": 0,
        "is_expansion": False,
    },
    "phantom_thief":{
        "name": "怪盗",
        "team": "human",
        "selected_score" : 0,
        "confirmed_score" : 0,
        "night_action": {"type": "target"},
        "night_message": "怪盗は、**選択役職**を交換する相手決めてください。",
        "order": 30,
        "is_expansion": False,
    },
    "cleric":{
        "name": "聖職者",
        "team": "human",
        "selected_score" : 0,
        "confirmed_score" : 0,
        "night_action": None,
        "night_message": "聖職者は、夜の行動終了時に全員の**確定役職**の中にモンスターが居るかどうかが分かります。\n誰・人数は分かりません。",
        "order": 100,
        "is_expansion": True,
    },
    "mayor":{
        "name": "村長",
        "team": "human",
        "selected_score" : 0,
        "confirmed_score" : 0,
        "night_action": None,
        "night_message": "村長は、夜の行動は特にありません。",
        "order": 0,
        "is_expansion": True,
    },
    "agent":{
        "name": "工作員",
        "team": "human",
        "selected_score" : 0,
        "confirmed_score" : 0,
        "night_action": {"type": "target"},
        "night_message": "工作員は、役職塗り替えを交換する相手決めてください。\n対象選択後、塗り替える役職選択用のボタンが出ます。",
        "order": 50,
        "is_expansion": True,
    },
    "serial_killer":{
        "name": "殺人鬼",
        "team": "human",
        "selected_score" : 0,
        "confirmed_score" : 0,
        "night_action": None,
        "night_message": "殺人鬼は、夜の行動は特にありません。",
        "order": 0,
        "is_expansion": True,
    },
    "mentalist":{
        "name": "メンタリスト",
        "team": "human",
        "selected_score" : 0,
        "confirmed_score" : 0,
        "night_action": {"type": "target"},
        "night_message": "メンタリストは、このラウンドで処刑予告する相手決めてください。",
        "order": 10,
        "is_expansion": True,
    },
    "devil":{
        "name": "悪魔",
        "team": "monster",
        "selected_score" : 0,
        "confirmed_score" : 0,
        "night_action": None,
        "night_message": "悪魔は、夜の行動は特にありません。",
        "order": 0,
        "is_expansion": True,
    },
    "esper":{
        "name": "超能力者",
        "team": "human",
        "selected_score" : 0,
        "confirmed_score" : 0,
        "night_action": None,
        "night_message": "超能力者は、夜の行動終了時に使用されている**確定役職**を知ることができます。\n各役職の人数は分かりません。",
        "order": 100,
        "is_expansion": True,
    },
    "vampire":{
        "name": "吸血鬼",
        "team": "monster",
        "selected_score" : 0,
        "confirmed_score" : 0,
        "night_action": {"type": "target"},
        "night_message": "吸血鬼は、眷属化する相手決めてください。\n眷属化された相手は、能力や得点方法はそのまま、陣営がモンスターになります。",
        "order": 80,
        "is_expansion": True,
    },
    #"half_vampire": "半吸血鬼",
    "dog":{
        "name": "犬",
        "team": "human",
        "selected_score" : 0,
        "confirmed_score" : 0,
        "night_action": {"type": "target"},
        "night_message": "犬は、飼い主を決めてください。\n夜の行動終了時に飼い主の確定役職を知ることが出来ます",
        "order": 100,
        "is_expansion": True,
    },
    "plushie":{
        "name": "ぬいぐるみ",
        "team": "human",
        "selected_score" : 0,
        "confirmed_score" : 0,
        "night_action": {"type": "target"},
        "night_message": "ぬいぐるみは、持ち主を決めてください。",
        "order": 10,
        "is_expansion": True,
    },
}

# 拡張役職抜き出し
EXPANSION_ROLES = [
    role for role, data in ROLE_DATA.items()
    if data["is_expansion"]
]

# フェーズ定数
PHASE_WAITING = "waiting"           # 参加受付
PHASE_ROLE_SELECT = "role_select"   # 役職選択
PHASE_NIGHT = "night"               # 夜の時間
PHASE_MORNING = "morning"           # 議論時間
PHASE_VOTE = "vote"                 # 投票
PHASE_HUNTER = "hunter_ability"     # 狩人能力
PHASE_RESULT = "result"             # 最終結果

# セッション管理
class ChoosewolfSession:
    def __init__(self, channel_id):
        self.channel_id = channel_id

    # 使用役職設定
    def set_roles(self):
        self.available_roles = [        # 使用可能な役職リスト
            "villager","werewolf","seer","hunter","death_seeker","phantom_thief",
            #"村人","人狼","占い師","狩人","死にたがり","怪盗",
        ]

    # ゲーム総合管理
    def reset_game(self):
        self.total_score = {}           # 総合得点
        self.round_number = 1           # ゲーム回数

    # ゲーム管理
    def reset_round(self):
        self.guild = None               # ギルド
        self.phase = None               # 現在のフェーズ
        self.owner_id = None            # 送信者
        self.players = set()            # 参加者リスト
        self.selected_roles = {}        # 選択役職
        self.confirmed_roles = {}       # 確定役職
        self.half_vampire = set()       # 半吸血鬼
        self.votes = {}                 # 投票先
        self.mayor_extra_vote = {}      # 村長の追加投票
        self.vampire_target = {}        # 投票の吸血鬼の噛み対象
        self.agent_target_role = {}     # 工作員の指定役職
        self.night_targets = {}         # 各能力の対象
        self.night_done = set()         # 夜の行動済判定
        self.vote_done = set()          # 投票済判定
        self.most_votes = set()         # 最多投票対象
        self.death = set()              # 死
        self.round_score = {}           # このラウンドでの得点
        self.message = None             # メッセージ削除用保管
        self.lock = asyncio.Lock()      # 2重進行ロック
        self.individual_pressed = set() # 個人公表済判定
        self.timer_task = None
        self.end_time = None
        self.timer_message = None
        self.timer_running = False
    
    # team判定（吸血鬼上書き用）
    def get_team(self, user_id):
        if user_id in self.half_vampire:
            return "monster"
        role = self.confirmed_roles.get(user_id)
        if role is None:
            return None
        return ROLE_DATA[role]["team"]
    
    # 役職一覧（吸血鬼上書き用）
    def get_role_name(self, user_id):
        if user_id in self.half_vampire:
            return "半吸血鬼"
        role = self.confirmed_roles.get(user_id)
        if role is None:
            return None
        return ROLE_DATA[role]["name"]

    # 夜の時間終了行動
    async def advance_phase(self, channel):
        # 1.怪盗の反映
        for thief_player_id in self.players:
            thief_role = self.selected_roles.get(thief_player_id)
            if thief_role == "phantom_thief" and thief_player_id in self.night_targets:
                thief_target_id = self.night_targets[thief_player_id]
                # 交換：確定役職へ反映
                self.confirmed_roles[thief_player_id] = self.selected_roles[thief_target_id]
                self.confirmed_roles[thief_target_id] = self.selected_roles[thief_player_id]

        # 2.工作員の反映
        # まずターゲットごとに誰が選んだかを集計
        target_count = {}
        for agent_player_id in self.players:
            agent_role = self.selected_roles.get(agent_player_id)
            if agent_role == "agent":
                agent_target_id = self.night_targets.get(agent_player_id)
                if agent_target_id is not None:
                    target_count[agent_target_id] = target_count.get(agent_target_id, 0) + 1

        if self.agent_target_role:
            for _agent_target_id in self.agent_target_role:
                if target_count[_agent_target_id] == 1:  # 複数選択は無効
                    # 有効
                    chosen_role = self.agent_target_role[_agent_target_id]  # 工作員が選んだ役職
                    self.confirmed_roles[_agent_target_id] = chosen_role

        # 3.吸血鬼による眷属化判定
        for vampire_player_id in self.players:
            vampire_role = self.selected_roles.get(vampire_player_id)
            if vampire_role == "vampire":
                vampire_target_id = self.night_targets.get(vampire_player_id)
                vampire_target_role = self.confirmed_roles.get(vampire_target_id)
                if vampire_target_role == "vampire":
                    self.death.add(vampire_player_id)  # 噛んだ吸血鬼は死亡
                else:
                    self.half_vampire.add(vampire_target_id)

        # 4.夜行動結果をDM送信
        await self.send_night_results_dm()

        # 5.議論フェーズへの案内
        self.phase = "morning"
        # メッセージを削除
        if self.session.message:
            try:
                await self.message.delete()
            except discord.NotFound:
                pass
            self.message = None
        view = TimerView(self)
        msg = await channel.send(
            "おはようございます\n"
            "**全員ミュート外してください**\n"
            "タイマーをスタートし議論を始めてください",
            view=view
        )
        self.message = msg

    # 夜行動後の判定結果送信
    async def send_night_results_dm(self):
        for user_id in self.players:
            role = self.selected_roles.get(user_id)
            messages = []

            if role == "seer":
                target_id = self.night_targets.get(user_id)
                if target_id is not None:
                    target_team = self.get_team(target_id)
                    member = self.guild.get_member(target_id)
                    messages.append(f"占いの結果： {member.display_name} は {target_team} です。")
            elif role == "cleric":
                has_monster = any(self.get_team(uid) == "monster" for uid in self.players)
                messages.append(f"聖職者の判定：この中にモンスターは {'存在します' if has_monster else 'いません'}。")
            elif role == "esper":
                used_role_names = set()
                for uid in self.confirmed_roles:
                    role_name = self.get_role_name(uid)
                    if role_name:  # None は無視
                        used_role_names.add(role_name)
                messages.append(f"超能力により使用役職が判明： {', '.join(sorted(used_role_names))}")

            # DM送信
            if messages:
                member = self.guild.get_member(user_id)
                try:
                    await member.send("\n".join(messages))
                except discord.Forbidden:
                    # DM拒否されている場合はチャンネルに通知でも可
                    await self.channel.send(f"<@{user_id}> にDMを送れませんでした。")

    # タイマー
    async def start_timer(self, minutes, channel):
        if self.timer_running:
            return

        self.timer_running = True
        self.end_time = time.monotonic() + minutes * 60

        self.timer_task = asyncio.create_task(self._run_timer(minutes, channel))

    # タイマー表示変更
    async def _run_timer(self, minutes, channel):
        try:
            while True:
                remaining = int(self.end_time - time.monotonic())

                if remaining <= 0:
                    break

                # 更新間隔制御
                if remaining > 30:
                    sleep_time = 60
                elif remaining > 10:
                    sleep_time = 10
                else:
                    sleep_time = 1

                minutes_left = remaining // 60
                seconds_left = remaining % 60
                if remaining > 60:
                    content=(
                        f"## 議論開始\n時間：{minutes}分\n"
                        f"残り：**{minutes_left}分{seconds_left}秒**"
                    )
                else:
                    content=(
                        f"## 議論開始\n時間：{minutes}分\n"
                        f"残り：**{remaining}秒**"
                    )
                await self.message.edit(
                    content=content,
                    view=self
                )

                await asyncio.sleep(min(sleep_time, remaining))

            # メッセージを削除
            if self.session.message:
                try:
                    await self.message.delete()
                except discord.NotFound:
                    pass
                self.message = None
            
            self.phase = "vote"
            
            view = VoteView(self)
            msg = await channel.send(
                f"## 議論終了：全員ミュートにしてください。"
                f"\n**投票の時間です。**"
                f"\n処刑した方が良いと思う相手を選んでください。"
                f"\n自分に投票しても構いません。"
                f"\n全員1票ならだれも処刑されません。"
                f"\n2票以上の最多同票は処刑されます。"
                f"\n〈未選択プレーヤー〉"
                + " ".join(f"<@{uid}>" for uid in self.session.players),
                view=view
            )
            self.message = msg

        except asyncio.CancelledError:
            try:
                await self.message.edit(content="⛔ タイマー終了",view=None)
            except:
                pass
            raise

        finally:
            self.timer_running = False
            self.timer_task = None

    # タイマー終了
    async def cancel_timer(self):
        if self.timer_task:
            self.timer_task.cancel()

    # タイマー延長
    async def extend_timer(self, seconds=60):
        if self.timer_running:
            self.end_time += seconds
    
    # 投票終了処理
    async def after_vote(self, channel):
        # 全員投票済み
        if len(self.vote_done) == len(self.players):
            # メッセージを削除
            if self.message:
                try:
                    await self.message.delete()
                except discord.NotFound:
                    pass
                self.message = None

            self.phase = "hunter_ability"
            # 投票結果の作成
            all_votes = list(self.votes.values()) + list(self.mayor_extra_vote.values())
            if not all_votes:
                penaltys = []
            else:
                vote_counts = Counter(all_votes)
                max_votes = max(vote_counts.values())
                # 全員1票なら該当なし
                if max_votes == 1:
                    penaltys = []
                else:
                    # 最大票数を得たプレーヤーIDをリスト化
                    for uid, count in vote_counts.items():
                        if count == max_votes:
                            penaltys.append(f"<@{uid}>")
                            self.most_votes.add(uid)

            view = VoteResultView(self, channel)
            msg = await channel.send(
                f"投票の結果処刑された人は\n"
                f"{'\n'.join(penaltys) if penaltys else '**誰もいませんでした**'}\n"
                f"狩人を選んだ人は生存者の中から1人を選んで処刑することが出来ます。\n"
                f"しなくても構いません。"
                f"処刑する場合は、30秒以内に選んでください。",
                view=view                
            )
            self.message = msg
            return
        
        # 未選択プレイヤー更新
        unselected = [
            f"<@{uid}>"
            for uid in self.players
            if uid not in self.vote_done
        ]
        content = (
            f"## 議論終了：全員ミュートにしてください。"
            f"\n**投票の時間です。**"
            f"\n処刑した方が良いと思う相手を選んでください。"
            f"\n自分に投票しても構いません。"
            f"\n全員1票ならだれも処刑されません。"
            f"\n2票以上の最多同票は処刑されます。"
            f"\n〈未選択プレーヤー〉"
            + (" ".join(unselected) if unselected else "なし")
        )
        await self.message.edit(content=content, view=self)

    # 最終結果処理
    async def result_progress(self, channel):
        self.phase = "result"





        dead = [
            f"<@{uid}>"
            for uid in self.death
        ]
        view = FinalResultView(self)
        msg = await channel.send(
            f"## 最終結果：全員ミュートを外してください。"
            f"\n今回の死者は"
            f"\n{'\n'.join(dead) if dead else '**誰もいませんでした**'}"
            f"\n『個人公表』ボタン：押したプレーヤーの得点結果を表示します。"
            f"\n『全体公表』ボタン：全員の得点結果をまとめて表示します。",
            view=view
        )
        self.message = msg

        # 専用TCに全員分結果送信
        await self.send_results_to_tc()

    # 専用TCへの結果ログ残し
    async def send_results_to_tc(self):
        guild = self.session.bot.get_guild(1049738686767562762)
        channel = guild.get_channel(1473178005059801240)
        if channel:
            results = [self.get_individual_result_log(uid) for uid in self.players]
            await channel.send("最終結果一覧:\n" + "\n\n".join(results))

    # 専用場所へのログ残し用（名前表示化）
    def get_individual_result_log(self, user_id: int) -> str:
        # ユーザー名
        user = self.guild.get_member(user_id)
        user_name = user.display_name if user else str(user_id)

        # 得点と今回の変動点
        score = self.total_score.get(user_id, 0)
        delta = self.round_score.get(user_id, 0)

        # 投票先
        voted = self.votes.get(user_id,"")
        mayor_extra = self.mayor_extra_vote.get(user_id,"")
        vote_mentions = []
        if voted:
            voted_name = self.guild.get_member(voted)
            vote_mentions.append(voted_name.display_name if voted_name else str(voted))
        if mayor_extra:
            mayor_extra_name = self.guild.get_member(mayor_extra)
            vote_mentions.append(mayor_extra_name.display_name if mayor_extra_name else str(mayor_extra))
        vote_text = ", ".join(vote_mentions) if vote_mentions else "なし"

        # 選択役職
        selected_role = self.selected_roles.get(user_id, "不明")
        selected_role_name = ROLE_DATA[selected_role]["name"]

        # 能力対象
        role_targets = self.night_targets.get(user_id, "")
        if role_targets:
            role_targets_name = self.guild.get_member(role_targets)
            role_targets_text = f"：能力対象({role_targets_name.display_name if role_targets else str(role_targets)})"
        else:
            role_targets_text = ""

        # 工作員の指定役職
        agent_role = self.agent_target_role.get(user_id, "")
        agent_role_name = ROLE_DATA[agent_role]["name"]
        agent_role_text = f"({agent_role_name})" if agent_role_name else ""

        # 吸血鬼の投票の吸血
        vampire_target = self.vampire_target.get(user_id, "")
        if vampire_target:
            vampire_target_name = self.guild.get_member(vampire_target)
            vampire_target_text = f"：吸血({vampire_target_name.display_name if vampire_target else str(vampire_target_name)})"
        else:
            vampire_target_text = ""

        # 確定役職
        confirmed_role = self.confirmed_roles.get(user_id, "不明")
        confirmed_role_name = ROLE_DATA[confirmed_role]["name"]

        # 吸血による半吸血鬼化
        half_vampire = self.half_vampire.get(user_id, False)
        half_vampire_text = "（半吸血鬼）" if half_vampire else ""

        # 生存
        death = self.death.get(user_id, True)
        death_text = "死亡" if death else "生存"

        return (
            f"{user_name}：{score}点（{delta}）：{death_text}"
            f"\n投票先{vote_text}{vampire_target_text}"
            f"\n選択役職：{selected_role_name}{role_targets_text}{agent_role_text}"
            f" → 確定役職：{confirmed_role_name}{half_vampire_text}"
        )
    
    # 個人結果まとめ
    def get_individual_result(self, user_id: int) -> str:
        # 得点と今回の変動点
        score = self.total_score.get(user_id, 0)
        delta = self.round_score.get(user_id, 0)

        # 投票先
        voted = self.votes.get(user_id,"")
        mayor_extra = self.mayor_extra_vote.get(user_id,"")
        vote_mentions = []
        if voted:
            vote_mentions.append(f"<@{voted}>")
        if mayor_extra:
            vote_mentions.append(f"<@{mayor_extra}>")
        vote_text = ", ".join(vote_mentions) if vote_mentions else "なし"

        # 選択役職
        selected_role = self.selected_roles.get(user_id, "不明")
        selected_role_name = ROLE_DATA[selected_role]["name"]

        # 能力対象
        role_targets = self.night_targets.get(user_id, "")
        role_targets_text = f"：能力対象<@{role_targets}>" if role_targets else ""

        # 工作員の指定役職
        agent_role = self.agent_target_role.get(user_id, "")
        agent_role_name = ROLE_DATA[agent_role]["name"]
        agent_role_text = f"({agent_role_name})" if agent_role_name else ""

        # 吸血鬼の投票の吸血
        vampire_target = self.vampire_target.get(user_id, "")
        vampire_target_text = f"：吸血<@{vampire_target}>" if vampire_target else ""

        # 確定役職
        confirmed_role = self.confirmed_roles.get(user_id, "不明")
        confirmed_role_name = ROLE_DATA[confirmed_role]["name"]

        # 吸血による半吸血鬼化
        half_vampire = self.half_vampire.get(user_id, False)
        half_vampire_text = "（半吸血鬼）" if half_vampire else ""

        # 生存
        death = self.death.get(user_id, True)
        death_text = "死亡" if death else "生存"

        return (
            f"<@{user_id}>：{score}点（{delta}）：{death_text}"
            f"\n投票先{vote_text}{vampire_target_text}"
            f"\n選択役職：{selected_role_name}{role_targets_text}{agent_role_text}"
            f" → 確定役職：{confirmed_role_name}{half_vampire_text}"
        )
    

# ====================
# 使用可能役職選択ビュー
class RoleDecisionView(ui.View):
    def __init__(self, session, channel_id: int, author: discord.User):
        super().__init__(timeout=None)
        self.session = session
        self.channel_id = channel_id
        self.author = author
        self.available_roles = set(self.session.available_roles)
        self.page = 0
        self.page_size = 20  # 1ページに表示するカテゴリ数
        self.total_pages = (len(EXPANSION_ROLES) - 1) // self.page_size + 1

        self.update_page_buttons()

    def update_page_buttons(self):
        # 既存のボタンをクリア
        self.clear_items()

        # 現在のページカテゴリを取得
        start_idx = self.page * self.page_size
        end_idx = start_idx + self.page_size
        page_cats = EXPANSION_ROLES[start_idx:end_idx]

        # 4行5列に分けてボタンを配置
        for i, cat in enumerate(page_cats):
            role_name = ROLE_DATA[cat]["name"]
            label = f"✅ {role_name}" if cat in self.available_roles else f"🔲 {role_name}"
            button = ui.Button(label=label, style=discord.ButtonStyle.secondary, row=i // 5)
            button.callback = self.make_toggle_callback(cat)
            self.add_item(button)

        # ページ切替 + 登録完了ボタン（最下段に固定）
        nav_row = ui.Button(label="⬅前のページ", style=discord.ButtonStyle.primary, row=4, disabled=(self.page == 0))
        nav_row.callback = self.prev_page
        self.add_item(nav_row)

        finish_btn = ui.Button(label="登録完了", style=discord.ButtonStyle.success, row=4)
        finish_btn.callback = self.finish
        self.add_item(finish_btn)

        next_btn = ui.Button(label="次のページ➡", style=discord.ButtonStyle.primary, row=4, disabled=(self.page == self.total_pages - 1))
        next_btn.callback = self.next_page
        self.add_item(next_btn)

    # 選択トグル
    def make_toggle_callback(self, role: str):
        async def callback(interaction: discord.Interaction):
            if interaction.user.id != self.author.id:
                await interaction.response.send_message("❌ このボタンは送信者だけ押せます。", ephemeral=True)
                return

            if role in self.available_roles:
                self.available_roles.remove(role)
            else:
                self.available_roles.add(role)

            self.update_page_buttons()
            await self.update_message(interaction)
        return callback
    
    async def update_message(self, interaction: discord.Interaction):
        page_info = f"📄  {self.page + 1} / {self.total_pages} ページ"
        content = (
            f"初期役職『村人』『人狼』『占い師』『狩人』『死にたがり』『怪盗』\n"
            f"追加する役職を選んでください\n{page_info}"
        )
        await interaction.response.edit_message(content=content, view=self)

    # 登録完了
    async def finish(self, interaction: discord.Interaction):
        if interaction.user.id != self.author.id:
            await interaction.response.send_message("❌ このボタンは送信者だけ押せます。", ephemeral=True)
            return

        self.session.available_roles = list(self.available_roles)

        cats_str = ", ".join(self.session.available_roles)
        await interaction.response.send_message(f"✅ 使用可能な役職を登録しました！\n選択カテゴリ：{cats_str}")
        
        try:
            await interaction.message.delete()
        except:
            pass

    # ページ切替
    async def prev_page(self, interaction: discord.Interaction):
        if interaction.user.id != self.author.id:
            await interaction.response.send_message("❌ このボタンは送信者だけ押せます。", ephemeral=True)
            return
        if self.page > 0:
            self.page -= 1
            self.update_page_buttons()
            await self.update_message(interaction)
        else:
            await interaction.response.defer()

    async def next_page(self, interaction: discord.Interaction):
        if interaction.user.id != self.author.id:
            await interaction.response.send_message("❌ このボタンは送信者だけ押せます。", ephemeral=True)
            return
        max_page = (len(EXPANSION_ROLES) - 1) // self.page_size
        if self.page < max_page:
            self.page += 1
            self.update_page_buttons()
            await self.update_message(interaction)
        else:
            await interaction.response.defer()

# ====================
# タイマーモーダル
class TimerModal(discord.ui.Modal, title="議論時間を入力してください（分）"):
    text_input = discord.ui.TextInput(
        label="議論時間を入力してください（分）",
        placeholder="1～20（分）※正の整数",
        required=True,
        max_length=2
    )
    
    def __init__(self, session):
        super().__init__()
        self.session = session

    async def on_submit(self, interaction: discord.Interaction):
        try:
            minutes = int(self.time_input.value)
        except ValueError:
            await interaction.response.send_message("整数を入力してください。", ephemeral=True)
            return

        if not 1 <= minutes <= 20:
            await interaction.response.send_message("1～20の整数のみ入力できます。", ephemeral=True)
            return

        try:
            await self.session.message.defer()
        except:
            pass
        
        view = TimerControlView(self.session)
        msg = await interaction.channel.send("タイマー開始準備中...",view=view)
        self.session.message = msg
        await self.session.start_timer(minutes, interaction.channel)

# 狩人能力対象セレクト
class HunterSelect(discord.ui.Select):
    def __init__(self, session):
        self.session = session
        options = [
            discord.SelectOption(label=p.user.display_name, value=str(p.id))
            for p in session.players.values()
            if not session.death.get(p.id, False)  # 生存者のみ
        ]
        super().__init__(
            placeholder="選択してください",
            options=options
        )

    async def callback(self, interaction: discord.Interaction):
        # すでに次フェーズなら何もしない
        if self.session.phase != "hunter_ability":
            for item in self.view.children:
                item.disabled = True
            await interaction.response.edit_message(view=self.view)
        
        self.session.selected_roles[interaction.user.id] = self.values[0]
        self.session.death.add(self.values[0])

        await interaction.response.send_message(
            "<@{self.values[0]}>を撃ちました。",
            ephemeral=True
        )

# 狩人能力対象ビュー
class HunterSelectView(discord.ui.View):
    def __init__(self, session, user_id):
        super().__init__(timeout=None)
        self.add_item(HunterSelect(session, user_id))

# 村長2回目投票セレクト
class MayorSecondSelect(discord.ui.Select):
    def __init__(self, session):
        self.session = session
        options = []
        for user_id in self.session.players:
            member = self.session.guild.get_member(user_id)
            if member:
                options.append(
                    discord.SelectOption(
                        label=member.display_name,
                        value=str(user_id)
                    )
                )
        options.append(
            discord.SelectOption(
                label="パス",
                value="pass"
            )
        )

        super().__init__(
            placeholder="2票目を選択",
            min_values=1,
            max_values=1,
            options=options
        )

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        user_id = interaction.user.id
        value = self.values[0]

        if value == "pass":
            await interaction.followup.send(
                "2回目の投票はパスしました。",
                ephemeral=True
            )
        else:
            target_id = int(value)
            self.session.mayor_extra_vote[user_id] = target_id
            await interaction.response.send_message(
                "<2回目は @{target_id}> に投票しました。",
                ephemeral=True
            )

        # 投票完了
        self.session.vote_done.add(user_id)
        # 投票終了判定
        await self.session.after_vote(interaction.channel)

# 村長2回目投票ビュー
class MayorSecondVoteView(discord.ui.View):
    def __init__(self, session):
        super().__init__(timeout=None)
        self.add_item(MayorSecondSelect(session))

# 投票セレクト
class VoteChoiceSelect(discord.ui.Select):
    def __init__(self, session):
        self.session = session
        options = []
        for user_id in self.session.players:
            member = self.session.guild.get_member(user_id)
            if member:
                options.append(
                    discord.SelectOption(
                        label=member.display_name,
                        value=str(user_id)
                    )
                )

        super().__init__(
            placeholder="投票先を選択",
            min_values=1,
            max_values=1,
            options=options
        )

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        target_id = int(self.values[0])
        user_id = interaction.user.id
        role = self.session.selected_roles.get(user_id)

        # 吸血鬼の投票変更
        if role == "vampire":
            target_role = self.session.confirmed_roles.get(target_id)
            if target_role == "vampire":
                self.session.death.add(user_id)  # 噛んだ吸血鬼は死亡
            else:
                self.session.half_vampire.add(target_id)
            await interaction.followup.send(
                f"<@{target_id}> を噛み、眷属化を行いました。",
                ephemeral=True
            )
        # 通常投票結果保存
        else:
            self.session.votes[user_id] = target_id

            # 村長なら2回目へ
            if role == "mayor":
                view = MayorSecondVoteView(self.session)
                await interaction.followup.send(
                    f"1回目は <@{target_id}> に投票しました。\n"
                    f"2回目の投票先を選んでください。\n"
                    f"2回目の投票は**パス**も出来ます",
                    view=view,
                    ephemeral=True
                )
                return
            
            await interaction.followup.send(
                f"<@{target_id}> に投票しました。",
                ephemeral=True
            )

        # 投票完了
        self.session.vote_done.add(user_id)
        # 投票終了判定
        await self.session.after_vote(interaction.channel)

# 投票セレクトビュー
class VoteSelectView(discord.ui.View):
    def __init__(self, session):
        super().__init__(timeout=None)
        self.add_item(VoteChoiceSelect(session))

# 役職能力対象セレクト
class NightTargetSelect(discord.ui.Select):
    def __init__(self, session, user_id):
        self.session = session
        self.user_id = user_id
        options = []

        for uid in session.players:
            if uid == user_id:
                continue

            member = session.guild.get_member(uid)
            if member:
                options.append(
                    discord.SelectOption(
                        label=member.display_name,
                        value=str(uid)
                    )
                )

        super().__init__(placeholder="対象を選んでください", options=options)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        # すでに次フェーズなら無効化
        if self.session.phase != "night":
            for item in self.view.children:
                item.disabled = True
            await interaction.response.edit_message(view=self.view)
            return
        user_id = interaction.user.id
        role = self.session.selected_roles.get(user_id)
        # 能力対象を保存
        target_id = int(self.values[0])
        self.session.night_targets[user_id] = target_id

        # セレクト削除（2重操作無効）
        for item in self.view.children:
            item.disabled = True
        try:
            await interaction.message.edit(view=self.view)
        except discord.NotFound:
            pass
        
        if role == "agent":
            view = AgentView(self.session)
            await interaction.followup.send(
                f"<@{target_id}> さんを選択しました"
                "塗り替える役職を選んでください",
                view=view,
                ephemeral=True
            )
            return

        # 行動完了
        self.session.night_done.add(user_id)

        await interaction.followup.send(
            f"<@{target_id}> さんを選択しました",
            ephemeral=True
        )

        # 全員完了チェック
        async with self.session.lock:
            if all(p in self.session.night_done for p in self.session.players):
                await self.session.advance_phase(interaction.channel)

# 役職能力対象セレクトビュー
class NightTargetSelectView(discord.ui.View):
    def __init__(self, session, user_id):
        super().__init__(timeout=None)
        self.add_item(NightTargetSelect(session, user_id))

# ====================
# 最終結果ビュー
class FinalResultView(ui.View):
    def __init__(self, session):
        super().__init__(timeout=None)
        self.session = session
        
    @discord.ui.button(label="個人公表", style=discord.ButtonStyle.primary)
    async def personal_result(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        user_id = interaction.user.id
        if user_id in self.session.individual_pressed:
            await interaction.followup.send(
                "既に公表済みです。",
                ephemeral=True
            )
            return
        
        if user_id not in self.session.players:
            await interaction.followup.send(
                "あなたはゲーム参加者ではありません。",
                ephemeral=True
            )
            return
        
        self.session.individual_pressed.add(user_id)

        # 個人結果作成（ここは session に合わせて調整）
        result_text = self.session.get_individual_result(user_id)
        await interaction.response.send_message(result_text, ephemeral=True)

        # 全員押したらボタン無効化
        if len(self.session.individual_pressed) == len(self.session.players):
            for child in self.children:
                child.disabled = True
            try:
                await self.message.edit(view=self)
            except discord.NotFound:
                pass

            # セッション削除
            self.session.reset_round()
    
    @discord.ui.button(label="全体公表", style=discord.ButtonStyle.green)
    async def whole_result(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        user_id = interaction.user.id
        if user_id != self.session.owner_id:
            await interaction.followup.send(
                "このボタンは進行役のみが押せます",
                ephemeral=True
            )
            return
        
        # ボタン無効化
        for child in self.children:
            child.disabled = True
        try:
            await self.message.edit(view=self)
        except discord.NotFound:
            pass

        # 全員結果送信
        results = [self.session.get_individual_result(uid) for uid in self.session.players]
        await interaction.channel.send("\n".join(results))

        # セッション削除
        self.session.reset_round()

# 投票結果ビュー
class VoteResultView(ui.View):
    def __init__(self, session, channel):
        super().__init__(timeout=30)
        self.session = session
        self.channel = channel
    
    @discord.ui.button(label="狩人実行", style=discord.ButtonStyle.primary)
    async def hunter(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.session.selected_roles[interaction.user.id] != "hunter":
            await interaction.response.send_message(
                "選択役職が**狩人**の場合のみ実行できます。",
                ephemeral=True
            )
            return
        
        view = HunterSelectView(self.session,interaction.user.id)
        await interaction.response.send_message(
            "処刑する相手を選んでください（30秒以内）",
            view=view,
            ephemeral=True
        )
    async def on_timeout(self):
        # 30秒経過で削除
        for item in self.children:
            item.disabled = True
        try:
            await self.session.message.edit(view=self)
        except discord.NotFound:
            pass

        self.session.result_progress(self.channel)

# 投票ビュー
class VoteView(ui.View):
    def __init__(self, session):
        super().__init__(timeout=None)
        self.session = session

    @discord.ui.button(label="投票", style=discord.ButtonStyle.danger)
    async def vote_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id not in self.session.players:
            await interaction.response.send_message(
                "参加者のみ投票できます。",
                ephemeral=True
            )
            return
        
        role = self.session.selected_roles.get(interaction.user.id)

        if role == "vampire":
            content = (
                "吸血鬼を選んだあなたの投票権は眷属化に変更されています。\n"
                "眷属化する相手決めてください。"
            )
        elif role == "mayor":
            content = (
                "村長を選んだあなたの投票権は2回です。\n"
                "1回目の投票先を選んでください"
            )
        else:
            content = "投票先を選んでください。"

        view = VoteSelectView(self.session)
        await interaction.response.send_message(
            content=content,
            view=view,
            ephemeral=True
        )

# タイマー制御用ビュー
class TimerControlView(discord.ui.View):
    def __init__(self, session):
        super().__init__(timeout=None)
        self.session = session

    async def interaction_check(self, interaction: discord.Interaction):
        if interaction.user.id != self.session.owner_id:
            await interaction.response.send_message(
                "このボタンは進行役のみが押せます",
                ephemeral=True
            )
            return False
        return True

    @discord.ui.button(label="＋1分延長", style=discord.ButtonStyle.green)
    async def extend(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.session.extend_timer(60)
        await interaction.response.defer()

    @discord.ui.button(label="議論終了", style=discord.ButtonStyle.red)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.session.cancel_timer()
        await interaction.response.defer()

# タイマービュー
class TimerView(ui.View):
    def __init__(self, session):
        super().__init__(timeout=None)
        self.session = session
    
    @discord.ui.button(label="タイマー", style=discord.ButtonStyle.green)
    async def start_timer(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.session.owner_id:
            await interaction.response.send_message("このボタンは進行役のみが押せます", ephemeral=True)
            return
        
        await interaction.response.send_modal(TimerModal(self.session))

# 工作員ビュー
class AgentView(ui.View):
    def __init__(self, session):
        super().__init__(timeout=None)
        self.session = session
        self.available_roles = set(self.session.available_roles)

        self.agent_role_select_buttons()

    def agent_role_select_buttons(self):
        # 既存のボタンをクリア
        self.clear_items()

        for role in self.available_roles:
            role_name = ROLE_DATA[role]["name"]
            button = ui.Button(label=role_name, style=discord.ButtonStyle.secondary)
            button.callback = self.agent_role_select_callback(role)
            self.add_item(button)

    def agent_role_select_callback(self, role: str):
        async def callback(interaction: discord.Interaction):
            await interaction.response.defer()
            # すでに次フェーズなら何もしない
            if self.session.phase != "night":
                for item in self.view.children:
                    item.disabled = True
                await interaction.response.edit_message(view=self.view)
                return
            user_id = interaction.user.id

            try:
                await interaction.message.edit(view=None)
            except discord.NotFound:
                pass

            # 工作員による役職設定保存
            self.session.agent_target_role[user_id] = role
            # 夜行動終了
            self.session.night_done.add(user_id)

            # 全員完了チェック
            async with self.session.lock:
                if all(p in self.session.night_done for p in self.session.players):
                    await self.session.advance_phase(interaction.channel)
        return callback

# 夜の時間ビュー
class NightView(ui.View):
    def __init__(self, session):
        super().__init__(timeout=None)
        self.session = session
    
    @ui.button(label="夜の行動", style=discord.ButtonStyle.green, row=1)
    async def confirm(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.defer()
        # すでに次フェーズなら何もしない
        if self.session.phase != "night":
            for item in self.view.children:
                item.disabled = True
            await interaction.response.edit_message(view=self.view)
            return
        if interaction.user.id not in self.session.players:
            await interaction.followup.send(
                "あなたはゲーム参加者ではありません",
                ephemeral=True
            )
            return

        role = self.session.selected_roles.get(interaction.user.id)
        role_info = ROLE_DATA.get(role, {})

        night_action = role_info.get("night_action")
        night_message = role_info.get("night_message", "夜の行動は特にありません。")

        # 対象セレクトタイプ
        if night_action and night_action.get("type") == "target":
            await interaction.followup.send(
                night_message,
                view=NightTargetSelectView(self.session, interaction.user.id),
                ephemeral=True
            )
            return

        # 行動なし
        self.session.night_done.add(interaction.user.id)
        await interaction.followup.send(night_message, ephemeral=True)

        # 全員完了チェック
        async with self.session.lock:
            if all(p in self.session.night_done for p in self.session.players):
                await self.session.advance_phase(interaction.channel)

# 役職選択ビュー
class RoleSelectView(ui.View):
    def __init__(self, session):
        super().__init__(timeout=None)
        self.session = session
        self.available_roles = set(self.session.available_roles)

        self.role_select_buttons()

    def role_select_buttons(self):
        # 既存のボタンをクリア
        self.clear_items()

        for role in self.available_roles:
            role_name = ROLE_DATA[role]["name"]
            button = ui.Button(label=role_name, style=discord.ButtonStyle.secondary)
            button.callback = self.role_select_callback(role)
            self.add_item(button)

    def role_select_callback(self, role: str):
        async def callback(interaction: discord.Interaction):
            await interaction.response.defer()
            user_id = interaction.user.id
            if user_id not in self.session.players:
                await interaction.followup.send(
                    "あなたはゲーム参加者ではありません",
                    ephemeral=True
                )
                return
            
            go_to_night = False
            
            # 🔒 ここからロック
            async with self.session.lock:
                # すでに次フェーズなら何もしない
                if self.session.phase != "role_select":
                    return
                # 上書き保存
                self.session.selected_roles[user_id] = role
                self.session.confirmed_roles[user_id] = role

                # 全員選択完了判定
                if len(self.session.selected_roles) == len(self.session.players):
                    self.session.phase = "night"
                    go_to_night = True
                    self.session.message = None

            if go_to_night:
                # メッセージを削除
                if self.session.message:
                    try:
                        await self.session.message.delete()
                    except discord.NotFound:
                        pass
                    self.session.message = None

                view = NightView(self.session)
                msg = await interaction.channel.send(
                    "おやすみなさい\n"
                    "**全員指示があるまでミュートにしてください**\n"
                    "夜の時間です\n"
                    "全員『夜の行動』ボタンを押してください\n"
                    "〈未選択プレーヤー〉\n"
                    + " ".join(f"<@{uid}>" for uid in self.session.players),
                    view=view
                )
                self.session.message = msg
                return
                
            # 未選択プレイヤー更新
            unselected = [
                f"<@{uid}>"
                for uid in self.session.players
                if uid not in self.session.selected_roles
            ]
            content = (
                "あなたの役職を選んでください\n"
                "〈未選択プレーヤー〉\n"
                + (" ".join(unselected) if unselected else "なし")
            )

            await interaction.message.edit(content=content, view=self)

        return callback

# 参加ビュー
class WaitingView(ui.View):
    def __init__(self, session):
        super().__init__(timeout=None)
        self.session = session
    
    @ui.button(label="参加", style=discord.ButtonStyle.green, row=1)
    async def confirm(self, interaction: discord.Interaction, button: ui.Button):
        user_id = interaction.user.id
        if user_id in self.session.players:
            await interaction.response.send_message(
                "すでに参加しています",
                ephemeral=True
            )
            return
        
        self.session.players.add(user_id)

        text = "\n".join([f"<@{p}>" for p in self.session.players])
        await interaction.response.edit_message(
            f"参加者は参加ボタンを押してください\n"
            f"〈参加者一覧〉\n{text}",
            view=self
        )

    @ui.button(label="ゲーム開始", style=discord.ButtonStyle.blurple, row=1)
    async def confirm(self, interaction: discord.Interaction, button: ui.Button):
        if interaction.user.id != self.session.owner_id:
            await interaction.response.send_message("このボタンは進行役のみが押せます", ephemeral=True)
            return
        if len(self.session.players)<3:
            await interaction.response.send_message("3人以上必要です", ephemeral=True)
            return

        # メッセージを削除
        if self.session.message:
            try:
                await self.session.message.delete()
            except discord.NotFound:
                pass
            self.session.message = None
        
        self.session.phase = "role_select"

        # 未選択プレイヤー更新
        unselected = [
            f"<@{uid}>"
            for uid in self.session.players
            if uid not in self.session.selected_roles
        ]
        content = (
            "あなたの役職を選んでください\n"
            "〈未選択プレーヤー〉\n"
            + (" ".join(unselected) if unselected else "なし")
        )
        view = RoleSelectView(self.session)
        msg = await interaction.response.send_message(content=content,view=view)
        self.session.message = msg

# Cog本体
class ChooseWolfCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.choosewolf_sessions = {}
        self.reset_confirm_flags = {}
        self.score_reset_confirm_flags = {}
    
    @app_commands.command(name="一夜人狼_役職設定", description="『一夜の自由な人狼たち』で使用可能な役職を設定します")
    async def role_setting(self, interaction: discord.Interaction):
        async def task(interaction):
            await interaction.response.defer()
            channel_id = interaction.channel.id
            session = self.choosewolf_sessions.get(channel_id)
            if session and session.phase is not None:
                roles = "、".join(
                    ROLE_DATA[role]["name"]
                    for role in session.available_roles
                )
                await interaction.followup.send(
                    f"ゲーム進行中は使用可能役職の変更できません\n"
                    f"〈現在使用可能な役職〉\n{roles}"
                )
                return

            if not session:
                session = ChoosewolfSession(channel_id)
                session.set_roles()
                session.reset_game()
                self.choosewolf_sessions[channel_id] = session

            view = RoleDecisionView(session, interaction.channel.id, interaction.user)

            await interaction.followup.send(
                "初期役職『村人』『人狼』『占い師』『狩人』『死にたがり』『怪盗』\n"
                "追加する役職を選んでください",
                view=view
            )

        await safe_execute(
            self.bot,
            task,
            interaction,
            context=f"一夜狼役職設定"
        )
    
    @app_commands.command(name="一夜人狼_得点リセット", description="『一夜の自由な人狼たち』の合計得点をリセットします")
    async def score_reset(self, interaction: discord.Interaction):
        await interaction.response.defer()
        channel_id = interaction.channel.id
        session = self.choosewolf_sessions.get(channel_id)
        if not session:
            await interaction.followup.send(
                "このTCにはまだゲーム記録はありません",
                ephemeral=True
            )
            return

        if self.score_reset_confirm_flags.get(channel_id):
            # 既にリセット確認済み → ゲーム記録リセット
            session.reset_game()
            await interaction.followup.send(
                "このTCでの自由狼の合計得点をリセットしました"
            )
        else:
            # 初回リセット要求
            if not hasattr(self, "score_reset_confirm_flags"):
                self.score_reset_confirm_flags = {}
            self.score_reset_confirm_flags[channel_id] = True
            await interaction.followup.send(
                "このTCでの自由狼の合計得点をリセットしますか？\nもう一度コマンドを実行するとリセットされます",
            )
            # 1分後にフラグを自動削除
            async def clear_flag():
                await asyncio.sleep(60)
                self.score_reset_confirm_flags.pop(channel_id, None)
            asyncio.create_task(clear_flag())
            return

    @app_commands.command(name="一夜の自由な人狼たち", description="『一夜の自由な人狼たち』を開始します")
    async def start_game(self, interaction: discord.Interaction):
        async def task(interaction):
            await interaction.response.defer()
            channel_id = interaction.channel.id
            session = self.choosewolf_sessions.get(channel_id)
            if session and session.phase is not None:
                # 既存ゲームがある場合
                if self.reset_confirm_flags.get(channel_id):
                    # 既にリセット確認済み → ゲームリセット
                    await interaction.followup.send(
                        "前のゲームをリセットして新しいゲームを開始します", ephemeral=True
                    )
                else:
                    # 初回リセット要求
                    if not hasattr(self, "reset_confirm_flags"):
                        self.reset_confirm_flags = {}
                    self.reset_confirm_flags[channel_id] = True
                    await interaction.followup.send(
                        "このチャンネルでは既にゲームが開催中です。\nもう一度コマンドを実行するとリセットされます",
                        ephemeral=True
                    )
                    # 1分後にフラグを自動削除
                    async def clear_flag():
                        await asyncio.sleep(60)
                        self.reset_confirm_flags.pop(channel_id, None)
                    asyncio.create_task(clear_flag())
                    return
            
            if not session:
                session = ChoosewolfSession(channel_id)
                session.set_roles()
                session.reset_game()
                self.choosewolf_sessions[channel_id] = session
            
            session.reset_round()

            session.guild = interaction.guild
            session.owner_id = interaction.user.id
            session.players.append(interaction.user.id)

            view = WaitingView(session)

            msg = await interaction.followup.send(
                f"参加者は参加ボタンを押してください\n"
                f"〈参加者一覧〉\n"
                f"{interaction.user.mention}",
                view=view
            )
            session.message = msg

        await safe_execute(
            self.bot,
            task,
            interaction,
            context=f"一夜狼開始"
        )

# -------------------------
# Cogロード用
# -------------------------
async def setup(bot: commands.Bot):
    await bot.add_cog(ChooseWolfCog(bot))
