#This is for testing purpose to make consumer online to offline
from flask import Flask, jsonify

app = Flask(__name__)

@app.route("/api/v1/events/process", methods=["POST"])
def process_event():
    return jsonify({"message": "Event processed successfully by consumer"})

if __name__ == "__main__":
    app.run(port=5001, debug=True) 