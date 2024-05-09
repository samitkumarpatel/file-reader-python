from flask import Flask

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
