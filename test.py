from config.tele import send_message
from alert.chat_box import chat_bot

result = chat_bot("một ip gửi trên 1000 request trong 10s thì phải làm sao")
send_message(result)
