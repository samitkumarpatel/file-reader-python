import asyncio
import threading
import redis
import websockets
from flask import Flask, request, jsonify
import os
from concurrent.futures import ThreadPoolExecutor

# Environment Variables
flask_host = os.getenv('FLASK_HOST', '0.0.0.0')
flask_port = int(os.getenv('FLASK_PORT', 5001))
web_socket_host = os.getenv('WEB_SOCKET_HOST', '0.0.0.0')
web_socket_port = int(os.getenv('WEB_SOCKET_PORT', 5002))
redis_host = os.getenv('REDIS_HOST', 'localhost')
redis_port = int(os.getenv('REDIS_PORT', 6379))
pub_sub_channel = os.getenv('PUB_SUB_CHANNEL', 'channel')
file_lookup_path = os.getenv('FILE_LOOKUP_PATH', '/tmp/upload')

# Initialize Flask app
app = Flask(__name__)
message_sink = asyncio.Queue()

def process_file_v2(file_name):
    lines, words, letters = 0, 0, 0
    try:
        with open(os.path.join(file_lookup_path, file_name), 'rb') as file:
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

async def redis_pubsub():
    redis_client = redis.StrictRedis(host=redis_host, port=redis_port, db=0)
    pubsub = redis_client.pubsub()
    pubsub.subscribe(pub_sub_channel)
    print(f"Subscribed to {pub_sub_channel}. Waiting for messages...")

    for message in pubsub.listen():
        if message['type'] == 'message':
            data = message['data'].decode('utf-8')
            print(f"Received: {data}")
            await message_sink.put('Received Message, Processing it! ...')
            result = process_file_v2(data)
            await message_sink.put(result)

async def websocket_handler(websocket, path):
    async def send_messages():
        while True:
            message = await message_sink.get()
            await websocket.send(str(message))

    sender_task = asyncio.create_task(send_messages())

    async for message in websocket:
        print(f"Received: {message}")
        await message_sink.put(message)

    await sender_task

async def websocket_server():
    server = await websockets.serve(websocket_handler, web_socket_host, web_socket_port)
    print(f'WebSocket Server started on {web_socket_host}:{web_socket_port}')
    await server.wait_closed()

@app.route('/')
def home():
    ping = request.args.get('ping')
    if ping:
        return jsonify({'message': ping})
    return jsonify({'message': 'PONG'})

@app.route('/details', methods=['GET'])
def details():
    filename = request.args.get('fileName', 'package.json')
    result = process_file_v2(filename)
    return jsonify(result)

def start_flask_server():
    from waitress import serve
    print(f'Server started on {flask_host}:{flask_port}')
    serve(app, host=flask_host, port=flask_port)

def main():
    loop = asyncio.get_event_loop()

    # Start Redis subscriber in a separate thread
    redis_thread = threading.Thread(target=lambda: asyncio.run(redis_pubsub()), daemon=True)
    redis_thread.start()

    # Start Flask server in a separate thread
    flask_thread = threading.Thread(target=start_flask_server, daemon=True)
    flask_thread.start()

    # Run WebSocket server in the main thread
    loop.run_until_complete(websocket_server())

if __name__ == '__main__':
    main()
