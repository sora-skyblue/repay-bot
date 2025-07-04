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

# 初期登録
LENDERS = {
    "@伊東　祐輔": 40000,
    "@sora.s": 93350
}

# データ読み書き

def load_data():
    try:
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    except:
        return {k: {"loan": v, "paid": 0} for k, v in LENDERS.items()}

def save_data(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f)

# ルーティング

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return 'OK'

# メッセージ処理

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    msg = event.message.text
    data = load_data()

    # 使い方
    if "使い方" in msg or "ヘルプ" in msg or "何ができる" in msg:
        reply = (
            "📘 使い方ガイド：\n"
            "1️⃣ 『5000円 @名前に返済』で返済記録\n"
            "2️⃣ 『@名前に30000円借りた』で借金登録\n"
            "3️⃣ 『あといくら？』で残額を確認\n"
            "4️⃣ 雑談や相談もOK（ChatGPTが返答）\n\n"
            "例：\n・2000円 @ゆいとに返済\n・@伊東　祐輔に40000円借りた\n・あといくら？\n"
        )
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply))
        return

    # 返済メッセージ
    m = re.match(r'(\d+)\s*円\s*(@.+?)に返済', msg)
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
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply))
        return

    # 借入メッセージ
    m2 = re.match(r'@(.+?)に(\d+)円借りた', msg)
    if m2:
        name = f"@{m2.group(1).strip()}"
        amount = int(m2.group(2))

        if name not in data:
            data[name] = {"loan": amount, "paid": 0}
        else:
            data[name]["loan"] += amount

        save_data(data)
        reply = f"📌 {name}から{amount}円の借入を記録しました。"
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply))
        return

    # 残額確認
    if "あといくら" in msg or "残り" in msg or "残額" in msg:
        reply = "📊 現在の残高：\n"
        for name, record in data.items():
            remain = record["loan"] - record["paid"]
            reply += f"{name}：{remain}円 残り\n"
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply))
        return

    # ChatGPT 応答
    try:
        messages = [
            {"role": "system", "content": "あなたは借金管理Botです。返済・借入・残額確認・使い方の説明もできます。丁寧に返答してください。"},
            {"role": "user", "content": msg}
        ]
        res = openai.ChatCompletion.create(model="gpt-3.5-turbo", messages=messages)
        reply = res.choices[0].message.content.strip()
    except Exception as e:
        reply = f"⚠ ChatGPT応答エラー: {str(e)}"

    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply))

if __name__ == "__main__":
    app.run()