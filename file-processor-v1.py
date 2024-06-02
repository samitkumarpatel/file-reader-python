import threading
import queue
import redis
import websockets
from flask import Flask, request, jsonify
import time
import os
import asyncio
app = Flask(__name__)
message_sink = queue.Queue()

# File processor function
def process_file(file_name):
    lines, words, letters = 0, 0, 0
    try:
        with open(file_name, 'r') as file:
            data = file.read()
        lines = len(data.split('\n'))
        words = len(data.split())
        letters = len(data.replace(' ', ''))
        print(f'File {file_name} has been processed with Lines: {lines}, Words: {words}, Letters: {letters}')
        return {'lines': lines, 'words': words, 'letters': letters}
    except Exception as e:
        print(e)
        return {'error': str(e)}

def process_file_v2(file_name):
    lines, words, letters = 0, 0, 0
    try:
        with open(file_name, 'rb') as file:
            data = file.read()
        try:
            text = data.decode('utf-8')
        except UnicodeDecodeError:
            text = data.decode('latin-1')  # Attempt to decode with a different encoding
        lines = len(text.split('\n'))
        words = len(text.split())
        letters = len(text.replace(' ', ''))
        print(f'File {file_name} has been processed with Lines: {lines}, Words: {words}, Letters: {letters}')
        return {'lines': lines, 'words': words, 'letters': letters}
    except Exception as e:
        print(e)
        return {'error': str(e)}

# Redis PubSub
def redis_pubsub():
    redis_client = redis.StrictRedis(host='localhost', port=6379, db=0)
    channel = 'channel'
    pubsub = redis_client.pubsub()
    pubsub.subscribe(channel)
    print(f"Subscribed to {channel}. Waiting for messages...")
    
    for message in pubsub.listen():
        if message['type'] == 'message':
            data = message['data'].decode('utf-8')
            print(f"Received: {data}")
            message_sink.put('Received Message, Processing it! ...')
            result = process_file_v2(data)
            message_sink.put(result)

# WebSocket server
def websocket_server():
    async def handler(websocket, path):
        while True:
            message = message_sink.get()
            await websocket.send(str(message))

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    server = websockets.serve(handler, 'localhost', 5001)
    loop.run_until_complete(server)
    print('WebSocket Started ...')
    loop.run_forever()

# Flask server
@app.route('/')
def home():
    ping = request.args.get('ping')
    if ping:
        return jsonify({'message': ping})
    return jsonify({'message': 'PONG'})

@app.route('/details', methods=['GET'])
def details():
    filename = request.args.get('fileName', 'package.json')
    result = process_file(filename)
    return jsonify(result)

def start_flask_server():
    app.run(port=5000)

if __name__ == '__main__':
    # Start Flask server in a separate thread
    threading.Thread(target=start_flask_server).start()

    # Start Redis subscriber in a separate thread
    threading.Thread(target=redis_pubsub).start()

    # Run WebSocket server in the main thread
    websocket_server()
