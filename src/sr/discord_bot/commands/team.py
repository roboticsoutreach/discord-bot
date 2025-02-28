from typing import Mapping, TYPE_CHECKING

import discord
from discord import app_commands

from sr.discord_bot.commands.ui import TeamDeleteConfirm

if TYPE_CHECKING:
    from sr.discord_bot.bot import BotClient

from sr.discord_bot.constants import (
    ROLE_PREFIX,
    TEAM_CATEGORY_NAME,
    TEAM_CHANNEL_PREFIX,
    TEAM_VOICE_CATEGORY_NAME,
)

TEAM_CREATED_REASON = "Created via command by "


@app_commands.guild_only()
@app_commands.default_permissions()
class Team(app_commands.Group):
    def __init__(self) -> None:
        super().__init__(description="Manage teams")


group = Team()


def permissions(
    client: "BotClient", team: discord.Role
) -> Mapping[
    discord.Role | discord.Member,
    discord.PermissionOverwrite,
]:
    if not isinstance(client.guild, discord.Guild):
        return {}

    return {
        client.guild.default_role: discord.PermissionOverwrite(
            read_messages=False,
            send_messages=False,
        ),
        client.volunteer_role: discord.PermissionOverwrite(
            read_messages=True,
            send_messages=True,
        ),
        team: discord.PermissionOverwrite(
            read_messages=True,
            send_messages=True,
        ),
    }


@group.command(  # type:ignore[arg-type]
    name="new",
    description="Creates a role and channel for a team",
)
@app_commands.describe(
    tla="Three Letter Acronym (e.g. SRO)",
    name="Name of the team",
    password="Password required for joining the team",
)
async def new_team(
    interaction: discord.interactions.Interaction["BotClient"],
    tla: str,
    name: str,
    password: str,
) -> None:
    guild: discord.Guild | None = interaction.guild
    if guild is None:
        raise app_commands.NoPrivateMessage()

    category = discord.utils.get(guild.categories, name=TEAM_CATEGORY_NAME)
    role_name = f"{ROLE_PREFIX}{tla.upper()}"

    if discord.utils.get(guild.roles, name=role_name) is not None:
        await interaction.response.send_message(
            f"{role_name} already exists", ephemeral=True
        )
        return

    role = await guild.create_role(
        reason=TEAM_CREATED_REASON + interaction.user.name,
        name=role_name,
        mentionable=True,
    )
    channel = await guild.create_text_channel(
        reason=TEAM_CREATED_REASON + interaction.user.name,
        name=f"{TEAM_CHANNEL_PREFIX}{tla.lower()}",
        topic=name,
        category=category,
        overwrites=permissions(interaction.client, role),
    )
    interaction.client.set_password(tla, password)
    await interaction.response.send_message(
        f"{role.mention} and {channel.mention} created!", ephemeral=True
    )


@group.command(  # type:ignore[arg-type]
    name="delete",
    description="Deletes a role and channel for a team",
)
@app_commands.describe(
    tla="Three Letter Acronym (e.g. SRO)",
)
async def delete_team(
    interaction: discord.interactions.Interaction["BotClient"], tla: str
) -> None:
    guild: discord.Guild | None = interaction.guild
    if guild is None:
        raise app_commands.NoPrivateMessage()
    role: discord.Role | None = discord.utils.get(
        guild.roles, name=f"{ROLE_PREFIX}{tla.upper()}"
    )

    if role is None:
        await interaction.response.send_message(
            f"Team {tla.upper()} does not exist", ephemeral=True
        )
        return

    view = TeamDeleteConfirm(guild, tla)

    await interaction.response.send_message(
        f"Are you sure you want to delete Team {tla.upper()}?\n\n"
        f"This will kick all of its members.",
        view=view,
        ephemeral=True,
    )
    await view.wait()
    if view.value:
        await interaction.edit_original_response(
            content=f"_Deleting Team {tla.upper()}..._", view=None
        )
        reason = f"Team removed by {interaction.user.name}"
        if role is not None:
            for member in role.members:
                await member.send(f"Your {guild.name} team has been removed.")
                await member.kick(reason=reason)

            for channel in guild.channels:
                if channel.name.startswith(f"{TEAM_CHANNEL_PREFIX}{tla.lower()}"):
                    await channel.delete(reason=reason)

            await role.delete(reason=reason)
            interaction.client.remove_password(tla)

            if isinstance(
                interaction.channel, discord.abc.GuildChannel
            ) and not interaction.channel.name.startswith(
                f"{TEAM_CHANNEL_PREFIX}{tla.lower()}"
            ):
                await interaction.edit_original_response(
                    content=f"Team {tla.upper()} has been deleted"
                )
    else:
        await interaction.delete_original_response()


@group.command(  # type:ignore[arg-type]
    name="voice",
    description="Create a voice channel for a team",
)
@app_commands.describe(
    tla="Three Letter Acronym (e.g. SRO)",
)
async def create_voice(
    interaction: discord.interactions.Interaction["BotClient"], tla: str
) -> None:
    guild: discord.Guild | None = interaction.guild
    if guild is None:
        raise app_commands.NoPrivateMessage()

    role: discord.Role | None = discord.utils.get(
        guild.roles, name=f"{ROLE_PREFIX}{tla.upper()}"
    )
    if role is None:
        await interaction.response.send_message(
            f"Team {tla.upper()} does not exist", ephemeral=True
        )
        return

    category = discord.utils.get(guild.categories, name=TEAM_VOICE_CATEGORY_NAME)
    channel = await guild.create_voice_channel(
        f"{TEAM_CHANNEL_PREFIX}{tla.lower()}",
        category=category,
        overwrites=permissions(interaction.client, role),
    )
    await interaction.response.send_message(
        f"{channel.mention} created!", ephemeral=True
    )


@group.command(  # type:ignore[arg-type]
    name="channel",
    description="Create a secondary channel for a team",
)
@app_commands.describe(
    tla="Three Letter Acronym (e.g. SRO)",
    suffix="Channel name suffix (e.g. design)",
)
async def create_team_channel(
    interaction: discord.interactions.Interaction["BotClient"],
    tla: str,
    suffix: str,
) -> None:
    guild: discord.Guild | None = interaction.guild
    if guild is None:
        raise app_commands.NoPrivateMessage()

    role: discord.Role | None = discord.utils.get(
        guild.roles, name=f"{ROLE_PREFIX}{tla.upper()}"
    )
    if role is None:
        await interaction.response.send_message("Team does not exist", ephemeral=True)
        return

    main_channel = discord.utils.get(
        guild.text_channels, name=f"{TEAM_CHANNEL_PREFIX}{tla.lower()}"
    )
    category = discord.utils.get(guild.categories, name=TEAM_CATEGORY_NAME)

    if category is None or main_channel is None:
        await interaction.response.send_message(
            f"Team {tla.upper()} does not exist", ephemeral=True
        )
        return

    new_channel = await guild.create_text_channel(
        name=f"{TEAM_CHANNEL_PREFIX}{tla.lower()}-{suffix.lower()}",
        category=category,
        overwrites=permissions(interaction.client, role),
        position=main_channel.position + 1,
        reason=TEAM_CREATED_REASON,
    )
    await interaction.response.send_message(
        f"{new_channel.mention} created!", ephemeral=True
    )


async def _export_team(
    team_tla: str,
    only_teams: bool,
    guild: discord.Guild,
    interaction: discord.interactions.Interaction["BotClient"],
) -> str:
    main_channel = discord.utils.get(
        guild.text_channels, name=f"team-{team_tla.lower()}"
    )
    if main_channel is None and not isinstance(main_channel, discord.abc.GuildChannel):
        raise app_commands.AppCommandError("Invalid TLA")

    password = interaction.client.passwords[team_tla]
    commands = [
        f"/team new tla:{team_tla} name:{main_channel.topic} password:{password}"
    ]

    if not only_teams:
        channels = filter(
            lambda c: c.name.startswith(f"team-{team_tla.lower()}-"),
            guild.text_channels,
        )
        for channel in channels:
            suffix = channel.name.removeprefix(f"team-{team_tla.lower()}-")
            commands.append(f"/team channel tla:{team_tla} suffix:{suffix}")

        has_voice: bool = (
            discord.utils.get(guild.voice_channels, name=f"team-{team_tla.lower()}")
            is not None
        )
        if has_voice:
            commands.append(f"/team voice tla:{team_tla}")

        return "\n".join(commands) + "\n"
    return ""


@group.command(  # type:ignore[arg-type]
    name="export",
    description="Outputs all commands needed to create a team (or all teams)",
)
@app_commands.describe(
    tla="Three Letter Acronym (e.g. SRO)",
    only_teams="Only creates teams without extra channels",
)
async def export_team(
    interaction: discord.interactions.Interaction["BotClient"],
    tla: str | None = None,
    only_teams: bool = False,
) -> None:
    guild: discord.Guild | None = interaction.guild
    if guild is None:
        raise app_commands.NoPrivateMessage()

    await interaction.response.defer(thinking=True, ephemeral=True)

    output = "```\n"

    if tla is None:
        for team_role in guild.roles:
            if team_role.name.startswith(ROLE_PREFIX):
                output += await _export_team(
                    team_role.name.removeprefix(ROLE_PREFIX),
                    only_teams,
                    guild,
                    interaction,
                )
    else:
        output = output + await _export_team(tla, only_teams, guild, interaction)
    output = output + "\n```"
    await interaction.followup.send(content=output, ephemeral=True)


def _repair_permissions_status_msg(cur_team: int, num_teams: int) -> str:
    return f"Repairing permissions... {cur_team}/{num_teams} teams processed"


@group.command(  # type:ignore[arg-type]
    name="repair-permissions",
    description="Reset channel and team permissions",
)
async def repair_permissions(
    interaction: discord.interactions.Interaction["BotClient"],
) -> None:
    guild: discord.Guild | None = interaction.guild
    if guild is None:
        raise app_commands.NoPrivateMessage()

    team_roles = [role for role in guild.roles if role.name.startswith(ROLE_PREFIX)]

    await interaction.response.defer(
        thinking=True,
        ephemeral=True,
    )
    await interaction.edit_original_response(
        content=_repair_permissions_status_msg(0, len(team_roles))
    )

    for index, role in enumerate(team_roles):
        tla = role.name.removeprefix(ROLE_PREFIX)
        channels = [
            channel
            for channel in guild.channels
            if channel.name.startswith(TEAM_CHANNEL_PREFIX + tla)
        ]
        channel_permissions = permissions(interaction.client, role)
        for channel in channels:
            for channel_role, overwrites in channel_permissions.items():
                await channel.set_permissions(target=channel_role, overwrite=overwrites)
        await role.edit(mentionable=True)
        await interaction.edit_original_response(
            content=_repair_permissions_status_msg(index + 1, len(team_roles))
        )

    await interaction.edit_original_response(content="Repairing permissions... done!")
