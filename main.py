import discord
import discord.ext
import random
import math
import datetime
from dotenv import load_dotenv, dotenv_values
import os, json, re
from time import sleep
with open('channels.json','r') as f:
    CHANNEL_LAYOUT=json.load(f)

load_dotenv()

TOKEN = os.getenv("TOKEN")
GUILD_ID = int(os.getenv("GUILD_ID"))
ADMIN_ROLE_ID = int(os.getenv("ADMIN_ROLE_ID"))
BOT_ROLE_ID = 0

description = '''A CTF Team bot for setting up CTF participation in a clean way.

Made by se.al'''

def clean_string(input_string):
    # Use regular expression to replace all characters except [a-z0-9-] with nothing
    cleaned_string = re.sub(r'[^a-z0-9- ]+', '', input_string)
    return cleaned_string

# setting up the bot
intents = discord.Intents.default()
# if you don't want all intents you can do discord.Intents.default()
client = discord.Client(intents=intents)
tree = discord.app_commands.CommandTree(client)

async def make_channel(category,ch,chname):
    if ch['type'] == "text":
        c = await category.create_text_channel(name=chname)
    elif ch['type'] == "forum":
        c = await category.create_forum(name=chname)
    elif ch['type'] == "voice":
        c = await category.create_voice_channel(name=chname)
    return c

@tree.command(name="rm", description="Remove a CTF",guild=discord.Object(id=GUILD_ID))
async def slash_command(interaction: discord.Interaction, name: str):    
    print(f'[{interaction.user.id}] - ran {interaction.command.name}')
    if interaction.user.guild_permissions.administrator or interaction.user.id == 630874656198361099:
        await interaction.response.defer()
        guild = interaction.guild
        role = discord.utils.get(guild.roles, name=name)
        for cat in CHANNEL_LAYOUT:
            catname=cat['name']
            catname = catname.replace('<NAME>',name,1)
            category = discord.utils.get(guild.categories, name=catname)
            if category:
                for channel in category.channels:
                    try:
                        await channel.delete()
                    except:
                        return await interaction.followup.send(f'CTF `{name}` could not delete the channel <#{channel.id}>.')
                await category.delete()
            else:
                return await interaction.followup.send(f'CTF `{name}` could not be removed as the category could not be found.')
        if role:
            try:
                await role.delete()
            except:
                return await interaction.followup.send(f'Unable to delete `{role.name}` role.')
        return await interaction.followup.send(f'CTF `{name}` was removed!')
    else:
        return await interaction.response.send_message('You are not an admin!',ephemeral=True)

@tree.command(name="archive", description="Archive a CTF",guild=discord.Object(id=GUILD_ID))
async def slash_command(interaction: discord.Interaction, name: str):    
    print(f'[{interaction.user.id}] - ran {interaction.command.name}')
    if interaction.user.guild_permissions.administrator or interaction.user.id == 630874656198361099:
        await interaction.response.defer()
        guild = interaction.guild
        role = discord.utils.get(guild.roles, name=name)
        year = datetime.date.today().year
        quarter = math.ceil(datetime.datetime.now().month/3.)
        cat_name = f"Archive {year} {quarter}/4"
        archival_category = discord.utils.get(guild.categories, name=cat_name)
        if not archival_category:
            archival_category = await guild.create_category(cat_name)
        for cat in CHANNEL_LAYOUT:
            catname = cat['name']
            catname = catname.replace('<NAME>',name,1)
            category = discord.utils.get(guild.categories, name=catname)
            if category:
                for ch in cat['channels']:
                    chname = ch['name']
                    chname = chname.replace('<NAME>',name,1)
                    channel = discord.utils.get(guild.channels, name=chname)
                    if not channel:
                        chname = ch['name']
                        chname = chname.replace('<NAME>','',1)
                        channel = discord.utils.get(guild.channels, name=clean_string(name.lower()).strip().replace(' ','-')+chname)
                    if channel:
                        if 'archive' in ch.keys():
                            if ch['archive'] == True and type(ch['archive']) == bool:
                                await channel.set_permissions(guild.default_role, view_channel=True, send_messages=False)
                                if len(CHANNEL_LAYOUT) != 1:
                                    await channel.edit(name=f"{catname}-{chname}")
                                await channel.edit(category=archival_category,position=len(archival_category.channels))
                            else:
                                await channel.delete()
                        else:
                            await channel.delete()
                await category.delete()
        return await interaction.followup.send(f'CTF `{name}` was archived!')
    else:
        return await interaction.response.send_message('You are not an admin!',ephemeral=True)

@tree.command(name="make", description="Create a CTF",guild=discord.Object(id=GUILD_ID))
async def slash_command(interaction: discord.Interaction, name: str):    
    print(f'[{interaction.user.id}] - ran {interaction.command.name}')
    if interaction.user.guild_permissions.administrator or interaction.user.id == 630874656198361099:
        await interaction.response.defer()
        guild = interaction.guild
        channel = interaction.channel
        try:
            adminrole = discord.utils.get(guild.roles, id=ADMIN_ROLE_ID)
        except:
            return await interaction.followup.send('Could not find the `admin` role.')
        try:
            for role in guild.roles:
                if len(role.members) == 1 and role.members[0].id == client.user.id and role.permissions.administrator:
                    botrole = discord.utils.get(guild.roles, id=role.id)
        except:
            return await interaction.followup.send('Could not find the `bot` role.')
        try:
            role = await guild.create_role(name=name)
            col = discord.Color(5860729)
            await role.edit(color=col)
        except:
            return await interaction.followup.send('Could not create/manage the new role!')
        for cat in CHANNEL_LAYOUT:
            catname=cat['name']
            catname = catname.replace('<NAME>',name,1)
            try:
                category = await guild.create_category(catname)
            except:
                return await interaction.followup.send('Could not create the new category!')
            await category.set_permissions(botrole, read_messages=True, send_messages=True)
            await category.set_permissions(role, read_messages=True, send_messages=True)
            await category.set_permissions(guild.default_role, read_messages=False)
            for ch in cat['channels']:
                chname=ch['name']
                chname =chname.replace('<NAME>',name,1)
                try:
                    channel = await make_channel(category,ch,chname)
                except:
                    return await interaction.followup.send(f'Could not create the {chname} channel!')
                if 'participant_editable' in ch.keys():
                    if ch['participant_editable'] == False and type(ch['participant_editable']) == bool:
                        try:
                            await channel.set_permissions(adminrole, send_messages=True)
                        except:
                            return await interaction.followup.send(f'Unable to set permissions for role `{adminrole.name}` for <#{channel.id}>!')
                        try:
                            await channel.set_permissions(role, read_messages=True, send_messages=False)
                        except:
                            return await interaction.followup.send(f'Unable to set permissions for role `{role.name}` for <#{channel.id}>!')
                    else:
                        try:
                            await channel.set_permissions(role, read_messages=True, send_messages=True)
                        except:
                            return await interaction.followup.send(f'Unable to set permissions for role `{role.name}` for <#{channel.id}>!')
                else:
                    try:
                        await channel.set_permissions(role, read_messages=True, send_messages=True)
                    except:
                        return await interaction.followup.send(f'Unable to set permissions for role `{role.name}` for <#{channel.id}>!')
                try:
                    await channel.set_permissions(guild.default_role, read_messages=False)
                except:
                    return await interaction.followup.send(f'Unable to set permissions for role `@everyone` for <#{channel.id}>!')
                try:
                    await channel.set_permissions(botrole, read_messages=True, send_messages=True)
                except:
                        return await interaction.followup.send(f'Unable to set permissions for role `{botrole.name}` for <#{channel.id}>!')
        try:
            message = await interaction.followup.send(f'Are you playing in `{name}`?')
            await message.add_reaction("👍")
        except:
            return await interaction.followup.send('Could not send the CTF message or could not react to it.')
    else:
        return await interaction.response.send_message('You are not an admin!',ephemeral=True)

# sync the slash command to your server
@client.event
async def on_ready():
    print(f'Syncing trees...')
    await tree.sync(guild=discord.Object(id=GUILD_ID))
    # print "ready" in the console when the bot is ready to work
    print(f'Finding the bots role...')
    guild = discord.utils.get(client.guilds, id=GUILD_ID)
    for role in guild.roles:
        if len(role.members) == 1 and role.members[0].id == client.user.id and role.permissions.administrator:
            BOT_ROLE_ID = role.id
            break
    if BOT_ROLE_ID == 0:
        print('WARNING: No bot role found! Please make sure there is a role unqiue to the bot with Admin permissions! Things will break!')
    print(f'Logged in as {client.user} (ID: {client.user.id})')
    print('------')

# run the bot
client.run(TOKEN)
