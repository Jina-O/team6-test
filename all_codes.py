# -*- coding: utf-8 -*
import requests
###
import json
import os
import re
import urllib.request

from bs4 import BeautifulSoup
from slackclient import SlackClient
from flask import Flask, request, make_response, render_template, jsonify

app = Flask(__name__)

slack_token = 'xoxb-503818135714-506719126544-uCmTo8DWuS9kqrPRHQYur27p'
slack_client_id = '503818135714.507453486050'
slack_client_secret = '000a42568d8f21b437b7320175dda73f'
slack_verification = 'PR5MTEUUU3wj5ArHBHB8kV8X'
sc = SlackClient(slack_token)
###
def get_answer(text, user_key):
    data_send = {
        'query': text,
        'sessionId': user_key,
        'lang': 'ko',
    }

    data_header = {
        'Authorization': 'Bearer 9517c5e431be412790bd1e0a1b23ffcb',
        'Content-Type': 'application/json; charset=utf-8'
    }

    dialogflow_url = 'https://api.dialogflow.com/v1/query?v=20150910'
    res = requests.post(dialogflow_url, data=json.dumps(data_send), headers=data_header)

    if res.status_code != requests.codes.ok:
        return '오류가 발생했습니다.'

    data_receive = res.json()
    result = {
        "speech" : data_receive['result']['fulfillment']['speech'],
        "intent" : data_receive['result']['metadata']['intentName']
    }

    real_result = result['speech']
    if(real_result == "music"):
        _crawl_naver_keywords(real_result)
    #return jsonify(real_result)

# 크롤링 함수 구현하기
def _crawl_naver_keywords(text):
    #####
    url = "https://music.bugs.co.kr/chart"
    # url = re.search(r'(https?://\S+)', text.split('|')[0]).group(0)
    req = urllib.request.Request(url)

    sourcecode = urllib.request.urlopen(url).read()
    soup = BeautifulSoup(sourcecode, "html.parser")
    ####
    # 여기에 함수를 구현해봅시다.
    keywords = []
    if "music" in url:
        for data in soup.find_all("p", class_="title"):
            if not data.get_text() in keywords:
                if len(keywords) >= 10:
                    break
                keywords.append(data.get_text().strip())

    nums = []
    for i in range(1, 11):
        nums.append(str(i))
        i += 1

    artists = []
    if "bugs" in url:
        for data in soup.find_all("p", class_="artist"):
            if not data.get_text() in keywords:
                if len(artists) >= 10:
                    break
                artists.append(data.get_text().strip())

    result = []
    for i in range(0, 10):
        result.append(nums[i] + "위: " + keywords[i] + " / " + artists[i])

    # 한글 지원을 위해 앞에 unicode u를 붙혀준다.
    return "Bugs 실시간 음악 차트 Top 10\n" + u'\n'.join(result)


# 이벤트 핸들하는 함수
def _event_handler(event_type, slack_event):
    print(slack_event["event"])

    if event_type == "app_mention":
        channel = slack_event["event"]["channel"]
        text = slack_event["event"]["text"]

        keywords = _crawl_naver_keywords(text)
        sc.api_call(
            "chat.postMessage",
            channel=channel,
            text=keywords
        )

        return make_response("App mention message has been sent", 200, )

    # ============= Event Type Not Found! ============= #
    # If the event_type does not have a handler
    message = "You have not added an event handler for the %s" % event_type
    # Return a helpful error message
    return make_response(message, 200, {"X-Slack-No-Retry": 1})


@app.route("/listening", methods=["GET", "POST"])
def hears():
    slack_event = json.loads(request.data)

    if "challenge" in slack_event:
        return make_response(slack_event["challenge"], 200, {"content_type":
                                                                 "application/json"
                                                             })

    if slack_verification != slack_event.get("token"):
        message = "Invalid Slack verification token: %s" % (slack_event["token"])
        make_response(message, 403, {"X-Slack-No-Retry": 1})

    if "event" in slack_event:
        event_type = slack_event["event"]["type"]
        return _event_handler(event_type, slack_event)

    # If our bot hears things that are not events we've subscribed to,
    # send a quirky but helpful error response
    return make_response("[NO EVENT IN SLACK REQUEST] These are not the droids\
                         you're looking for.", 404, {"X-Slack-No-Retry": 1})

app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False

@app.route('/', methods=['POST', 'GET'])
def webhook():
    content = request.args.get('content')
    userid = 'session'
    return get_answer(content, userid)

###


@app.route("/", methods=["GET"])
def index():
    return "<h1>Server is ready.</h1>"


if __name__ == '__main__':
    app.run('0.0.0.0')