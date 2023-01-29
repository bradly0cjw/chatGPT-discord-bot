import discord
from discord import app_commands
from src import responses
from src import log

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
            str(message.user.id) + '>\n\n'
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
                logger.info(f"Send starting prompt with size {len(prompt)}")
                # responseMessage = await responses.handle_response(prompt)
                responseMessage = "Online!"
                if (config['discord_channel_id']):
                    channel = client.get_channel(int(config['discord_channel_id']))
                    # await channel.send('Online!')
                    await channel.send(responseMessage)
            logger.info(f"Starting prompt response:{responseMessage}")
        else:
            logger.info(f"No {prompt_name}. Skip sending starting prompt.")
    except Exception as e:
        logger.exception(f"Error while sending starting prompt: {e}")


def run_discord_bot():
    client = aclient()

    @client.event
    async def on_ready():
        await send_start_prompt(client)
        await client.tree.sync()
        logger.info(f'{client.user} is now running!')

    @client.tree.command(name="chat", description="Have a chat with ChatGPT")
    async def chat(interaction: discord.Interaction, *, message: str):
        if interaction.user == client.user:
            return
        username = str(interaction.user)
        user_message = message
        channel = str(interaction.channel)
        await send_message(interaction, user_message)
        import os
        # get config.json path
        config_dir = os.path.abspath(__file__ + "/../../")
        config_name2 = 'curusage.txt'
        config_path2 = os.path.join(config_dir, config_name2)
        with open(config_path2, "r") as file:
        # Write some text to the file
            cur=file.read()
        cur=int(cur)    
        await interaction.followup.send("You use %d Token this time"%cur)
        logger.info(
            f"\x1b[31m{username}\x1b[0m : '{user_message}' {cur} ({channel})")

    @client.tree.command(name="usege", description="Check current API usege")
    async def cur_usege(interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=False)
        import os
        # get config.json path
        config_dir = os.path.abspath(__file__ + "/../../")
        config_name = 'usage.txt'
        config_path = os.path.join(config_dir, config_name)
        with open(config_path, 'r') as file:
            use=file.read()
        use=int(use)
        usepercent=use/900000
        usecredit=use/1000*0.02
        # print("Current Usage:%d/900000(%.2f%%)\nCurrent Credit:$%.2f/$18.00"%(use,usepercent,usecredit))
        await interaction.followup.send("Current Usage: %d/900000 (%.2f%%)\nCurrent Credit: $%.2f/$18.00 (USD)"%(use,usepercent,usecredit))    

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

    @client.tree.command(name="help", description="Show help for the bot")
    async def help(interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=False)
        await interaction.followup.send("This Bot is hosted by Bradly<@494796055439867905> \n    :star:**BASIC COMMANDS** \n    `/chat [message]` Chat with ChatGPT!\n    For complete documentation, please visit https://github.com/bradly0cjw/chatGPT-discord-bot \n    Special Thanks: Zero6992")
        logger.info(
            "\x1b[31mSomeone need help!\x1b[0m")

    TOKEN = config['discord_bot_token']
    client.run(TOKEN)
