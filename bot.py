from __future__ import annotations
import os
import discord
import datetime
from discord.ext import commands
from typing import List
from dotenv import load_dotenv
from models import PushUpLog, UserTotal, get_session, create_db_and_tables
from sqlmodel import select

load_dotenv()
token = os.getenv("DISCORD_TOKEN")


class PushUpOption(discord.ui.Button):
    def __init__(self, x: int):
        super().__init__(style=discord.ButtonStyle.secondary, label="\u200b")
        self.x = x
        self.label = f"+{x}"

    async def callback(self, interaction: discord.Interaction):
        assert self.view is not None
        view: PushUpView = self.view
        user_id = str(interaction.user.id)

        try:
            session = next(get_session())
            # Log the push-ups
            log = PushUpLog(user_id=user_id, pushups=self.x)
            session.add(log)

            # Update the user's total
            user_total = session.exec(
                select(UserTotal).where(UserTotal.user_id == user_id)
            ).first()
            if user_total:
                user_total.total_pushups += self.x
            else:
                user_total = UserTotal(user_id=user_id, total_pushups=self.x)
                session.add(user_total)

            session.commit()

            # Get the updated leaderboard
            leaderboard = session.exec(
                select(UserTotal).order_by(UserTotal.total_pushups.desc())
            ).all()

            content = "Leaderboard:\n\n"
            for rank, user in enumerate(leaderboard, start=1):
                entry_user = await bot.fetch_user(int(user.user_id))
                content += (
                    f"{rank}. **{entry_user.name}**: {user.total_pushups} pushups\n"
                )
            # Get the last 5 entries
            last_entries = session.exec(
                select(PushUpLog).order_by(PushUpLog.timestamp.desc()).limit(5)
            ).all()

            content += "\nLast 5 entries:\n"
            for entry in last_entries:
                entry_user = await bot.fetch_user(int(entry.user_id))
                entry.timestamp += datetime.timedelta(hours=2)
                content += f"\n[{entry.timestamp.strftime('%I:%M %p')}] {entry_user.name} added {entry.pushups} pushups"

            await interaction.response.edit_message(content=content, view=view)
        except Exception as e:
            print(e)


# This is our actual board View
class PushUpView(discord.ui.View):
    options: List[PushUpOption]

    def __init__(self):
        super().__init__(timeout=None)
        self.push_up_options = [1, 5, 10, 20]

        for x in self.push_up_options:
            self.add_item(PushUpOption(x))


class PouetBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True

        super().__init__(
            command_prefix=commands.when_mentioned_or("!"), intents=intents
        )

    async def on_ready(self):
        print(f"Logged in as {self.user} (ID: {self.user.id})")
        print("------")


bot = PouetBot()


@bot.command(name="pushup")
async def pushup(ctx: commands.Context):
    await ctx.send("Push up challenge", view=PushUpView())


create_db_and_tables()

bot.run(token)
