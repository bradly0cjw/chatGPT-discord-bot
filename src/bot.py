import discord
import os
import openai
from random import randrange
from discord import app_commands
from src import responses
from src import log
from src import art
from src import personas

from datetime import datetime
import json

logger = log.setup_logger(__name__)

isPrivate = False

class aclient(discord.Client):
    def __init__(self) -> None:
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)
        self.activity = discord.Activity(type=discord.ActivityType.listening, name="/chat | /help")

async def send_message(message, user_message,userid,client):
    isReplyAll =  os.getenv("REPLYING_ALL")
    if isReplyAll == "False":
        author = message.user.id
        await message.response.defer(ephemeral=isPrivate)
    else:
        author = message.author.id
    try:
        response = (f'> **{user_message}** - <@{str(author)}' + '> \n\n')
        chat_model = os.getenv("CHAT_MODEL")
        if chat_model == "OFFICIAL":
            response = f"{response}{await responses.official_handle_response(user_message)}"
        elif chat_model == "UNOFFICIAL":
            response = f"{response}{await responses.unofficial_handle_response(user_message)}"
        char_limit = 1900
        if len(response) > char_limit:
            # Split the response into smaller chunks of no more than 1900 characters each(Discord limit is 2000 per chunk)
            if "```" in response:
                # Split the response if the code block exists
                parts = response.split("```")

                for i in range(len(parts)):
                    if i%2 == 0: # indices that are even are not code blocks
                        if isReplyAll == "True":
                            await message.channel.send(parts[i])
                        else:
                            await message.followup.send(parts[i])

                    else: # Odd-numbered parts are code blocks
                        code_block = parts[i].split("\n")
                        formatted_code_block = ""
                        for line in code_block:
                            while len(line) > char_limit:
                                # Split the line at the 50th character
                                formatted_code_block += line[:char_limit] + "\n"
                                line = line[char_limit:]
                            formatted_code_block += line + "\n"  # Add the line and seperate with new line

                        # Send the code block in a separate message
                        if (len(formatted_code_block) > char_limit+100):
                            code_block_chunks = [formatted_code_block[i:i+char_limit]
                                                 for i in range(0, len(formatted_code_block), char_limit)]
                            for chunk in code_block_chunks:
                                if isReplyAll == "True":
                                    await message.channel.send(f"```{chunk}```")
                                else:
                                    await message.followup.send(f"```{chunk}```")
                        elif isReplyAll == "True":
                            await message.channel.send(f"```{formatted_code_block}```")
                        else:
                            await message.followup.send(f"```{formatted_code_block}```")

            else:
                response_chunks = [response[i:i+char_limit]
                                   for i in range(0, len(response), char_limit)]
                for chunk in response_chunks:
                    if isReplyAll == "True":
                        await message.channel.send(chunk)
                    else:
                        await message.followup.send(chunk)
        elif isReplyAll == "True":
            await message.channel.send(response)
        else:
            await message.followup.send(response)
    except Exception as e:
        if isReplyAll:
            await message.channel.send("> **Error: Something went wrong, please try again later!**\n> **Exception:%s**"%e)
        else:
            await message.followup.send("> **Error: Something went wrong, please try again later!**\n> **Exception:%s**"%e)
        await client.get_channel(int(os.getenv("DISCORD_LOG"))).send("> **Error: Something went wrong, please try again later!**\n> **Exception:%s**"%e)
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
    return str(interaction.user),str(interaction.guild),str(interaction.channel),client.get_channel(int(os.getenv("DISCORD_LOG"))),datetime.now().strftime("%Y-%m-%d %H:%M:%S")

async def startup(client):
    responseMessage = "Online!"
    #Get the current time
    now = datetime.now()
    cur=now.isoformat()
    write_to_file('time',cur, 'data.json')
    # Format the current time as a string
    time_string = now.strftime("%Y-%m-%d %H:%M:%S")
    channel = client.get_channel(int(os.getenv("DISCORD_LOG")))
    # await channel.send('Online!')
    await channel.send("> `%s`\n> %s Connected to `%s` servers\n> **Ping:**`%s`\n"%(time_string,responseMessage,len(client.guilds),str(round(client.latency * 1000, 2))))
    # print(client.guilds)


async def send_start_prompt(client):
    import os.path

    config_dir = os.path.abspath(f"{__file__}/../../")
    prompt_name = 'starting-prompt.txt'
    prompt_path = os.path.join(config_dir, prompt_name)
    discord_channel_id = os.getenv("DISCORD_CHANNEL_ID")
    try:
        if os.path.isfile(prompt_path) and os.path.getsize(prompt_path) > 0:
            with open(prompt_path, "r", encoding="utf-8") as f:
                prompt = f.read()
                if (discord_channel_id):
                    logger.info(f"Send starting prompt with size {len(prompt)}")
                    chat_model = os.getenv("CHAT_MODEL")
                    response = ""
                    if chat_model == "OFFICIAL":
                        response = f"{response}{await responses.official_handle_response(prompt)}"
                    elif chat_model == "UNOFFICIAL":
                        response = f"{response}{await responses.unofficial_handle_response(prompt)}"
                    channel = client.get_channel(int(discord_channel_id))
                    await channel.send(response)
                    logger.info(f"Starting prompt response:{response}")
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


    @client.tree.command(name="chat", description="Have a chat with ChatGPT")
    async def chat(interaction: discord.Interaction, *, message: str):
        isReplyAll =  os.getenv("REPLYING_ALL")
        if isReplyAll == "True":
            await interaction.response.defer(ephemeral=False)
            await interaction.followup.send(
                "> **Warn: You already on replyAll mode. If you want to use slash command, switch to normal mode, use `/replyall` again**")
            logger.warning("\x1b[31mYou already on replyAll mode, can't use slash command!\x1b[0m")
            return
        if interaction.user == client.user:
            return
        username = str(interaction.user)
        channel = str(interaction.channel)
        # responses.chatbot.reset()
        # try:
        #     # responses.chatbot.prompt.chat_history=[]
        #     responses.chatbot.load_conversation(str(interaction.user.id))
        #     a=responses.chatbot.conversations[str(interaction.user.id)].chat_history
        #     b=responses.chatbot.conversations["849950082714435624"].chat_history
        #     c=responses.chatbot.conversations["494796055439867905"].chat_history
        #     print("get %s ,%s"%(interaction.user.id,a))
        #     print("get %s ,%s"%("Yee",c))
        #     print("get %s ,%s"%("lin",b))
                # except:
        #     # responses.chatbot.prompt.chat_history=[]
        #     print("err")
        #     pass
        
        # print("current: %s"%responses.chatbot.prompt.chat_history)

        await send_message(interaction, user_message,interaction.user.id,client)
        # await interaction.response.defer(ephemeral=True)
        # await interaction.followup.send("現在Chat Gpt 的Api被肏爛了\n請等待修復")

        # responses.chatbot.save_conversation(str(interaction.user.id))
        # a=responses.chatbot.prompt.chat_history
        # try:
        #     print(a)
        #     b=responses.chatbot.conversations["849950082714435624"].chat_history
        #     c=responses.chatbot.conversations["494796055439867905"].chat_history
        #     print("get %s ,%s"%("Yee",c))
        #     print("get %s ,%s"%("lin",b))
        # except:
        #     print("error")
        # responses.chatbot.dump_conversation_history()

        ## logginfg for usage (Current usage unavailble)

        # data=read_from_file('data.json')
        # cur=int(data['curuse'])
        # model=str(data['model'])
        # if model=="text-davinci-003":    
        #     await interaction.followup.send("You use `%d` Tokens this time"%cur)
        # else:
        #     # await interaction.followup.send("You use `%d` Tokens this time\nBut currently `%s` model is free to use"%(cur,model))
        #     pass
        model=os.getenv("CHAT_MODEL")
        cur="N/A"
        logger.info(
            f"\x1b[31m{username}\x1b[0m : '{user_message}' with {model} {cur} ({channel})")
        username,guild,sendchannel,channel,time_string=logging(client,interaction)
        await channel.send(
            "> `%s`\n> %s\n> **Text:**`%s`\n> **Model:**`%s` **Token:**`%s`\n> @`%s#%s`\n"%(time_string,username,user_message,model,cur,guild,sendchannel))


    @client.tree.command(name="private", description="Toggle private access (Need Permission)")
    async def private(interaction: discord.Interaction):
        global isPrivate
        if int(interaction.user.id) == int(os.getenv("DISCORD_ADMIN")):
            await interaction.response.defer(ephemeral=False)
            if not isPrivate:
                isPrivate = not isPrivate
                logger.warning("\x1b[31mSwitch to private mode\x1b[0m")
                logger.warning(interaction.user.id)
                await interaction.followup.send(
                    "> **Info: Next, the response will be sent via private message. If you want to switch back to public mode, use `/public`**")
            else:
                logger.info("You already on private mode!")
                await interaction.followup.send(
                    "> **Warn: You already on private mode. If you want to switch to public mode, use `/public`**")
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
        if int(interaction.user.id) == int(os.getenv("DISCORD_ADMIN")):
            await interaction.response.defer(ephemeral=False)
            if isPrivate:
                isPrivate = not isPrivate
                await interaction.followup.send(
                    "> **Info: Next, the response will be sent to the channel directly. If you want to switch back to private mode, use `/private`**")
                logger.warning("\x1b[31mSwitch to public mode\x1b[0m")
                logger.warning(interaction.user.id)
            else:
                await interaction.followup.send(
                    "> **Warn: You already on public mode. If you want to switch to private mode, use `/private`**")
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



    @client.tree.command(name="replyall", description="Toggle replyAll access")
    async def replyall(interaction: discord.Interaction):
        if int(interaction.user.id) == int(os.getenv("DISCORD_ADMIN")):
            isReplyAll =  os.getenv("REPLYING_ALL")
            os.environ["REPLYING_ALL_DISCORD_CHANNEL_ID"] = str(interaction.channel_id)
            await interaction.response.defer(ephemeral=False)
            if isReplyAll == "True":
                os.environ["REPLYING_ALL"] = "False"
                await interaction.followup.send(
                    "> **Info: The bot will only response to the slash command `/chat` next. If you want to switch back to replyAll mode, use `/replyAll` again.**")
                logger.warning("\x1b[31mSwitch to normal mode\x1b[0m")
            elif isReplyAll == "False":
                os.environ["REPLYING_ALL"] = "True"
                await interaction.followup.send(
                    "> **Info: Next, the bot will response to all message in this channel only.If you want to switch back to normal mode, use `/replyAll` again.**")
                logger.warning("\x1b[31mSwitch to replyAll mode\x1b[0m")
        else:
            await interaction.response.defer(ephemeral=False)
            username = str(interaction.user)
            channel = str(interaction.channel)
            logger.warning(
            f"\x1b[31m{username}\x1b[0m : '{interaction.user.id}' ({channel}) Reply All")
            await interaction.followup.send("> **Warn: You don't have Permission ! **")
        username,guild,sendchannel,channel,time_string=logging(client,interaction)
        await channel.send("> `%s`\n> %s Reply All\n> @`%s#%s`\n"%(time_string,username,guild,sendchannel))

    
    # @client.tree.command(name="reset", description="Complete reset ChatGPT conversation history")
    # async def reset(interaction: discord.Interaction):
    #     responses.chatbot.reset_chat()

           
    @client.tree.command(name="chat-model", description="Switch different chat model")
    @app_commands.choices(choices=[
        app_commands.Choice(name="Official GPT-3.5", value="OFFICIAL"),
        app_commands.Choice(name="Website ChatGPT", value="UNOFFICIAL")
    ])
    async def chat_model(interaction: discord.Interaction, choices: app_commands.Choice[str]):
        await interaction.response.defer(ephemeral=False)
        if choices.value == "OFFICIAL":
            responses.chatbot = responses.get_chatbot_model("OFFICIAL")
            os.environ["CHAT_MODEL"] = "OFFICIAL"
            await interaction.followup.send(
                "> **Info: You are now in Official GPT-3.5 model.**\n> You need to set your `OPENAI_API_KEY` in `env` file.")
            logger.warning("\x1b[31mSwitch to OFFICIAL chat model\x1b[0m")
        elif choices.value == "UNOFFICIAL":
            responses.chatbot = responses.get_chatbot_model("UNOFFICIAL")
            os.environ["CHAT_MODEL"] = "UNOFFICIAL"
            await interaction.followup.send(
                "> **Info: You are now in Website ChatGPT model.**\n> You need to set your `SESSION_TOKEN` or `OPENAI_EMAIL` and `OPENAI_PASSWORD` in `env` file.")
            logger.warning("\x1b[31mSwitch to UNOFFICIAL(Website) chat model\x1b[0m")    


    @client.tree.command(name="reset", description="Complete reset ChatGPT conversation history")
    async def reset(interaction: discord.Interaction):
        chat_model = os.getenv("CHAT_MODEL")
        if chat_model == "OFFICIAL":
            responses.chatbot.reset()
        elif chat_model == "UNOFFICIAL":
            responses.chatbot.reset_chat()
            # responses.unofficial_chatbot.reset_chat()
        # responses.chatbot.reset()
        # responses.chatbot.save_conversation(conversation_id=interaction.user.id)
        await interaction.response.defer(ephemeral=False)
        await interaction.followup.send("> **Info: I have forgotten everything.**")
        personas.current_persona = "standard"
        logger.warning(
            "\x1b[31mChatGPT bot has been successfully reset\x1b[0m")
        username,guild,sendchannel,channel,time_string=logging(client,interaction)
        await channel.send("> `%s`\n> %s **Reset**\n> @`%s#%s`\n"%(time_string,username,guild,sendchannel))
        await send_start_prompt(client)
    
    @client.tree.command(name="dbug", description="debug only (need permission)")
    async def chat(interaction: discord.Interaction,*,fun:str,id:str):
        if int(interaction.user.id) == int(os.getenv("DISCORD_ADMIN")):
            # responses.chatbot.save_conversation(str(interaction.user.id))
            # print(responses.chatbot.get_conversations())
            # responses.chatbot.dump_conversation_history()
            await interaction.response.defer(ephemeral=True)
            # a=responses.chatbot.prompt.chat_history
            # try:
            #     print(a)
            # except:
            #     print("error")
            #     pass
            if fun=="l":
                responses.chatbot.load_conversation(str(id))
                print("l")
            elif fun=="s":
                responses.chatbot.save_conversation(str(id))
                print("s")
            elif fun=="sf":
                responses.chatbot.conversations.save(str(id))
                print("sf")
            elif fun=="lf":
                responses.chatbot.conversations.load(str(id))
                print("lf")
            elif fun=="hi":
                pass
            else:
                return
            await interaction.followup.send("Finish")
            print("current: %s"%responses.chatbot.prompt.chat_history)
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
        await interaction.followup.send(""":star:**BASIC COMMANDS** \n
        - `/chat [message]` Chat with ChatGPT!
        - `/draw [prompt]` Generate an image with the Dalle2 model
        - `/switchpersona [persona]` Switch between optional chatGPT jailbreaks
                `random`: Picks a random persona
                `chatgpt`: Standard chatGPT mode
                `dan`: Dan Mode 11.0, infamous Do Anything Now Mode
                `sda`: Superior DAN has even more freedom in DAN Mode
                `confidant`: Evil Confidant, evil trusted confidant
                `based`: BasedGPT v2, sexy gpt
                `oppo`: OPPO says exact opposite of what chatGPT would say
                `dev`: Developer Mode, v2 Developer mode enabled

        - `/private` ChatGPT switch to private mode
        - `/public` ChatGPT switch to public mode
        - `/replyall` ChatGPT switch between replyAll mode and default mode
        - `/reset` Clear ChatGPT conversation history
        - `/chat-model` Switch different chat model
                `OFFICIAL`: GPT-3.5 model
                `UNOFFICIAL`: Website ChatGPT
                Modifying CHAT_MODEL field in the .env file change the default model

        For complete documentation, please visit https://github.com/Zero6992/chatGPT-discord-bot""")

        logger.info(
            "\x1b[31mSomeone needs help!\x1b[0m")

    @client.tree.command(name="draw", description="Generate an image with the Dalle2 model")
    async def draw(interaction: discord.Interaction, *, prompt: str):
        isReplyAll =  os.getenv("REPLYING_ALL")
        if isReplyAll == "True":
            await interaction.response.defer(ephemeral=False)
            await interaction.followup.send(
                "> **Warn: You already on replyAll mode. If you want to use slash command, switch to normal mode, use `/replyall` again**")
            logger.warning("\x1b[31mYou already on replyAll mode, can't use slash command!\x1b[0m")
            return
        if interaction.user == client.user:
            return

        #await interaction.response.defer(ephemeral=False)
        username = str(interaction.user)
        channel = str(interaction.channel)
        logger.info(
            f"\x1b[31m{username}\x1b[0m : /draw [{prompt}] in ({channel})")


        await interaction.response.defer(thinking=True)
        try:
            path = await art.draw(prompt)

            file = discord.File(path, filename="image.png")
            title = '> **' + prompt + '**\n'
            embed = discord.Embed(title=title)
            embed.set_image(url="attachment://image.png")

            # send image in an embed
            await interaction.followup.send(file=file, embed=embed)

        except openai.InvalidRequestError:
            await interaction.followup.send(
                "> **Warn: Inappropriate request 😿**")
            logger.info(
            f"\x1b[31m{username}\x1b[0m made an inappropriate request.!")

        except Exception as e:
            await interaction.followup.send(
                "> **Warn: Something went wrong 😿**")
            logger.exception(f"Error while generating image: {e}")


    @client.tree.command(name="switchpersona", description="Switch between optional chatGPT jailbreaks")
    @app_commands.choices(persona=[
        app_commands.Choice(name="Random", value="random"),
        app_commands.Choice(name="Standard", value="standard"),
        app_commands.Choice(name="Do Anything Now 11.0", value="dan"),
        app_commands.Choice(name="Superior Do Anything", value="sda"),
        app_commands.Choice(name="Evil Confidant", value="confidant"),
        app_commands.Choice(name="BasedGPT v2", value="based"),
        app_commands.Choice(name="OPPO", value="oppo"),
        app_commands.Choice(name="Developer Mode v2", value="dev")
    ])
    async def chat(interaction: discord.Interaction, persona: app_commands.Choice[str]):
        isReplyAll =  os.getenv("REPLYING_ALL")
        if isReplyAll == "True":
            await interaction.response.defer(ephemeral=False)
            await interaction.followup.send(
                "> **Warn: You already on replyAll mode. If you want to use slash command, switch to normal mode, use `/replyall` again**")
            logger.warning("\x1b[31mYou already on replyAll mode, can't use slash command!\x1b[0m")
            return
        if interaction.user == client.user:
            return

        await interaction.response.defer(thinking=True)
        username = str(interaction.user)
        channel = str(interaction.channel)
        logger.info(
            f"\x1b[31m{username}\x1b[0m : '/switchpersona [{persona.value}]' ({channel})")

        persona = persona.value

        if persona == personas.current_persona:
            await interaction.followup.send(f"> **Warn: Already set to `{persona}` persona**")

        elif persona == "standard":
            chat_model = os.getenv("CHAT_MODEL")
            if chat_model == "OFFICIAL":
                responses.chatbot.reset()
            elif chat_model == "UNOFFICIAL":
                responses.chatbot.reset_chat()

            personas.current_persona = "standard"
            await interaction.followup.send(
                f"> **Info: Switched to `{persona}` persona**")

        elif persona == "random":
            choices = list(personas.PERSONAS.keys())
            choice = randrange(0, 6)
            chosen_persona = choices[choice]
            personas.current_persona = chosen_persona
            await responses.switch_persona(chosen_persona)
            await interaction.followup.send(
                f"> **Info: Switched to `{chosen_persona}` persona**")


        elif persona in personas.PERSONAS:
            try:
                await responses.switch_persona(persona)
                personas.current_persona = persona
                await interaction.followup.send(
                f"> **Info: Switched to `{persona}` persona**")
            except Exception as e:
                await interaction.followup.send(
                    "> **Error: Something went wrong, please try again later! 😿**")
                logger.exception(f"Error while switching persona: {e}")

        else:
            await interaction.followup.send(
                f"> **Error: No available persona: `{persona}` 😿**")
            logger.info(
                f'{username} requested an unavailable persona: `{persona}`')

    @client.event
    async def on_message(message):
        isReplyAll =  os.getenv("REPLYING_ALL")
        if isReplyAll == "True" and message.channel.id == int(os.getenv("REPLYING_ALL_DISCORD_CHANNEL_ID")):
            if message.author == client.user:
                return
            username = str(message.author)
            user_message = str(message.content)
            channel = str(message.channel)
            logger.info(f"\x1b[31m{username}\x1b[0m : '{user_message}' ({channel})")
            await send_message(message, user_message,"",client)

    TOKEN = os.getenv("DISCORD_BOT_TOKEN")

    client.run(TOKEN)
