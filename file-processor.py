from flask import Flask
import redis


redis_client = redis.StrictRedis(host='localhost', port=6379, db=0)
channel = 'channel'
pubsub = redis_client.pubsub()
pubsub.subscribe(channel)
print(f"Subscribed to {channel}. Waiting for messages...")
for message in pubsub.listen():
    if message['type'] == 'message':
        print(f"Received: {message['data'].decode('utf-8')}")


app = Flask(__name__)

@app.route("/")
def hello_world():
    return "PONG"

@app.route("/details")
def file_processor():
    filename = 'requirment.txt'
    lines = words = letters = 0

    with open(filename, 'r') as file:
        for line in file:
            lines += 1
            words += len(line.split())
            letters += sum(c.isalpha() for c in line)

    print(f'Lines: {lines}')
    print(f'Words: {words}')
    print(f'Letters: {letters}')

    return "PROCESSED"
