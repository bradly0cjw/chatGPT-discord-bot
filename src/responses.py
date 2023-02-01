from revChatGPT.Official import Chatbot
import json
from asgiref.sync import sync_to_async
import requests


def get_config() -> dict:
    import os
    # get config.json path
    config_dir = os.path.abspath(__file__ + "/../../")
    config_name = 'config.json'
    config_path = os.path.join(config_dir, config_name)

    with open(config_path, 'r') as f:
        config = json.load(f)

    return config


config = get_config()
chatbot = Chatbot(api_key=config['openAI_key'])

def write(token,model):
    import os
    # get config.json path
    config_dir = os.path.abspath(__file__ + "/../../")
    config_name = 'usage.txt'
    config_name2 = 'curusage.txt'
    config_name3 = 'model.txt'
    config_path = os.path.join(config_dir, config_name)
    config_path2 = os.path.join(config_dir, config_name2)
    config_path3 = os.path.join(config_dir, config_name3)
    with open(config_path2, "w") as file:
        # Write some text to the file
        file.write(str(token))
    with open(config_path, 'r') as file:
        use=file.read()
    with open(config_path3, "w") as file:
        # Write some text to the file
        file.write(str(model))
    if model!="text-chat-davinci-002-20230126":  
        use=int(use)+int(token)
    # print(use)
    with open(config_path, "w") as file:
        # Write some text to the file
        file.write(str(use))

async def handle_response(message) -> str:
    response = await sync_to_async(chatbot.ask)(message)
    responseMessage = response["choices"][0]["text"]
    nowusage=response["usage"]["total_tokens"]
    model=response["model"]
    write(str(nowusage),str(model))
    return responseMessage
