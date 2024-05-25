from __future__ import annotations

import uuid

import nextcord
import psycopg2
from dotenv import load_dotenv
from nextcord.ext import application_checks, commands

load_dotenv()
import os
from os import getenv

# if you are asking why there's a "my_" before the values, then it's because self.title overlaps the value in modal


class TagEditModal(nextcord.ui.Modal):
    def __init__(self, db: psycopg2.connection, tag_info: tuple):
        self._db: psycopg2.connection = db
        self._tag: tuple = tag_info
        super().__init__("Edit tag")

        self.my_title = nextcord.ui.TextInput(
            label="Tag Title",
            required=True,
            max_length=60,
            style=nextcord.TextInputStyle.short,
            default_value=self._tag[2],
        )
        self.add_item(self.my_title)

        self.my_content = nextcord.ui.TextInput(
            label="Tag Content",
            required=True,
            max_length=4000,
            style=nextcord.TextInputStyle.paragraph,
            default_value=self._tag[3],
        )
        self.add_item(self.my_content)

    async def callback(self, interaction: nextcord.Interaction) -> None:
        with self._db.cursor() as cursor:
            try:
                cursor.execute(
                    "UPDATE taginfo SET title=%s WHERE id=%s",
                    (self.my_title.value, self._tag[0]),
                )
                cursor.execute(
                    "UPDATE taginfo SET content=%s WHERE id=%s",
                    (self.my_content.value, self._tag[0]),
                )
            except:
                cursor.execute("ROLLBACK")

            self._db.commit()

        await interaction.response.send_message("Done", ephemeral=True)


class TagEditView(nextcord.ui.View):
    def __init__(self, ctx: commands.Context, db: psycopg2.connection, tag: tuple):
        super().__init__()
        self._ctx: commands.Context = ctx
        self._db: psycopg2.connection = db
        self._tag: tuple = tag

    @nextcord.ui.button(label="Edit tag!", style=nextcord.ButtonStyle.green)
    async def create_tag(
        self, button: nextcord.ui.Button, interaction: nextcord.Interaction
    ):
        if interaction.user.id == self._ctx.author.id:
            modal = TagEditModal(self._db, self._tag)
            await interaction.response.send_modal(modal)
        else:
            await interaction.response.send_message("Fool", ephemeral=True)


class TagCreationModal(nextcord.ui.Modal):
    def __init__(self, db: psycopg2.connection):
        self._db: psycopg2.connection = db
        super().__init__("Create tag")

        self.my_name = nextcord.ui.TextInput(
            label="Tag Name",
            required=True,
            max_length=60,
            style=nextcord.TextInputStyle.short,
        )

        self.add_item(self.my_name)

        self.my_title = nextcord.ui.TextInput(
            label="Tag Title",
            required=True,
            max_length=60,
            style=nextcord.TextInputStyle.short,
        )
        self.add_item(self.my_title)

        self.my_content = nextcord.ui.TextInput(
            label="Tag Content",
            required=True,
            max_length=4000,
            style=nextcord.TextInputStyle.paragraph,
        )
        self.add_item(self.my_content)

    async def callback(self, interaction: nextcord.Interaction) -> None:
        with self._db.cursor() as cursor:
            cursor.execute("SELECT * FROM taginfo WHERE name=%s", (self.my_name.value,))
            if not cursor.fetchone():
                id = uuid.uuid4()
                try:
                    cursor.execute(
                        # f"INSERT INTO taginfo VALUES('{id.hex}', '{self.my_name.value}', '{self.my_title.value}', '{self.my_content.value}', '{str(interaction.user.id)}')"
                        f"INSERT INTO taginfo VALUES(%s, %s, %s, %s, %s)",
                        (
                            id.hex,
                            self.my_name.value,
                            self.my_title.value,
                            self.my_content.value,
                            str(interaction.user.id),
                        ),
                    )
                except:
                    cursor.execute("ROLLBACK")
                self._db.commit()
                await interaction.response.send_message("Done", ephemeral=True)
            else:
                await interaction.response.send_message(
                    "Tag already existed", ephemeral=True
                )

        # await interaction.response.send_message("Done", ephemeral=True)


class TagCreationView(nextcord.ui.View):
    def __init__(self, ctx: commands.Context, db: psycopg2.connection):
        super().__init__()
        self._ctx: commands.Context = ctx
        self._db: psycopg2.connection = db

    @nextcord.ui.button(label="Create tag!", style=nextcord.ButtonStyle.green)
    async def create_tag(
        self, button: nextcord.ui.Button, interaction: nextcord.Interaction
    ):
        if interaction.user.id == self._ctx.author.id:
            modal = TagCreationModal(self._db)
            await interaction.response.send_modal(modal)
        else:
            await interaction.response.send_message("Fool", ephemeral=True)


def tag_operation_check(ctx):
    return (
        ctx.author.get_role(1197475623745110109) is not None
    ) or ctx.author.id == 716134528409665586


class TagsNewSlash(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self._bot: commands.Bot = bot
        self._db = psycopg2.connection = psycopg2.connect(
            host=getenv("DBHOST"),
            user=getenv("DBUSER"),
            port=getenv("DBPORT"),
            password=getenv("DBPASSWORD"),
            dbname=getenv("DBNAME"),
        )

    @nextcord.slash_command()
    async def tag(self, interaction: nextcord.Interaction) -> None:
        pass

    @tag.subcommand()
    @application_checks.has_role(1197475623745110109)
    async def create(self, interaction: nextcord.Interaction) -> None:
        await interaction.response.send_modal(TagCreationModal(self._db))

    @tag.subcommand()
    @application_checks.has_role(1197475623745110109)
    async def edit(
        self,
        interaction: nextcord.Interaction,
        tag_name: str = nextcord.SlashOption(
            description="The tag you want",
            required=True,
        ),
    ) -> None:
        """Edit a tag"""
        with self._db.cursor() as cursor:
            cursor.execute("SELECT * FROM taginfo\nWHERE name=%s", (tag_name,))
            if info := cursor.fetchone():
                await interaction.response.send_modal(TagEditModal(self._db, info))
            else:
                await interaction.response.send_message("Invalid tag", ephemeral=True)

    @tag.subcommand()
    async def find(
        self,
        interaction: nextcord.Interaction,
        tag_name: str = nextcord.SlashOption(
            description="The tag you want",
            required=True,
        ),
    ) -> None:
        """Request a tag"""
        with self._db.cursor() as cursor:
            cursor.execute("SELECT * FROM taginfo\nWHERE name=%s", (tag_name,))
            if info := cursor.fetchone():
                # print(info)
                await interaction.send(
                    embed=nextcord.Embed(
                        title=info[2], description=info[3], color=nextcord.Color.red()
                    ).set_footer(text=f"ID {info[0]}. Author ID: {info[4]}")
                )
            else:
                await interaction.send("Fool")

    @tag.subcommand()
    async def delete(
        self,
        interaction: nextcord.Interaction,
        tag_name: str = nextcord.SlashOption(
            description="The tag you want", required=True
        ),
    ) -> None:
        """Delete a tag"""
        with self._db.cursor() as cursor:
            cursor.execute("SELECT * FROM taginfo WHERE name=%s", (tag_name,))
            if info := cursor.fetchone():
                cursor.execute("DELETE FROM taginfo WHERE name=%s", (tag_name,))
                self._db.commit()
                await interaction.send("Done")
            else:
                await interaction.send("Fool")


class TagsNew(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self._bot: commands.Bot = bot
        self._db: psycopg2.connection = psycopg2.connect(
            host=getenv("DBHOST"),
            user=getenv("DBUSER"),
            port=getenv("DBPORT"),
            password=getenv("DBPASSWORD"),
            dbname=getenv("DBNAME"),
        )

    @commands.Cog.listener()
    async def on_message(self, message: nextcord.Message) -> None:
        if message.content.startswith("^"):
            if os.getenv("NO_SPAWN_TAG") == 1:
                return
            with self._db.cursor() as cursor:
                cursor.execute(
                    "SELECT * FROM taginfo\nWHERE name=%s",
                    (message.content[1:],),
                )
                if info := cursor.fetchone():
                    # print(info)
                    await message.channel.send(
                        embed=nextcord.Embed(
                            title=info[2],
                            description=info[3],
                            color=nextcord.Color.red(),
                        ).set_footer(text=f"ID {info[0]}. Author ID: {info[4]}")
                    )
                else:
                    pass

    @commands.group(invoke_without_command=True)
    async def tag(self, ctx: commands.Context, tag_name: str = "null"):
        """Find a tag. Equivalent to `^tag_name` and `oc/find tag_name`."""
        with self._db.cursor() as cursor:
            cursor.execute("SELECT * FROM taginfo\nWHERE name=%s", (tag_name,))
            if info := cursor.fetchone():
                # print(info)
                await ctx.send(
                    embed=nextcord.Embed(
                        title=info[2], description=info[3], color=nextcord.Color.red()
                    ).set_footer(text=f"ID {info[0]}. Author ID: {info[4]}")
                )
            else:
                await ctx.send("Fool")

    @tag.command()
    async def list(self, ctx: commands.Context):
        """List current available tag."""
        with self._db.cursor() as cursor:
            cursor.execute("SELECT name FROM taginfo")
            await ctx.send(cursor.fetchall())

    @commands.command()
    async def find(self, ctx: commands.Context, tag_name: str = "null"):
        """Find a tag."""
        # print("command found")
        # print(tag_name)
        with self._db.cursor() as cursor:
            cursor.execute("SELECT * FROM taginfo\nWHERE name=%s", (tag_name,))
            if info := cursor.fetchone():
                # print(info)
                await ctx.send(
                    embed=nextcord.Embed(
                        title=info[2], description=info[3], color=nextcord.Color.red()
                    ).set_footer(text=f"ID {info[0]}. Author ID: {info[4]}")
                )
            else:
                await ctx.send("Fool")

    @tag.command()
    @commands.check(tag_operation_check)
    async def create(self, ctx: commands.Context):
        """Create a tag."""
        await ctx.send(view=TagCreationView(ctx, self._db))

    @tag.command()
    @commands.check(tag_operation_check)
    async def delete(self, ctx: commands.Context, tag_name: str):
        """Delete a tag."""
        with self._db.cursor() as cursor:
            cursor.execute("SELECT * FROM taginfo WHERE name=%s", (tag_name,))
            if info := cursor.fetchone():
                cursor.execute("DELETE FROM taginfo WHERE name=%s", (tag_name,))
                self._db.commit()
                await ctx.send("Done")
            else:
                await ctx.send("Fool")

    @tag.command()
    @commands.check(tag_operation_check)
    async def edit(self, ctx: commands.Context, tag_name: str):
        """Edit a tag."""
        with self._db.cursor() as cursor:
            cursor.execute("SELECT * FROM taginfo WHERE name=%s", (tag_name,))
            if info := cursor.fetchone():
                await ctx.send(
                    f"Editing tag {tag_name}", view=TagEditView(ctx, self._db, info)
                )
            else:
                await ctx.send("Fool")


def setup(bot):
    bot.add_cog(TagsNew(bot))
    bot.add_cog(TagsNewSlash(bot))
