from __future__ import annotations

from typing import Final, Tuple

from nextcord import Interaction, OptionConverter
from nextcord.ext import commands

__all__: Final[Tuple[str]] = ("SubdomainNameConverter", "SlashSubdomainNameConverter")


class SubdomainNameConverter(commands.Converter):
    async def convert(self, ctx: commands.Context, argument: str) -> str:
        argument = argument.lower()
        if argument.endswith(".is-a.dev"):
            return argument[:-9]
        return argument


class RGBColorTupleConverter(commands.Converter):
    async def convert(self, ctx: commands.Context, argument: str) -> Tuple[str]:
        return argument.split("-")  # type: ignore[reportReturnType]


class SlashSubdomainNameConverter(OptionConverter):
    async def convert(self, interaction: Interaction, value: str) -> str:
        value = value.lower()
        if value.endswith(".is-a.dev"):
            return value[:-9]
        return value
