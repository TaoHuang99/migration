import requests

url = "http://192.168.122.125:8021/container/service_migration/cmd"
data = {
    "container_name": "piskes",
    "dstnode": "192.168.122.71"
}

headers = {
    'Content-Type': 'application/json',
}

try:
    response = requests.post(url, json=data, headers=headers)
    if response.status_code == 200:
        print("HTTP POST request successful")
    else:
        print(f"HTTP POST request failed with status code: {response.status_code}")
except requests.exceptions.RequestException as e:
    print(f"An error occurred: {e}")
