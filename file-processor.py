from flask import Flask

import json
import logging
app = Flask(__name__)    
logger = logging.getLogger('waitress')
logger.setLevel(logging.INFO)

@app.route("/")
def message():
    return {
        "message": "pong"
    }

@app.route("/details")
def file_processor():
    filename = 'requirment.txt'
    lines = words = letters = 0

    with open(filename, 'r') as file:
        for line in file:
            lines += 1
            words += len(line.split())
            letters += sum(c.isalpha() for c in line)
    return {
        "lines": lines,
        "words": words,
        "letters": letters
    }

if __name__ == "__main__":
    from waitress import serve
    serve(app, host="0.0.0.0", port=5000)