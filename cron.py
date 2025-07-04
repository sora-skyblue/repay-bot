from linebot import LineBotApi
from linebot.models import TextSendMessage
import os

line_bot_api = LineBotApi(os.environ['LINE_CHANNEL_ACCESS_TOKEN'])
GROUP_ID = '★あなたのグループIDをここに入れてね★'

message = TextSendMessage(
    text="📅 今月の返済をお願いします！\n『5000円 @Aさんに返済』の形式で入力してください。"
)

line_bot_api.push_message(GROUP_ID, message)
