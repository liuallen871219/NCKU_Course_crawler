import os
import sys
import requests
from flask import Flask, jsonify, request, abort, send_file
from dotenv import load_dotenv
from linebot import LineBotApi, WebhookParser
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from bs4 import BeautifulSoup
from fsm import TocMachine
from utils import send_text_message

load_dotenv()


machine = TocMachine(
    states=["user", "state1", "state2","show_fsm","equal","larger","smaller"],
    transitions=[
        {
            "trigger": "advance",
            "source": "user",
            "dest": "state1",
            "conditions": "is_going_to_state1",
        },
        {
            "trigger": "advance",
            "source": "state1",
            "dest": "state2",
            "conditions": "is_going_to_state2",
        },
        {
            "trigger": "advance",
            "source": "user",
            "dest": "show_fsm",
            "conditions": "is_going_to_show_fsm",
        },
        {
            "trigger": "advance",
            "source": "state1",
            "dest": "user",
            "conditions": "is_going_to_user",
        },
        {
            "trigger": "advance",
            "source": "show_fsm",
            "dest": "smaller",
            "conditions": "is_going_to_smaller",
        },
        {
            "trigger": "advance",
            "source": "show_fsm",
            "dest": "equal",
            "conditions": "is_going_to_equal",
        },
        {
            "trigger": "advance",
            "source": "show_fsm",
            "dest": "larger",
            "conditions": "is_going_to_larger",
        },
        {
            "trigger": "advance",
            "source": "smaller",
            "dest": "smaller",
            "conditions": "is_going_to_smaller",
        },
        {
            "trigger": "advance",
            "source": "smaller",
            "dest": "larger",
            "conditions": "is_going_to_larger",
        },
        {
            "trigger": "advance",
            "source": "smaller",
            "dest": "equal",
            "conditions": "is_going_to_equal",
        },
        {
            "trigger": "advance",
            "source": "larger",
            "dest": "larger",
            "conditions": "is_going_to_larger",
        },
        {
            "trigger": "advance",
            "source": "larger",
            "dest": "equal",
            "conditions": "is_going_to_equal",
        },
        {
            "trigger": "advance",
            "source": "larger",
            "dest": "smaller",
            "conditions": "is_going_to_smaller",
        },
        {
            "trigger": "advance",
            "source": "larger",
            "dest": "user",
            "conditions": "restart",
        },
        {
            "trigger": "advance",
            "source": "smaller",
            "dest": "user",
            "conditions": "restart",
        },
        {
            "trigger": "advance",
            "source": "show_fsm",
            "dest": "user",
            "conditions": "restart",
        },
        {
            "trigger": "advance",
            "source": "user",
            "dest": "user",
            "conditions": "restart",
        },
        {"trigger": "go_back", "source": "state1", "dest": "user"},
        {"trigger": "go_back_state1", "source": "state2", "dest": "state1"},
        {"trigger": "go_back_user", "source": "equal", "dest": "user"},

    ],
    initial="user",
    auto_transitions=False,
    show_conditions=True,
)

app = Flask(__name__, static_url_path="")


# get channel_secret and channel_access_token from your environment variable
channel_secret = os.getenv("LINE_CHANNEL_SECRET", None)
channel_access_token = os.getenv("LINE_CHANNEL_ACCESS_TOKEN", None)
if channel_secret is None:
    print("Specify LINE_CHANNEL_SECRET as environment variable.")
    sys.exit(1)
if channel_access_token is None:
    print("Specify LINE_CHANNEL_ACCESS_TOKEN as environment variable.")
    sys.exit(1)

line_bot_api = LineBotApi(channel_access_token)
parser = WebhookParser(channel_secret)


@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers["X-Line-Signature"]
    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # parse webhook body
    try:
        events = parser.parse(body, signature)
    except InvalidSignatureError:
        abort(400)

    # if event is MessageEvent and message is TextMessage, then echo text
    for event in events:
        if not isinstance(event, MessageEvent):
            continue
        if not isinstance(event.message, TextMessage):
            continue

        line_bot_api.reply_message(
            event.reply_token, TextSendMessage(text=event.message.text)
        )

    return "OK"


@app.route("/webhook", methods=["POST"])
def webhook_handler():
    signature = request.headers["X-Line-Signature"]
    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info(f"Request body: {body}")

    # parse webhook body
    try:
        events = parser.parse(body, signature)
    except InvalidSignatureError:
        abort(400)

    # if event is MessageEvent and message is TextMessage, then echo text
    for event in events:
        if not isinstance(event, MessageEvent):
            continue
        if not isinstance(event.message, TextMessage):
            continue
        if not isinstance(event.message.text, str):
            continue
        print(f"\nFSM STATE: {machine.state}")
        print(f"REQUEST BODY: \n{body}")
        response = machine.advance(event)
        if response == False:
            send_text_message(event.reply_token, "Not Entering any State")

    return "OK"


@app.route("/show-fsm", methods=["GET"])
def show_fsm():
    machine.get_graph().draw("my_fsm.png", prog="dot", format="png")
    return send_file("my_fsm.png", mimetype="image/png")


if __name__ == "__main__":
    port = os.environ.get("PORT", 8000)
    app.run(host="0.0.0.0", port=port, debug=True)


# def movie():
#     target_url = 'https://movies.yahoo.com.tw/'
#     rs = requests.session()
#     res = rs.get(target_url, verify=False)
#     res.encoding = 'utf-8'
#     soup = BeautifulSoup(res.text, 'html.parser')   
#     content = ""
#     for index, data in enumerate(soup.select('div.movielist_info h2 a')):
#         if index == 10:
#             return content       
#         title = data.text
#         link =  data['href']
#         content += '{}\n{}\n'.format(title, link)
#     return content