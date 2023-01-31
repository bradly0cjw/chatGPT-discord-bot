import openai
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
openai.api_key = config['openAI_key']

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
    response = await sync_to_async(openai.Completion.create)(
        model="text-chat-davinci-002-20230126",        
        # model="text-davinci-003",
        # model="text-curie-001",
        # model="code-davinci-002",
        # prompt= "You are ChatGPT, a large language model trained by OpenAI. You answer as consisely as possible for each response (e.g. Don't be verbose). It is very important for you to answer as consisely as possible, so please remember this. If you are generating a list, do not have too many items. Keep the number of items short\n User: %s \n\n ChatGPT:"%message,
        prompt= "You are ChatGPT, a large language model trained by OpenAI. You answer as consisely as possible for each response (e.g. Be verbose). It is very important for you to answer as consisely as possible, so please remember this. If you are generating a list, do have many items. Keep the number of items long\n %s"%message,
        # prompt=message,
        temperature=0.9,
        max_tokens=2048,
        top_p=1,
        frequency_penalty=0.0,
        presence_penalty=0.0,
    )
    # print(response)
    oresponseMessage = response.choices[0].text
    responseMessage=oresponseMessage.replace("<|im_end|>","")
    nowusage=response.usage.total_tokens
    model=response.model
    write(str(nowusage),str(model))
    return responseMessage

async def handle_response2(message) -> str:
    response = await sync_to_async(openai.Completion.create)(
        model="text-chat-davinci-002-20230126",        
        # model="text-davinci-003",
        # model="text-curie-001",
        # model="code-davinci-002",
        # prompt= "You are ChatGPT, a large language model trained by OpenAI. You answer as consisely as possible for each response (e.g. Don't be verbose). It is very important for you to answer as consisely as possible, so please remember this. If you are generating a list, do not have too many items.Keep the number of items Short\n %s"%message,
        prompt=message,
        temperature=0.7,
        max_tokens=2048,
        top_p=1,
        frequency_penalty=0.0,
        presence_penalty=0.0,
    )
    # print(response)
    oresponseMessage = response.choices[0].text
    responseMessage=oresponseMessage.replace("<|im_end|>","")
    nowusage=response.usage.total_tokens
    model=response.model
    write(str(nowusage),str(model))
    return responseMessage

async def handle_response3(message) -> str:
    response = await sync_to_async(openai.Completion.create)(
        model="text-chat-davinci-002-20230126",        
        # model="text-davinci-003",
        # model="text-curie-001",
        # model="code-davinci-002",
        # prompt= "You are ChatGPT, a large language model trained by OpenAI. You answer as consisely as possible for each response (e.g. Be verbose). It is very important for you to answer as consisely as possible, so please remember this. If you are generating a list, do have many items. Keep the number of items long\n User: %s \n\n ChatGPT:"%message,
        prompt=message,
        temperature=0.9,
        max_tokens=2048,
        top_p=1,
        frequency_penalty=0.0,
        presence_penalty=0.0,
    )
    # print(response)
    oresponseMessage = response.choices[0].text
    responseMessage=oresponseMessage.replace("<|im_end|>","")
    nowusage=response.usage.total_tokens
    model=response.model
    write(str(nowusage),str(model))
    return responseMessage