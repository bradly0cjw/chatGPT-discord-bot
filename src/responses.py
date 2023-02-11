# from revChatGPT.Official import Chatbot,Prompt
# from ...ChatGPT.src.revChatGPT.Official import Chatbot,Prompt,Conversation,AsyncChatbot
from revChatGPT.Official import Chatbot,Prompt,Conversation,AsyncChatbot
from asgiref.sync import sync_to_async
from dotenv import load_dotenv
import os


load_dotenv()
openAI_key = os.getenv("OPENAI_KEY")
openAI_model = os.getenv("ENGINE")
print(openAI_model)
chatbot = Chatbot(api_key=openAI_key, engine=openAI_model)

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

async def handle_response(message,userid) -> str:
    model=openAI_model
    write(str(0),str(model))
    response = await sync_to_async(chatbot.ask)(message,conversation_id=userid)
    print(response)
    responseMessage = response["choices"][0]["text"]
    nowusage=response["usage"]["total_tokens"]
    write(str(nowusage),str(model))
    return responseMessage
