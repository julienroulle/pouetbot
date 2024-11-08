from __future__ import annotations
import os
import discord
from discord.ext import commands
from typing import List
from dotenv import load_dotenv
from models import (
    PushUpLog,
    UserTotal,
    create_db_and_tables,
    engine,
    get_session,
)
from sqlmodel import Session, select
from sqlalchemy import func
from datetime import datetime, time, timedelta, UTC

import logging

load_dotenv()
token = os.getenv("DISCORD_TOKEN")

map_user_id_to_name = {
    "190104710060048384": "kendaryth",
    "272849004927123466": "macmaseb",
    "440181001742712852": "pionks",
    "384452097048969217": "spirine",
    "268368259953328129": "zboobas",
    "444421186907275265": "oboulland",
}


class PushUpOption(discord.ui.Button):
    def __init__(self, x: int):
        super().__init__(style=discord.ButtonStyle.secondary, label="\u200b")
        self.x = x
        self.label = f"+{x}"

    async def callback(self, interaction: discord.Interaction):
        assert self.view is not None
        view: PushUpView = self.view
        user_id = str(interaction.user.id)

        async with get_session() as session:
            try:
                # Log the push-ups
                log = PushUpLog(user_id=user_id, pushups=self.x)
                session.add(log)

                # Update the user's total
                user_total = await session.execute(
                    select(UserTotal).where(UserTotal.user_id == user_id)
                )
                user_total = user_total.first()[0]
                if user_total:
                    user_total.total_pushups += self.x
                else:
                    user_total = UserTotal(
                        user_id=user_id, total_pushups=self.x
                    )
                    session.add(user_total)

                # Get the updated leaderboard
                leaderboard = await session.execute(
                    select(UserTotal).order_by(UserTotal.total_pushups.desc())
                )

                content = "Leaderboard:\n\n"
                for rank, user in enumerate(leaderboard, start=1):
                    user = user[0]
                    content += f"{rank}. **{map_user_id_to_name[user.user_id]}**: {user.total_pushups} pushups\n"

                # Get the total pushups for each user for the current day
                today = (datetime.now(UTC) + timedelta(hours=1)).date()
                today_start = datetime.combine(today, time.min) - timedelta(
                    hours=1
                )
                today_end = datetime.combine(today, time.max) - timedelta(
                    hours=1
                )

                daily_totals = await session.execute(
                    select(
                        PushUpLog.user_id,
                        func.sum(PushUpLog.pushups).label("total_pushups"),
                    )
                    .where(PushUpLog.timestamp.between(today_start, today_end))
                    .group_by(PushUpLog.user_id)
                    .order_by(func.sum(PushUpLog.pushups).desc())
                )

                content += "\nToday's Pushup Totals:\n"
                for user_id, total_pushups in daily_totals:
                    content += f"\n{map_user_id_to_name[user_id]}: {total_pushups} pushups"

                # If there are no entries for today
                if not daily_totals:
                    content += "\nNo pushups recorded today yet!"

                await session.commit()
                await interaction.response.edit_message(
                    content=content, view=view
                )
            except Exception:
                logging.exception()
                await session.rollback()


# This is our actual board View
class PushUpView(discord.ui.View):
    options: List[PushUpOption]

    def __init__(self):
        super().__init__(timeout=None)
        self.push_up_options = [1, 5, 10, 15, 20]

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
        await create_db_and_tables()


bot = PouetBot()


@bot.command(name="pushup")
async def pushup(ctx: commands.Context):
    await ctx.send("Push up challenge", view=PushUpView())


bot.run(token)
