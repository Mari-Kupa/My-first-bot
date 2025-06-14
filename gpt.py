from langchain_core.messages import HumanMessage, SystemMessage
from langchain_gigachat import GigaChat
# from langchain_community.chat_models.gigachat import GigaChat
from config import GPT_TOKEN

chat = GigaChat(credentials=GPT_TOKEN, verify_ssl_certs=False)

role = "Ты многофункциональный бот-помощник, который готов отвечать пользователям на все вопросы"

messages = [
    SystemMessage(
        content=role
    )
]

def gpt_request(text):
    messages.append(HumanMessage(content=text))
    res = chat.invoke(messages)
    messages.append(res)
    return res.content