from typing import List, NamedTuple
from statistics import mean

import discord

from sr.discord_bot.constants import ROLE_PREFIX


class TeamData(NamedTuple):
    """Stores the TLA, number of members and presence of a team supervisor for a team."""

    TLA: str
    members: int = 0

    def __str__(self) -> str:
        return f"{self.TLA:<15} {self.members:>2}"


class TeamsData(NamedTuple):
    """A container for a list of TeamData objects."""

    teams_data: List[TeamData]

    def gen_team_memberships(self, guild: discord.Guild) -> None:
        """Generate a list of TeamData objects for the given guild, stored in teams_data."""
        teams_data = []

        for role in filter(lambda role: role.name.startswith(ROLE_PREFIX), guild.roles):
            team_data = TeamData(
                TLA=role.name[len(ROLE_PREFIX) :],
                members=len(role.members),
            )

            teams_data.append(team_data)

        teams_data.sort(key=lambda team: team.TLA)  # sort by TLA
        self.teams_data.clear()
        self.teams_data.extend(teams_data)

    @property
    def empty_tlas(self) -> List[str]:
        """A list of TLAs for teams with no members or supervisors."""
        return [
            team.TLA
            for team in self.teams_data
            if not team.leader and team.members == 0
        ]

    def team_summary(self) -> str:
        """A summary of the teams."""
        return "\n".join(
            [
                "Members per team",
                *(str(team) for team in self.teams_data),
            ]
        )

    def warnings(self) -> str:
        """A list of warnings for the teams."""
        return "\n".join(
            [
                f"Empty teams: {len(self.empty_tlas)}",
            ]
        )

    def statistics(self) -> str:
        """A list of statistics for the teams."""
        num_teams: int = len(self.teams_data)
        member_counts = [team.members for team in self.teams_data]
        num_members = sum(member_counts)

        min_team = min(self.teams_data, key=lambda x: x.members)
        max_team = max(self.teams_data, key=lambda x: x.members)

        return "\n".join(
            [
                f"Total teams: {num_teams}",
                f"Total participants: {num_members}",
                f"Max team size: {max_team.members} ({max_team.TLA})",
                f"Min team size: {min_team.members} ({min_team.TLA})",
                f"Average team size: {mean(member_counts):.1f}",
            ]
        )
