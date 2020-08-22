import asyncio
from distutils import util
from typing import Optional, List

import discord
from discord.ext import commands

import core.subsystems.sql as sql
from core import Borealis

from .utils import guildchecks
from .utils.paginator import Pages

def _get_optional_guild(ctx: commands.Context, arg: Optional[int]) -> Optional[discord.Guild]:
    if arg:
        return ctx.bot.get_guild(arg)
    else:
        return ctx.message.guild

def _to_lower(arg) -> str:
    return arg.lower()

class ConfigCog(commands.Cog):
    def __init__(self, bot: Borealis):
        self.bot: Borealis = bot

    @commands.is_owner()
    @commands.group(pass_context=True)
    async def config(self, ctx):
        """General configuration commands."""
        pass

    @config.group(pass_context=True)
    async def guild(self, ctx):
        """Guild configuration commands."""
        pass

    @guild.command(name="info")
    async def guild_info(self, ctx, guild_id: Optional[int]):
        """Prints the current guild's info."""

        guild = _get_optional_guild(ctx, guild_id)

        if not guild:
            if guild_id:
                await ctx.send(f"No guild with ID {guild_id} found.")
            else:
                await ctx.send("We are not in a guild and no guild ID provided.")
            return

        guild_conf = self.bot.Config().get_guild(guild.id)
        if not guild_conf:
            await ctx.send("No special configuration exists for this guild.")
        else:
            embed = discord.Embed(title="Guild Config")

            for name, value in guild_conf.to_embed().items():
                embed.add_field(name=name, value=value)

            await ctx.send(embed=embed)

    @commands.guild_only()
    @guild.command(name="setup")
    async def guild_setup(self, ctx):
        guild_conf = sql.GuildConfig()
        guild_conf.id = ctx.message.guild.id

        author = ctx.author
        channel = ctx.message.channel

        permissions = ctx.message.guild.get_member(self.bot.client.id).guild_permissions

        def check(m: discord.Message) -> bool:
            return m.author == author and m.channel == channel

        def is_yes(m: discord.Message) -> bool:
            return bool(util.strtobool(m.content))

        try:
            await ctx.send("Should the server have moderation features enabled? (`yes`/`no`)")
            msg = await self.bot.wait_for("message", timeout=30.0, check=check)
            guild_conf.admin_actions_enabled = is_yes(msg)

            if not permissions.kick_members or not permissions.ban_members:
                await ctx.send("Missing kick and ban permissions. Cannot moderate the server. Cancelled.")
                return

            await ctx.send("Should the server have subscribing enabled? (`yes`/`no`)")
            msg = await self.bot.wait_for("message", timeout=30.0, check=check)
            guild_conf.subscribes_enabled = is_yes(msg)

            if not permissions.manage_roles:
                await ctx.send("Missing manage roles permissions. Cannot edit subscribers. Cancelled.")
                return

            embed = discord.Embed(title="Guild Config")
            for name, value in guild_conf.to_embed().items():
                embed.add_field(name=name, value=value)
            await ctx.send(embed=embed)
            await ctx.send("Please confirm. (`yes`/`no`)")

            msg = await self.bot.wait_for("message", timeout=30.0, check=check)
            if not is_yes(msg):
                await ctx.send("Cancelled.")
                return
            
            self.bot.Config().commit_guild(guild_conf)
            await ctx.send("Committed.")

        except asyncio.TimeoutError:
            await ctx.send("Setup timed out & cancelled.")
            return
        except ValueError:
            await ctx.send("Invalid input provided. Please answer as required. Cancelled.")
            return
        except RuntimeError as err:
            await ctx.send(err.message)
            return

    @guild.command(name="edit")
    async def guild_edit(self, ctx, guild_id: Optional[int], param: _to_lower, value):
        """Edit a guild's settings and commit them to DB."""
        guild = _get_optional_guild(ctx, guild_id)

        if not guild:
            if guild_id:
                await ctx.send(f"No guild with ID {guild_id} found.")
            else:
                await ctx.send("We are not in a guild and no guild ID provided.")
            return

        guild_conf: Optional[sql.GuildConfig] = self.bot.Config().get_guild(guild.id)
        if not guild_conf:
            await ctx.send("No valid guild found.")
            return

        try:
            if param == "admin_actions_enabled":
                guild_conf.admin_actions_enabled = util.strtobool(value)
            elif param == "subscribes_enabled":
                guild_conf.subscribes_enabled = util.strtobool(value)
            else:
                await ctx.send(f"Unknown parameter: `{param}`.")
                return
        except ValueError:
            await ctx.send(f"Invalid parameter value given: `{value}`.")
            return

        self.bot.Config().commit_guild(guild_conf)
        await ctx.send(f"Committed: set `{param}` to `{value}`.")

    @guild.command(name="delete")
    async def guild_delete(self, ctx, guild_id: Optional[int]):
        guild = _get_optional_guild(ctx, guild_id)

        if not guild:
            if guild_id:
                await ctx.send(f"No guild with ID `{guild_id}`` found.")
            else:
                await ctx.send("We are not in a guild and no guild ID provided.")
            return

        guild_conf: Optional[sql.GuildConfig] = self.bot.Config().get_guild(guild.id)
        if not guild_conf:
            await ctx.send(f"Guild with ID `{guild.id}` is not configured.")
            return

        with sql.SessionManager.scoped_session() as session:
            session.delete(guild_conf)

        self.bot.Config().load_sql()

        await ctx.send(f"Guild setup deleted.")

    @guild.command(name="list")
    async def guild_list(self, ctx):
        data: List[str] = []

        for _, guild in self.bot.Config().guilds.items():
            d_guild = ctx.bot.get_guild(guild.id)

            name = "NOT FOUND"
            if d_guild:
                name = d_guild.name

            data.append(f"{guild.id} - {name}")

        if not len(data):
            await ctx.send("No guilds configured yet.")
            return

        p = Pages(ctx, entries=data, per_page=20)
        p.embed.title = "Configured Guilds"
        p.embed.description = "All configured guilds."
        await p.paginate()

    @guild.command(name="channels")
    async def guild_channels(self, ctx, guild_id: Optional[int]):
        """Show all channels that are set up for the guild."""
        guild = _get_optional_guild(ctx, guild_id)

        if not guild:
            if guild_id:
                await ctx.send(f"No guild with ID {guild_id} found.")
            else:
                await ctx.send("We are not in a guild and no guild ID provided.")
            return

        guild_obj: Optional[sql.GuildConfig] = self.bot.Config().get_guild(guild.id)
        if not guild_obj:
            await ctx.send(f"Guild is not set up.")
            return

        data: List[str] = []
        for channel in guild_obj.channels:
            data.append(f"{channel.id} - {channel.channel_type}")

        if not len(data):
            await ctx.send("No channels setup for this guild.")
            return

        p = Pages(ctx, entries=data, per_page=20)
        p.embed.title = f"Configured Channels ({guild_obj.id})"
        p.embed.description = f"All configured channels for guild {guild_obj.id}."
        await p.paginate()

    @config.group(pass_context=True)
    async def channel(self, ctx):
        """Channel editing commands. Guild must be set up first."""
        pass

    @commands.guild_only()
    @commands.has_permissions(send_messages=True)
    @guildchecks.guild_is_setup()
    @channel.command(name="add")
    async def channel_add(self, ctx, ch_type: sql.ChannelType.from_string):
        author = ctx.author

        existing_channel: Optional[sql.ChannelConfig] = self.bot.Config().get_channel(ctx.channel.id)
        if existing_channel:
            await ctx.send(f"Channel already exists as type {existing_channel.channel_type}.")
            return

        ch: sql.ChannelConfig = sql.ChannelConfig()
        ch.id = ctx.channel.id
        ch.channel_type = ch_type
        ch.guild = self.bot.Config().get_guild(ctx.message.guild.id)

        self.bot.Config().commit_channel(ch)
        await ctx.send(f"Channel added as type {ch_type}.")

    @channel.command(name="delete")
    async def channel_delete(self, ctx, channel: Optional[discord.TextChannel]):
        """Removes the current or specified channel from the special roles channel."""
        if not channel:
            if ctx.channel.guild:
                channel = ctx.channel
            else:
                await ctx.send("Not in a valid channel and no channel specified..")
                return

        ch: Optional[sql.ChannelConfig] = self.bot.Config().get_channel(channel.id)
        if not ch:
            await ctx.send(f"Channel with ID `{channel.id}` is not configured.")
            return

        with sql.SessionManager.scoped_session() as session:
            session.delete(ch)

        self.bot.Config().load_sql()

        await ctx.send("Channel deleted.")

def setup(bot: Borealis):
    bot.add_cog(ConfigCog(bot))
