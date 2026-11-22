#Basinga bot 
#Made by Arturo Jorge
#Version: 2.0.0

import io
import os
import random
import discord
import asyncio
import imageio_ffmpeg
from discord.ext import commands
from constants import *
from chistes import load_jokes, find_joke, synthesize, speech_text, JokeAPIError, JokeCacheError
from voice_utils import wait_until_voice_ready

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


voice_locks = {}  # guild id -> Lock, so the bot says only one thing at a time per server


def get_free_voice_lock(ctx):
    """Return the server's voice lock, or None if the bot is already talking.

    Checked before moving the bot, so speech in another channel is never cut off.
    """
    lock = voice_locks.setdefault(ctx.guild.id, asyncio.Lock())
    if lock.locked() or (ctx.voice_client and ctx.voice_client.is_playing()):
        return None
    return lock


async def speak(ctx, text):
    """Join the author's voice channel and say the text with TTS."""
    channel = ctx.author.voice.channel
    vc = ctx.voice_client
    if vc is None:
        vc = await channel.connect()
    elif vc.channel != channel:
        await vc.move_to(channel)

    try:
        audio = await synthesize(text)
    except Exception:
        await ctx.send("I couldn't speak this time.")
        return

    # Right after joining, audio is dropped until voice encryption is ready.
    await wait_until_voice_ready(vc)

    vc.play(discord.FFmpegPCMAudio(io.BytesIO(audio), pipe=True, executable=imageio_ffmpeg.get_ffmpeg_exe()))


@client.command()
async def chiste(ctx, joke_id: int = None):
    if not ctx.author.voice:
        await ctx.send("You need to be in a voice channel to hear a joke.")
        return

    lock = get_free_voice_lock(ctx)
    if lock is None:
        await ctx.send("I'm already telling a joke.")
        return

    async with lock:
        await tell_joke(ctx, joke_id)


async def tell_joke(ctx, joke_id):
    try:
        jokes = await load_jokes()
    except JokeAPIError:
        await ctx.send("I couldn't download jokes, try again later.")
        return
    except JokeCacheError as e:
        await ctx.send(f"res/chistes.json has an error: {e}")
        return

    if joke_id is None:
        joke = random.choice(jokes)
    else:
        joke = find_joke(jokes, joke_id)
        if joke is None:
            await ctx.send(f"There's no joke with id {joke_id}.")
            return

    # Only spoken: the joke text is never sent to the chat.
    await speak(ctx, speech_text(joke))


@chiste.error
async def chiste_error(ctx, error):
    if isinstance(error, commands.BadArgument):
        await ctx.send("The joke id must be a number.")
    else:
        await ctx.send("Something went wrong telling the joke.")
        raise error


@client.command()
async def say(ctx, *, message: commands.clean_content):
    # clean_content turns mentions like <@123> into readable @names.
    if not ctx.author.voice:
        await ctx.send("You need to be in a voice channel so I can talk.")
        return

    lock = get_free_voice_lock(ctx)
    if lock is None:
        await ctx.send("I'm already talking.")
        return

    async with lock:
        await speak(ctx, message)


@say.error
async def say_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("Tell me what to say: &say <message>")
    else:
        await ctx.send("Something went wrong saying that.")
        raise error


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

