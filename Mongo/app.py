import requests

sample_event_data = {"eventname": "Sample Event", "location": "Sample Location"}
server_endpoint = "http://localhost:80/api/v1/events/create"

try:
    response = requests.post(server_endpoint, json=sample_event_data)
    if response.status_code == 200:
        print("Event submitted successfully to the server.")
    else:
        print(f"Failed to submit event to the server. Status code: {response.status_code}")
except Exception as e:
    print(f"Error during the request: {str(e)}")
