from flask import Flask

app = Flask(__name__)

@app.route('/')
def index():
    return 'Welcome to BlindBuddy!'

@app.route('/logs')
def logs():
    # Logic to fetch and display logs
    return 'This is the logs page'

if __name__ == '__main__':
    app.run(debug=True)
