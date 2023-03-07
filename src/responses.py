from revChatGPT.V1 import AsyncChatbot
from revChatGPT.V3 import Chatbot
from dotenv import load_dotenv
import os


load_dotenv()
OPENAI_EMAIL = os.getenv("OPENAI_EMAIL")
OPENAI_PASSWORD = os.getenv("OPENAI_PASSWORD")
SESSION_TOKEN = os.getenv("SESSION_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ENGINE = os.getenv("OPENAI_ENGINE")
CHAT_MODEL = os.getenv("CHAT_MODEL")

if CHAT_MODEL ==  "UNOFFICIAL":
    unofficial_chatbot = AsyncChatbot(config={"email":OPENAI_EMAIL, "password":OPENAI_PASSWORD, "session_token":SESSION_TOKEN})
elif CHAT_MODEL == "OFFICIAL":
    offical_chatbot = Chatbot(api_key=OPENAI_API_KEY, engine=ENGINE)

async def official_handle_response(message) -> str:
    return offical_chatbot.ask(message)

async def unofficial_handle_response(message) -> str:
    async for response in unofficial_chatbot.ask(message):
        responseMessage = response["message"]
    return responseMessage
# openAI_key = os.getenv("OPENAI_KEY")
# openAI_model = os.getenv("ENGINE")
# print(openAI_model)


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
    if model=="text-davinci-003":  
        use=int(use)+int(token)
    write_to_file('usage',use,'data.json')

# async def handle_response(message,userid) -> str:
#     model=openAI_model
#     write(str(0),str(model))
#     response = await sync_to_async(chatbot.ask)(message,conversation_id=userid)
#     print(response)
#     responseMessage = response["choices"][0]["text"]
#     nowusage=response["usage"]["total_tokens"]
#     write(str(nowusage),str(model))
#     return responseMessage
