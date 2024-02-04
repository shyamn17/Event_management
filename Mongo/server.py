from flask import Flask, Response, request, jsonify
import pymongo
from bson.objectid import ObjectId
import requests
import json
import time

app = Flask(__name__)

try:
    mongo = pymongo.MongoClient(
        host="localhost", port=27017, serverSelectionTimeoutMS=1000
    )
    db = mongo.event_management
    mongo.server_info()
except pymongo.errors.ServerSelectionTimeoutError as e:
    print(f"Could not connect to MongoDB: {e}")
except Exception as e:
    print(f"An unexpected error occurred: {e}")

@app.route("/api/v1/events/submit", methods=["POST"])
def submit_event():
    try:
        event_data = request.json
        db_response = db.events.insert_one(event_data)
        inserted_id = db_response.inserted_id
        print(f"Event logged to database with ID: {inserted_id}")
        forward_event_to_consumers(event_data)
        return jsonify({"message": "Event submitted successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/v1/events/create", methods=["POST"])
def create_event():
    try:
        event_data = request.json
        process_event(event_data)
        db_response = db.events.insert_one(event_data)
        inserted_id = db_response.inserted_id
        print(f"Event created with ID: {inserted_id}")
        forward_event_to_consumers(event_data)
        return jsonify({"message": "Event created", "id": str(inserted_id)}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def process_event(event_data):
    pass

def forward_event_to_consumers(event_data):
    consumer_urls = ["http://consumer1.com/api/v1/events/process", "http://consumer2.com/api/v1/events/process"]
    for consumer_url in consumer_urls:
        try:
            response = requests.post(consumer_url, json=event_data)
            
            if response.status_code != 200:
                print(f"Failed to forward event to {consumer_url}. Status code: {response.status_code}")
        except Exception as e:
            print(f"Error forwarding event to {consumer_url}: {str(e)}")

@app.route("/api/v1/events/subscribe", methods=["POST"])
def subscribe():
    try:
        event_id = request.form.get("event_id")
        if not event_id:
            return jsonify({"message": "Event ID is required for subscription"}), 400

        user_data = {"name": request.form["name"], "lastname": request.form["lastname"], "event_id": event_id}
        db_response = db.subscriptions.insert_one(user_data)
        inserted_id = db_response.inserted_id
        print(f"Subscribed user with ID: {inserted_id} to event with ID: {event_id}")
        return jsonify({"message": "Subscribed to event", "id": str(inserted_id), "event": event_id}), 200
    except Exception as ex:
        print(ex)
        return jsonify({"message": "Error subscribing to event"}), 500

def notify_subscribers_with_retry(event_id, subscribers, max_retries, retry_interval):
    retries = 0
    success = False

    while retries <= max_retries and not success:
        try:
            log_notification(event_id, subscribers)

            for subscriber in subscribers:
                send_notification(subscriber, event_id)

            success = True
        except Exception as ex:
            print(f"Error notifying subscribers: {ex}")
            retries += 1
            time.sleep(retry_interval)

    if not success:
        print(f"Notification failed after {max_retries} attempts")

@app.route("/api/v1/events/notify/<event_id>", methods=["PATCH"])
def notify_subscribers_route(event_id):
    try:
        subscribers = list(db.subscriptions.find({"event_id": event_id}))

        if not subscribers:
            return jsonify({"message": "No subscribers for the given event_id"}), 404

        notify_subscribers_with_retry(event_id, subscribers, max_retries=5, retry_interval=60)

        return jsonify({"message": "Notification attempts completed"}), 200

    except Exception as ex:
        print(ex)
        return jsonify({"message": "Error notifying subscribers"}), 500

def log_notification(event_id, subscribers):
    try:
        print("Subscribers:", subscribers)

        subscriber_ids = [ObjectId(subscriber["_id"]) for subscriber in subscribers]
        notification_data = {
            "event_id": ObjectId(event_id),
            "subscribers": subscriber_ids,
            "provider": get_provider_identifier(),
        }

        print("Notification Data:", notification_data)

        db.notifications.insert_one(notification_data)
    except Exception as ex:
        print(f"Error logging notification: {ex}")

def send_notification(subscriber, event_id):
    pass

def get_provider_identifier():
    provider_id = request.headers.get("Provider-Identification")
    return provider_id if provider_id else request.remote_addr

if __name__ == "__main__":
    app.run(port=80, debug=True)
