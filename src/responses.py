from revChatGPT.Official import Chatbot,Prompt
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
    from .bot import write_to_file,read_from_file
    # get config.json path
    write_to_file('curuse',int(token),'data.json')
    data=read_from_file('data.json')
    try:
        use=data['usage']
    except:
        use=0
        write_to_file('usage',use,'data.json')
    write_to_file('model',str(model),'data.json')
    if model!="text-chat-davinci-002-20230126":  
        use=int(use)+int(token)
    write_to_file('usage',use,'data.json')

async def handle_response(message) -> str:
    response = await sync_to_async(chatbot.ask)(message)
    responseMessage = response["choices"][0]["text"]
    nowusage=response["usage"]["total_tokens"]
    model=response["model"]
    write(str(nowusage),str(model))
    return responseMessage
