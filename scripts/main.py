#Basinga bot 
#Made by Arturo Jorge
#Version: 2.0.0

import os
import discord
import asyncio
from discord.ext import commands
from constants import *

GIF_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'res', 'fish-react.gif')

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

client = commands.Bot(command_prefix='&', intents=intents)

negative_votes = 0
positive_votes = 0
memids = []
voted_users = set()  # Set to track users who have voted

class VoteButtons(discord.ui.View):

    def __init__(self, ctx):
        super().__init__(timeout=30)
        self.ctx = ctx
        self.value = True
        self.votes_event = asyncio.Event()

    @discord.ui.button(label="KICK", style=discord.ButtonStyle.green, emoji="👍")
    async def positive_vote(self, interaction: discord.Interaction, button: discord.ui.Button):
        global positive_votes
        global negative_votes
        user_id = interaction.user.id

        if user_id not in memids:
            await interaction.response.send_message("Only people in the voice channel can vote.", ephemeral=True)
            return

        if user_id in voted_users:
            await interaction.response.send_message("You have already voted.", ephemeral=True)
            return

        voted_users.add(user_id)
        positive_votes += 1
        embed = discord.Embed(color=discord.Color.random())
        embed.set_author(name="Votes:")
        embed.add_field(name=f"F1: {positive_votes} | F2: {negative_votes}", value="------------")
        await interaction.response.edit_message(embed=embed)
        self.votes_event.set()

    @discord.ui.button(label="DON'T KICK", style=discord.ButtonStyle.red, emoji="👎")
    async def negative_vote(self, interaction: discord.Interaction, button: discord.ui.Button):
        global negative_votes
        global positive_votes
        user_id = interaction.user.id

        if user_id not in memids:
            await interaction.response.send_message("Only people in the voice channel can vote.", ephemeral=True)
            return

        if user_id in voted_users:
            await interaction.response.send_message("You have already voted.", ephemeral=True)
            return

        voted_users.add(user_id)
        negative_votes += 1
        embed = discord.Embed(color=discord.Color.random())
        embed.set_author(name="Votes:")
        embed.add_field(name=f"F1: {positive_votes} | F2: {negative_votes}", value="------------")
        await interaction.response.edit_message(embed=embed)
        self.votes_event.set()

    async def on_timeout(self):
        self.value = False
        self.stop()
        self.votes_event.set()  # wake up wait() so the vote ends

    async def wait(self):
        global positive_votes
        global negative_votes
        while self.value and positive_votes < len(memids) / 2 and negative_votes <= len(memids) / 2:
            await self.votes_event.wait()
            self.votes_event.clear()

@client.command()
async def vtk(ctx, *, member: discord.Member):
    global negative_votes
    global positive_votes
    global memids
    global voted_users

    negative_votes = 0
    positive_votes = 0
    memids = []
    voted_users = set()

    if not ctx.author.voice:
        await ctx.send("You need to be in a voice channel to start a votekick.")
        return

    members = ctx.author.voice.channel.members

    for mem in members:
        memids.append(mem.id)

    view = VoteButtons(ctx)
    await ctx.reply(f"{ctx.message.author} wants to kick {member}", view=view)

    await view.wait()

    if positive_votes >= len(memids) / 2:
        await member.move_to(channel=None, reason="Votekick")
        await ctx.send(f"{member} was kicked.")
    else:
        await ctx.send(f"{member} wasn't kicked.")

@client.event
async def on_ready():
    print("The bot is ready!")
    print("-----------------")

@client.command()
async def fishreact(ctx):
    fishes = ('🐟', '🎣', '🐠', '🐡', '🦈', '🐬', '🐳', '🐋', '🦐', '🦑', '🐙')

    if ctx.message.reference is None:
        await ctx.send("Reply to a message to fishreact it.")
        return

    target_id = ctx.message.reference.message_id
    target_message = await ctx.fetch_message(target_id)
    await ctx.message.delete()
    with open(GIF_PATH, 'rb') as f:
        picture = discord.File(f)
        await ctx.send(file=picture)
    for fish in fishes:
        await target_message.add_reaction(fish)
    

@client.command()
async def bazinga(ctx):
    await ctx.send("BAZINGA!")


@client.command()
async def join(ctx):
    if (ctx.author.voice):
        channel = ctx.message.author.voice.channel
        await channel.connect()
    else:
        await ctx.send("Not in a channel, can't join.")

@client.command()
async def leave(ctx):
    if (ctx.voice_client):
        await ctx.guild.voice_client.disconnect()
    else:
        await ctx.send("Not in a voice channel.")

@client.command()
async def prueba(ctx):
    
    view = VoteButtons(ctx)
    await ctx.reply("Vota:", view=view)


        

client.run(BOTTOKEN)

