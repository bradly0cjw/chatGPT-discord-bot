from src import personas
from asgiref.sync import sync_to_async

async def official_handle_response(message, client) -> str:
    return await sync_to_async(client.chatbot.ask)(message)

async def unofficial_handle_response(message, client) -> str:
    async for response in client.chatbot.ask(message):
        responseMessage = response["message"]
    return responseMessage

async def bard_handle_response(message, client) -> str:
    response = await sync_to_async(client.chatbot.ask)(message)
    responseMessage = response["content"]
    return responseMessage

# resets conversation and asks chatGPT the prompt for a persona
async def switch_persona(persona, client) -> None:
    if client.chat_model ==  "UNOFFICIAL":
        client.chatbot.reset_chat()
        async for response in client.chatbot.ask(personas.PERSONAS.get(persona)):
            pass
    elif client.chat_model == "OFFICIAL":
        client.chatbot.reset()
        await sync_to_async(client.chatbot.ask)(personas.PERSONAS.get(persona))
    elif client.chat_model == "Bard":
        client.chatbot = client.get_chatbot_model()
        await sync_to_async(client.chatbot.ask)(personas.PERSONAS.get(persona))

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

