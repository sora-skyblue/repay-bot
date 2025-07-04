from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import json
import re
import os
from dotenv import load_dotenv
load_dotenv()

import openai
openai.api_key = os.environ['OPENAI_API_KEY']


app = Flask(__name__)

line_bot_api = LineBotApi(os.environ['LINE_CHANNEL_ACCESS_TOKEN'])
handler = WebhookHandler(os.environ['LINE_CHANNEL_SECRET'])

DATA_FILE = 'data.json'
LENDERS = {
    "@伊東　祐輔": 40000,
    "@sora.s": 93350
}

def load_data():
    try:
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    except:
        return {k: {"loan": v, "paid": 0} for k, v in LENDERS.items()}

def save_data(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f)

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_message = event.message.text
    data = load_data()

    m = re.match(r'(\d+)\s*円\s*(@.+?)に返済', user_message)
    if m:
        amount = int(m.group(1))
        target = m.group(2)

        if target in data:
            data[target]['paid'] += amount
            save_data(data)
            remain = data[target]['loan'] - data[target]['paid']
            reply = f"✅ {target}への返済 {amount}円 を記録しました。\n残額：{remain}円"
        else:
            reply = f"⚠ 登録されていない相手です：{target}"

    elif "あといくら" in user_message:
        reply = "📊 現在の残高：\n"
        for name, record in data.items():
            remain = record["loan"] - record["paid"]
            reply += f"{name}：{remain}円 残り\n"

    else:
        reply = "💬 『5000円 @Aさんに返済』の形式で入力してね！"

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply)
    )


