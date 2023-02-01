import discord
from discord import app_commands
from src import responses
from src import log
from datetime import datetime
import json

logger = log.setup_logger(__name__)

config = responses.get_config()

isPrivate = False


class aclient(discord.Client):
    def __init__(self) -> None:
        super().__init__(intents=discord.Intents.default())
        self.tree = app_commands.CommandTree(self)
        self.activity = discord.Activity(type=discord.ActivityType.watching, name="/chat | /help")


async def send_message(message, user_message):
    await message.response.defer(ephemeral=isPrivate)
    try:
        response = '> **' + user_message + '** - <@' + \
            str(message.user.id) + '> \n\n'
        response = f"{response}{await responses.handle_response(user_message)}"
        if len(response) > 1900:
            # Split the response into smaller chunks of no more than 1900 characters each(Discord limit is 2000 per chunk)
            if "```" in response:
                # Split the response if the code block exists
                parts = response.split("```")
                # Send the first message
                await message.followup.send(parts[0])
                # Send the code block in a seperate message
                code_block = parts[1].split("\n")
                formatted_code_block = ""
                for line in code_block:
                    while len(line) > 1900:
                        # Split the line at the 50th character
                        formatted_code_block += line[:1900] + "\n"
                        line = line[1900:]
                    formatted_code_block += line + "\n"  # Add the line and seperate with new line

                # Send the code block in a separate message
                if (len(formatted_code_block) > 2000):
                    code_block_chunks = [formatted_code_block[i:i+1900]
                                         for i in range(0, len(formatted_code_block), 1900)]
                    for chunk in code_block_chunks:
                        await message.followup.send("```" + chunk + "```")
                else:
                    await message.followup.send("```" + formatted_code_block + "```")

                # Send the remaining of the response in another message

                if len(parts) >= 3:
                    await message.followup.send(parts[2])
            else:
                response_chunks = [response[i:i+1900]
                                   for i in range(0, len(response), 1900)]
                for chunk in response_chunks:
                    await message.followup.send(chunk)
        else:
            await message.followup.send(response)
    except Exception as e:
        await message.followup.send("> **Error: Something went wrong, please try again later!**")
        logger.exception(f"Error while sending message: {e}")

def write_to_file(key, value,file_name):
    try:
        data=read_from_file(file_name)
    except json.decoder.JSONDecodeError:
        data = {}
    data[key] = value
    with open(file_name, "w") as file:
        json.dump(data, file, indent=4)

def read_from_file(file_name):
    with open(file_name, 'r') as f:
        data=json.load(f)
        return data
        
def logging(client,interaction):
    return str(interaction.user),str(interaction.guild),str(interaction.channel),client.get_channel(int(config['discord_log'])),datetime.now().strftime("%Y-%m-%d %H:%M:%S")

async def startup(client):
    responseMessage = "Online!"
    #Get the current time
    now = datetime.now()
    cur=now.isoformat()
    write_to_file('time',cur, 'data.json')
    # Format the current time as a string
    time_string = now.strftime("%Y-%m-%d %H:%M:%S")
    channel = client.get_channel(int(config['discord_log']))
    # await channel.send('Online!')
    await channel.send("> `%s`\n> %s Connected to `%s` servers\n> **Ping:**`%s`\n"%(time_string,responseMessage,len(client.guilds),str(round(client.latency * 1000, 2))))
    # print(client.guilds)


async def send_start_prompt(client):
    import os
    import os.path

    config_dir = os.path.abspath(__file__ + "/../../")
    prompt_name = 'starting-prompt.txt'
    prompt_path = os.path.join(config_dir, prompt_name)
    try:
        if os.path.isfile(prompt_path) and os.path.getsize(prompt_path) > 0:
            with open(prompt_path, "r") as f:
                prompt = f.read()
                if (config['discord_channel_id']):
                    logger.info(f"Send starting prompt with size {len(prompt)}")
                    responseMessage = await responses.handle_response(prompt)
                    channel = client.get_channel(int(config['discord_channel_id']))
                    await channel.send(responseMessage)
                    logger.info(f"Starting prompt response:{responseMessage}")
                else:
                    logger.info("No Channel selected. Skip sending starting prompt.")
        else:
            logger.info(f"No {prompt_name}. Skip sending starting prompt.")
    except Exception as e:
        logger.exception(f"Error while sending starting prompt: {e}")


def run_discord_bot():
    client = aclient()

    @client.event
    async def on_ready():
        await startup(client)
        await send_start_prompt(client)
        await client.tree.sync()
        logger.info(f'{client.user} is now running!')

    @client.tree.command(name="chat", description="Have a chat with ChatGPT (With OpenAi Preset prompt)")
    async def chat(interaction: discord.Interaction, *, message: str):
        if interaction.user == client.user:
            return
        username = str(interaction.user)
        user_message = message
        channel = str(interaction.channel)
        await send_message(interaction, user_message)
        data=read_from_file('data.json')
        cur=int(data['curuse'])
        model=str(data['model'])
        if model!="text-chat-davinci-002-20230126":    
            await interaction.followup.send("You use `%d` Tokens this time"%cur)
        else:
            # await interaction.followup.send("You use `%d` Tokens this time\nBut currently `%s` model is free to use"%(cur,model))
            pass
        logger.info(
            f"\x1b[31m{username}\x1b[0m : '{user_message}' with {model} {cur} ({channel})")
        username,guild,sendchannel,channel,time_string=logging(client,interaction)
        await channel.send("> `%s`\n> %s\n> **Text:**`%s`\n> **Model:**`%s` **Token:**`%d`\n> @`%s#%s`\n"%(time_string,username,user_message,model,cur,guild,sendchannel))

    
    @client.tree.command(name="reset", description="Complete reset ChatGPT conversation history")
    async def reset(interaction: discord.Interaction):
        responses.chatbot.reset()
        await interaction.response.defer(ephemeral=False)
        await interaction.followup.send("> **Info: I have forgotten everything.**")
        logger.warning(
            "\x1b[31mChatGPT bot has been successfully reset\x1b[0m")
        username,guild,sendchannel,channel,time_string=logging(client,interaction)
        await channel.send("> `%s`\n> %s **Reset**\n> @`%s#%s`\n"%(time_string,username,guild,sendchannel))
        await send_start_prompt(client)
    
    @client.tree.command(name="dbug", description="debug only (need permission)")
    async def chat(interaction: discord.Interaction, *, message: str):
        if int(interaction.user.id) == int(config['discord_admin']):
            return
        else:
            return

    @client.tree.command(name="usage", description="Check current API usage")
    async def cur_usege(interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=False)
        try:
            data=read_from_file('data.json')
            use=int(data['usage'])
        except:
            use=0
            write_to_file('usage',use,'data.json')
        usepercent=use/900000*100
        usecredit=use/1000*0.02
        await interaction.followup.send("**Used Tokens:** `%d/900000` (%.2f%%)\n**Used Credit:** `$%.2f/$18.00` (USD)"%(use,usepercent,usecredit))    
        username,guild,sendchannel,channel,time_string=logging(client,interaction)
        await channel.send("> `%s`\n> %s Usage\n> @`%s#%s`\n> **Used Tokens:** `%d/900000` (%.2f%%)\n> **Used Credit:** `$%.2f/$18.00` (USD)\n"%(time_string,username,guild,sendchannel,use,usepercent,usecredit))

    @client.tree.command(name="private", description="Toggle private access (Need Permission)")
    async def private(interaction: discord.Interaction):
        global isPrivate
        if int(interaction.user.id) == int(config['discord_admin']):
            await interaction.response.defer(ephemeral=False)
            if not isPrivate:
                isPrivate = not isPrivate
                logger.warning("\x1b[31mSwitch to private mode\x1b[0m")
                logger.warning(interaction.user.id)
                await interaction.followup.send("> **Info: Next, the response will be sent via private message. If you want to switch back to public mode, use `/public`**")
            else:
                logger.info("You already on private mode!")
                await interaction.followup.send("> **Warn: You already on private mode. If you want to switch to public mode, use `/public`**")
        else:
            await interaction.response.defer(ephemeral=False)
            username = str(interaction.user)
            channel = str(interaction.channel)
            logger.warning(
            f"\x1b[31m{username}\x1b[0m : '{interaction.user.id}' ({channel}) Private")
            await interaction.followup.send("> **Warn: You don't have Permission ! **")
        username,guild,sendchannel,channel,time_string=logging(client,interaction)
        await channel.send("> `%s`\n> %s Private\n> @`%s#%s`\n"%(time_string,username,guild,sendchannel))

    @client.tree.command(name="public", description="Toggle public access (Need Permission)")
    async def public(interaction: discord.Interaction):
        global isPrivate
        if int(interaction.user.id) == int(config['discord_admin']):
            await interaction.response.defer(ephemeral=False)
            if isPrivate:
                isPrivate = not isPrivate
                await interaction.followup.send("> **Info: Next, the response will be sent to the channel directly. If you want to switch back to private mode, use `/private`**")
                logger.warning("\x1b[31mSwitch to public mode\x1b[0m")
                logger.warning(interaction.user.id)
            else:
                await interaction.followup.send("> **Warn: You already on public mode. If you want to switch to private mode, use `/private`**")
                logger.info("You already on public mode!")
        else:
            await interaction.response.defer(ephemeral=False)
            username = str(interaction.user)
            channel = str(interaction.channel)
            logger.warning(
            f"\x1b[31m{username}\x1b[0m : '{interaction.user.id}' ({channel}) Private")
            await interaction.followup.send("> **Warn: You don't have Permission ! **")
        username,guild,sendchannel,channel,time_string=logging(client,interaction)
        await channel.send("> `%s`\n> %s Public\n> @`%s#%s`\n"%(time_string,username,guild,sendchannel))

    @client.tree.command(name="sta",description="Show bot staus")
    async def sta(interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=False)
        pre=read_from_file('data.json')
        pre=datetime.fromisoformat(pre["time"])
        pingvalue=str(round(client.latency * 1000, 2))
        username,guild,sendchannel,channel,time_string=logging(client,interaction)
        now = datetime.now()
        diff=now-pre
        days = diff.days/1
        hours = (diff.seconds/60/60)%24
        min = (diff.seconds/60)%60
        sec = diff.seconds%60
        time_str=("`%d D %02d:%02d:%02d`"%(days,hours,min,sec))
        await interaction.followup.send("> **Pong!~** `%s` **ms**\n> **Uptime:** %s"%(pingvalue,time_str))
        await channel.send("> `%s`\n> %s \n> **Ping:**`%s`\n> **Uptime:** %s\n> @`%s#%s`\n"%(time_string,username,pingvalue,time_str,guild,sendchannel))

    @client.tree.command(name="help", description="Show help for the bot")
    async def help(interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=False)
        await interaction.followup.send("This Bot is hosted by Bradly<@494796055439867905> \n    :star:**BASIC COMMANDS** \n    `/chat [message]` Chat with ChatGPT!\n    For complete documentation, please visit https://github.com/bradly0cjw/chatGPT-discord-bot \n    Special Thanks: Zero6992")
        logger.info(
            "\x1b[31mSomeone need help!\x1b[0m")
        username,guild,sendchannel,channel,time_string=logging(client,interaction)
        await channel.send("> `%s`\n> %s Help\n> @`%s#%s`\n"%(time_string,username,guild,sendchannel))

    TOKEN = config['discord_bot_token']
    client.run(TOKEN)
