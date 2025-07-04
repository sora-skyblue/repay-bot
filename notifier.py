from linebot import LineBotApi
from linebot.models import TextSendMessage
import os
import json
from dotenv import load_dotenv

load_dotenv()

# 環境変数から読み込み
line_bot_api = LineBotApi(os.environ['LINE_CHANNEL_ACCESS_TOKEN'])
TO = os.environ['NOTIFY_TARGET_ID']  # 送信先のユーザーまたはグループID

DATA_FILE = 'data.json'

def load_data():
    try:
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    except:
        return {}

def create_summary(data):
    if not data:
        return "📊 現在の記録はありません。"

    lines = ["📅 毎月の借金残高のお知らせ："]
    for name, record in data.items():
        remain = record['loan'] - record['paid']
        lines.append(f"{name}：{remain}円 残り")
    return "\n".join(lines)

def main():
    data = load_data()
    message = create_summary(data)
    line_bot_api.push_message(TO, TextSendMessage(text=message))

if __name__ == "__main__":
    main()
