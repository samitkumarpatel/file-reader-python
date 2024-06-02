from flask import Flask
import redis
import json
import logging
import threading
import websockets
import asyncio
import queue

app = Flask(__name__)    
logger = logging.getLogger('waitress')
logger.setLevel(logging.INFO)

message_sink = asyncio.Queue()
#message_sink = queue.Queue()
def process_file(fileName):
    lines = words = letters = 0

    with open(fileName, 'r') as file:
        for line in file:
            lines += 1
            words += len(line.split())
            letters += sum(c.isalpha() for c in line)
    return {
        "lines": lines,
        "words": words,
        "letters": letters
    }

@app.route("/")
def message():
    return {
        "message": "pong"
    }

@app.route("/details")
def file_processor():
    filename = 'requirment.txt'
    return process_file(filename)

def start_flask_server():
    from waitress import serve
    serve(app, host="0.0.0.0", port=5000)

# redis subscriber
def start_redis_subscriber():
    redis_client = redis.StrictRedis(host='localhost', port=6379, db=0)
    channel = 'channel'
    pubsub = redis_client.pubsub()
    pubsub.subscribe(channel)
    print(f"Subscribed to {channel}. Waiting for messages...")
    for message in pubsub.listen():
        if message['type'] == 'message':
            print(f"Received: {message['data'].decode('utf-8')}")
            message_sink.put(message['data'].decode('utf-8'))
            #result = process_file(message)
            #message_sink.put(result)


# WebSocket server
async def echo_back(websocket):
    async for message in websocket:
        await message_sink.put(message)
        message_from_sink = await message_sink.get()
        await websocket.send(message_from_sink)

async def start_ws():
    from websockets.server import serve
    async with serve(echo_back, "0.0.0.0", 5001):
        print("WebSocket started")
        await asyncio.Future()  # run forever


if __name__ == "__main__":
    threading.Thread(target=start_flask_server).start()
    threading.Thread(target=start_redis_subscriber).start()
    asyncio.run(start_ws())
    
    

    