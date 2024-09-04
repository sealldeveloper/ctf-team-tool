import discord
import discord.ext
import random
import math
import datetime
from dotenv import load_dotenv, dotenv_values
import os, json, re
from emoji import emoji_count
from time import sleep
from tinydb import TinyDB, Query, operations
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_env_variable(var_name, default=None):
    value = os.environ.get(var_name)
    print(value)
    if value is None:
        load_dotenv()  # Load .env file if not already loaded
        value = os.getenv(var_name, default)
        print(value)
    return value

TOKEN = get_env_variable("TOKEN")
GUILD_ID = int(get_env_variable("GUILD_ID", 0))
ADMIN_ROLE_ID = int(get_env_variable("ADMIN_ROLE_ID", 0))

DB_PATH = get_env_variable("DB_PATH", "db.json")
db = TinyDB(DB_PATH)
query = Query()

CHANNELS_PATH = get_env_variable("CHANNELS_PATH", "channels.json")
with open(CHANNELS_PATH, 'r') as f:
    CHANNEL_LAYOUT = json.load(f)

# db = TinyDB('db.json')
# query = Query()
# with open('channels.json','r') as f:
#     CHANNEL_LAYOUT=json.load(f)
    

# load_dotenv()

# TOKEN = os.getenv("TOKEN")
# GUILD_ID = int(os.getenv("GUILD_ID"))
# ADMIN_ROLE_ID = int(os.getenv("ADMIN_ROLE_ID"))
BOT_ROLE_ID = 0

if not db.all():
    db.insert({'reaction_messages':{}})
messages = db.all()[0]['reaction_messages']
print(messages,type(messages))

description = '''A CTF Team bot for setting up CTF participation in a clean way.

Made by se.al / sealldeveloper'''

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

@tree.command(name="rmctf", description="Remove a CTF",guild=discord.Object(id=GUILD_ID))
async def slash_command(interaction: discord.Interaction, name: str):    
    await interaction.response.defer(ephemeral=True)
    print(f'[{interaction.user.id}] - ran {interaction.command.name}')
    if interaction.user.guild_permissions.administrator or interaction.user.id == 630874656198361099:
        if not name:
            return await interaction.edit_original_response(content='Must provide a name.')
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
                        return await interaction.edit_original_response(content=f'CTF `{name}` could not delete the channel <#{channel.id}>.')
                await category.delete()
            else:
                return await interaction.edit_original_response(content=f'CTF `{name}` could not be removed as the category could not be found.')
        if role:
            try:
                await role.delete()
            except:
                return await interaction.edit_original_response(content=f'Unable to delete `{role.name}` role.')
        messages = db.all()[0]['reaction_messages']
        for message_id in messages.keys():
            if messages[message_id]['type'] == 'ctfmenu':
                if name == messages[message_id]['ctfname']:
                    del messages[message_id]
                    for channel in guild.text_channels:
                        try:
                            message = await channel.fetch_message(message_id)
                            if message:
                                await message.delete()
                                break
                        except:
                            message = None
                    break
        db.update({'reaction_messages':messages})
        return await interaction.edit_original_response(content=f'CTF `{name}` was removed!')
    else:
        return await interaction.edit_original_response(content='You are not an admin!')

@tree.command(name="archivectf", description="Archive a CTF",guild=discord.Object(id=GUILD_ID))
async def slash_command(interaction: discord.Interaction, name: str):    
    await interaction.response.defer(ephemeral=True)
    logger.info(f'[{interaction.user.id}] - ran {interaction.command.name}')
    
    if not (interaction.user.guild_permissions.administrator or interaction.user.id == 630874656198361099):
        logger.warning(f'User {interaction.user.id} attempted to use command without permission')
        return await interaction.edit_original_response(content='You are not an admin!')

    if not name:
        logger.warning('Command executed without a name parameter')
        return await interaction.edit_original_response(content='Must provide a name.')

    guild = interaction.guild
    role = discord.utils.get(guild.roles, name=name)
    logger.info(f'Looking for role: {name}, Found: {role is not None}')
    year = datetime.date.today().year
    quarter = math.ceil(datetime.datetime.now().month/3.)
    cat_name = f"Archive {year} {quarter}/4"
    archival_category = discord.utils.get(guild.categories, name=cat_name)
    if not archival_category:
        archival_category = await guild.create_category(cat_name)
    try:
        for cat in CHANNEL_LAYOUT:
            
            catname = cat['name']
            catname = catname.replace('<NAME>',name,1)
            logger.info(f'Processing category: {catname}')
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
    except Exception as e:
        logger.error(f'Error during archiving process: {str(e)}')
        return await interaction.edit_original_response(content=f'An error occurred while archiving: {str(e)}')
    # messages = db.all()[0]['reaction_messages']
    # for message_id in messages.keys():
    #     if messages[message_id]['type'] == 'ctfmenu':
    #         if name == messages[message_id]['ctfname']:
    #             del messages[message_id]
    #             for channel in guild.text_channels:
    #                 try:
    #                     message = await channel.fetch_message(message_id)
    #                     if message:
    #                         await message.delete()
    #                         break
    #                 except:
    #                     message = None
    #             break
    db.update({'reaction_messages':messages})
    logger.info(f'CTF {name} archived successfully')
    return await interaction.edit_original_response(content=f'CTF `{name}` was archived!')

@tree.command(name="makectf", description="Create a CTF",guild=discord.Object(id=GUILD_ID))
async def slash_command(interaction: discord.Interaction, name: str):  
    await interaction.response.defer(ephemeral=True)  
    print(f'[{interaction.user.id}] - ran {interaction.command.name}')
    if interaction.user.guild_permissions.administrator or interaction.user.id == 630874656198361099:
        if not name:
            return await interaction.edit_original_response(content='Must provide a name.')
        guild = interaction.guild
        channel = interaction.channel
        try:
            adminrole = discord.utils.get(guild.roles, id=ADMIN_ROLE_ID)
        except:
            return await interaction.edit_original_response(content='Could not find the `admin` role.')
        try:
            for role in guild.roles:
                if len(role.members) == 1 and role.members[0].id == client.user.id and role.permissions.administrator:
                    botrole = discord.utils.get(guild.roles, id=role.id)
        except:
            return await interaction.edit_original_response(content='Could not find the `bot` role.')
        try:
            role = await guild.create_role(name=name)
            col = discord.Color(5860729)
            await role.edit(color=col)
        except:
            return await interaction.edit_original_response(content='Could not create/manage the new role!')
        for cat in CHANNEL_LAYOUT:
            catname=cat['name']
            catname = catname.replace('<NAME>',name,1)
            try:
                category = await guild.create_category(catname)
            except:
                return await interaction.edit_original_response(content='Could not create the new category!')
            await category.set_permissions(botrole, read_messages=True, send_messages=True)
            await category.set_permissions(role, read_messages=True, send_messages=True)
            await category.set_permissions(guild.default_role, read_messages=False)
            for ch in cat['channels']:
                chname=ch['name']
                chname =chname.replace('<NAME>',name,1)
                try:
                    channel = await make_channel(category,ch,chname)
                except:
                    return await interaction.edit_original_response(content=f'Could not create the {chname} channel!')
                if 'participant_editable' in ch.keys():
                    if ch['participant_editable'] == False and type(ch['participant_editable']) == bool:
                        try:
                            await channel.set_permissions(adminrole, send_messages=True)
                        except:
                            return await interaction.edit_original_response(content=f'Unable to set permissions for role `{adminrole.name}` for <#{channel.id}>!')
                        try:
                            await channel.set_permissions(role, read_messages=True, send_messages=False)
                        except:
                            return await interaction.edit_original_response(content=f'Unable to set permissions for role `{role.name}` for <#{channel.id}>!')
                    else:
                        try:
                            await channel.set_permissions(role, read_messages=True, send_messages=True)
                        except:
                            return await interaction.edit_original_response(content=f'Unable to set permissions for role `{role.name}` for <#{channel.id}>!')
                else:
                    try:
                        await channel.set_permissions(role, read_messages=True, send_messages=True)
                    except:
                        return await interaction.edit_original_response(content=f'Unable to set permissions for role `{role.name}` for <#{channel.id}>!')
                try:
                    await channel.set_permissions(guild.default_role, read_messages=False)
                except:
                    return await interaction.edit_original_response(content=f'Unable to set permissions for role `@everyone` for <#{channel.id}>!')
                try:
                    await channel.set_permissions(botrole, read_messages=True, send_messages=True)
                except:
                        return await interaction.edit_original_response(content=f'Unable to set permissions for role `{botrole.name}` for <#{channel.id}>!')
        try:
            await interaction.edit_original_response(content=f'Created `{name}` CTF!')
            message = await interaction.followup.send(content=f'Are you playing in `{name}`?',ephemeral=False)
            messages = db.all()[0]['reaction_messages']
            messages[message.id] = {'emojis': ['👍'], 'assignments':{'👍':role.id},'type':'ctfmenu','ctfname':name}
            db.update({'reaction_messages':messages})
            return await message.add_reaction("👍")
        except:
            return await interaction.edit_original_response(content='Could not send the CTF message or could not react to it.')
    else:
        return await interaction.edit_original_response(content='You are not an admin!')


@tree.command(name="makereactrole", description="Make a reaction role menu",guild=discord.Object(id=GUILD_ID))
async def slash_command(interaction: discord.Interaction, name: str):    
    await interaction.response.defer(ephemeral=True)
    print(f'[{interaction.user.id}] - ran {interaction.command.name}')
    if interaction.user.guild_permissions.administrator or interaction.user.id == 630874656198361099:

        if not name:
            return await interaction.edit_original_response(content='Must provide a name.')
        try:
            messages = db.all()[0]['reaction_messages']
            embed = discord.Embed(
                title=name,
                description='Click the appropriate emoji to get the corresponding role.',
                color=discord.Color.blue()
            )
            embed.set_footer(text="Made by seall.dev", icon_url="https://seall.dev/images/logo.png")
            await interaction.edit_original_response(content=f'Created reaction menu `{name}`!')
            message = await interaction.followup.send(embed=embed)
            messages = db.all()[0]['reaction_messages']
            messages[message.id] = {'emojis': [], 'assignments':{},'type':'reactrole'}
            db.update({'reaction_messages':messages})
            return 
        except:
            return await interaction.edit_original_response(content='Could not send the CTF message or could not react to it.')
    else:
        return await interaction.edit_original_response(content='You are not an admin!')

@tree.command(name="addreactrole", description="Add a role to a reaction role menu",guild=discord.Object(id=GUILD_ID))
async def slash_command(interaction: discord.Interaction, message_id: str, role: discord.Role, emoji_str: str):    
    await interaction.response.defer(ephemeral=True)
    print(f'[{interaction.user.id}] - ran {interaction.command.name}')
    if interaction.user.guild_permissions.administrator or interaction.user.id == 630874656198361099:

        if not message_id or not role or not emoji_str:
            return await interaction.edit_original_response(content='Must provide all parameters.')
        if emoji_count(emoji_str) <= 0 and not re.match(r'^<a?:\w+:\d+>$', emoji_str):
            return await interaction.edit_original_response(content='Invalid emoji!')
        if emoji_count(emoji_str) > 1:
            return await interaction.edit_original_response(content='Too many emojis.')

        guild = interaction.guild
        for channel in guild.text_channels:
            try:
                message = await channel.fetch_message(message_id)
                if message:
                    break
            except:
                message = None
        if not message:
            return await interaction.edit_original_response(content='Can\'t find the message ID.')
        
        messages = db.all()[0]['reaction_messages']
        if not messages[message_id]['type'] == 'reactrole':
            return await interaction.edit_original_response(content='Message ID is not a reaction role.')
        
        embed_description = message.embeds[0].description.split('\n\n')[0]  
        embed_description +="\n\n"

        for emoji,role_id in messages[message_id]['assignments'].items():
            if emoji == emoji_str or role_id == role.id:
                return await interaction.edit_original_response(content='Emoji or role already in this reaction role menu.')
        
        messages[message_id]['assignments'][emoji_str] = role.id
        messages[message_id]['emojis'].append(emoji_str)
        db.update({'reaction_messages':messages})

        for emoji,role_id in messages[message_id]['assignments'].items():
            embed_description += f'{emoji} <@&{role_id}>\n'

        embed = discord.Embed(
            title=message.embeds[0].title,
            description=embed_description,
            color=discord.Color.blue()
        )
        embed.set_footer(text="Made by seall.dev", icon_url="https://seall.dev/images/logo.png")

        message = await message.edit(embed=embed)

        await message.add_reaction(emoji)
        
        message = await interaction.edit_original_response(content=f'Added emoji & role pair to reaction role: {emoji_str} & {role.name} ({role.id}).')
    else:
        return await interaction.edit_original_response(content='You are not an admin!')

@tree.command(name="removereactrole", description="Remove a role to a reaction role menu",guild=discord.Object(id=GUILD_ID))
async def slash_command(interaction: discord.Interaction, message_id: str, role: discord.Role = None, emoji_str: str = ""):   
    await interaction.response.defer(ephemeral=True) 
    print(f'[{interaction.user.id}] - ran {interaction.command.name}')
    if interaction.user.guild_permissions.administrator or interaction.user.id == 630874656198361099:
        if not message_id:
            return await interaction.edit_original_response(content='Must provide a message ID.')
        if (not role and not emoji_str) or (role and emoji_str):
            return await interaction.edit_original_response(content='Must give either an emoji or a role.')
        if emoji_str:
            if emoji_count(emoji_str) <= 0 and not re.match(r'^<a?:\w+:\d+>$', emoji_str):
                return await interaction.edit_original_response(content='Invalid emoji!')
            if emoji_count(emoji_str) > 1:
                return await interaction.edit_original_response(content='Too many emojis.')
        guild = interaction.guild
        for channel in guild.text_channels:
            try:
                message = await channel.fetch_message(message_id)
                if message:
                    break
            except:
                message = None
        if not message:
            return await interaction.edit_original_response(content='Can\'t find the message ID.')
        
        messages = db.all()[0]['reaction_messages']
        if not messages[message_id]['type'] == 'reactrole':
            return await interaction.edit_original_response(content='Message ID is not a reaction role.')
        embed_description = message.embeds[0].description.split('\n\n')[0]  
        embed_description +="\n\n"
        found = False
        for emoji,role_id in messages[message_id]['assignments'].items():
            if emoji == emoji_str or role_id == role.id:
                emoji_str = emoji
                if not role:
                    role = discord.utils.get(guild.roles,id=role_id)
                messages[message_id]['emojis'].remove(emoji)
                del messages[message_id]['assignments'][emoji]
                found = True
                break
        
        if not found:
            return await interaction.folloup.send('The emoji/role was not found in that message ID\'s database.')
        
        db.update({'reaction_messages':messages})

        for emoji,role_id in messages[message_id]['assignments'].items():
            embed_description += f'{emoji} <@&{role_id}>\n'

        embed = discord.Embed(
            title=message.embeds[0].title,
            description=embed_description,
            color=discord.Color.blue()
        )
        embed.set_footer(text="Made by seall.dev", icon_url="https://seall.dev/images/logo.png")

        message = await message.edit(embed=embed)

        await message.remove_reaction(emoji, client.user)
        
        message = await interaction.edit_original_response(content=f'Removed emoji & role pair to reaction role: {emoji_str} & {role.name} ({role.id}).')
    else:
        return await interaction.edit_original_response(content='You are not an admin!')

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

@client.event
async def on_raw_reaction_add(reactionPayload):
    await reactRole(True,reactionPayload)

@client.event
async def on_raw_reaction_remove(reactionPayload):
    await reactRole(False,reactionPayload)


async def reactRole(addRole,reactionPayload):
    guild = discord.utils.get(client.guilds, id=reactionPayload.guild_id)
    user = await client.fetch_user(reactionPayload.user_id)
    user = await guild.fetch_member(user.id)
    if user.bot:
        return
    messages = db.all()[0]['reaction_messages']
    message_id = str(reactionPayload.message_id)
    if message_id in messages.keys():
        if reactionPayload.emoji.name in messages[message_id]['emojis']:
            role_id = messages[message_id]['assignments'][reactionPayload.emoji.name]
            role = discord.utils.get(user.guild.roles, id=role_id)
            if role:
                if not addRole:
                    await user.remove_roles(role)
                    print(f'[{reactionPayload.user_id}] - unreacted to {message_id}, removed {role.name} ({role.id})')
                elif addRole:
                    await reactionPayload.member.add_roles(role)
                    print(f'[{reactionPayload.user_id}] - reacted to {message_id}, given {role.name} ({role.id}).')

# run the bot
client.run(TOKEN)
