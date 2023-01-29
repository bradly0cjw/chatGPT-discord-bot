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

def write(token):
    import os
    # get config.json path
    config_dir = os.path.abspath(__file__ + "/../../")
    config_name = 'usage.txt'
    config_name2 = 'curusage.txt'
    config_path = os.path.join(config_dir, config_name)
    config_path2 = os.path.join(config_dir, config_name2)
    with open(config_path2, "w") as file:
        # Write some text to the file
        file.write(str(token))
    with open(config_path, 'r') as file:
        use=file.read()
    use=int(use)+int(token)
    # print(use)
    with open(config_path, "w") as file:
        # Write some text to the file
        file.write(str(use))

async def handle_response(message) -> str:
    response = await sync_to_async(openai.Completion.create)(
        model="text-davinci-003",
        # model="text-curie-001",
        # model="code-davinci-002",
        prompt=message,
        temperature=0.7,
        max_tokens=2048,
        top_p=1,
        frequency_penalty=0.0,
        presence_penalty=0.0,
    )
    # print(response)
    responseMessage = response.choices[0].text
    nowusage=response.usage.total_tokens
    write(str(nowusage))
    return responseMessage