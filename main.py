import json
import sys, os

import requests
from flask import Flask, request

import settings

app = Flask(__name__)

ACCESS_TOKEN = os.environ.get('ACCESS_TOKEN', settings.ACCESS_TOKEN)
VERIFY_TOKEN = os.environ.get('VERIFY_TOKEN', settings.VERIFY_TOKEN)


@app.route('/')
def about():
    return 'A Facebook Messenger Chatbot!'


@app.route('/', methods=['GET', 'POST'])
def main_processing():
    if (request.method == 'POST'):
        payload = request.get_data()
        # For message handling
        for sender_id, message in messaging_events(payload):
            # Start processing valid requests
            try:
                response = request_processing(sender_id, message)
                
                if response is not None:
                    send_message(ACCESS_TOKEN, sender_id, response)

                else:
                    send_message(ACCESS_TOKEN, sender_id, "Sorry I don't understand that")
            except Exception, e:
                print e
        return "ok"

    elif (request.method == 'GET'):
        print "Handling Verification."
        if request.args.get('hub.verify_token', '') == VERIFY_TOKEN:
            print "Webhook verified!"
            return request.args.get('hub.challenge', '')
        else:
            return "Wrong verification token!"



def request_processing(user_id, message):
    if message['type'] == 'text':
        message_text = message['data']
        return message_text

    else:
        return "Sorry! What do you mean?"


def messaging_events(payload):
    
    data = json.loads(payload)
    messaging_events = data["entry"][0]["messaging"]
    
    for event in messaging_events:
        sender_id = event["sender"]["id"]

        # Not a message
        if "message" not in event:
            yield sender_id, None

        # Pure text message
        if "message" in event and "text" in event["message"] and "quick_reply" not in event["message"]:
            data = event["message"]["text"].encode('unicode_escape')
            yield sender_id, {'type':'text', 'data': data, 'message_id': event['message']['mid']}
        
        # Quick reply message type
        elif "quick_reply" in event["message"]:
            data = event["message"]["quick_reply"]["payload"]
            yield sender_id, {'type':'quick_reply','data': data, 'message_id': event['message']['mid']}
        
        else:
            yield sender_id, {'type':'text','data':"I don't understand this", 'message_id': event['message']['mid']}


def send_message(token, user_id, text):
    r = requests.post("https://graph.facebook.com/v2.6/me/messages",
                      params={"access_token": token},
                      data=json.dumps({
                          "recipient": {"id": user_id},
                          "message": {"text": text.decode('unicode_escape')}
                      }),
                      headers={'Content-type': 'application/json'})
    if r.status_code != requests.codes.ok:
        print r.text


if __name__ == '__main__':
    # starting the flask instance
    if len(sys.argv) == 2:
        app.run(port=int(sys.argv[1]))
    else:
        print("Specify the Port Number")