import urllib.request
import json
import os

api_key = "AIzaSyAVgY_AafnKfuGcJNibXcHIHfb6ViFKXRc"
url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent?key={api_key}"
payload = {
    "contents": [{"parts": [{"text": "Hello"}]}]
}
req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers={'Content-Type': 'application/json'})
try:
    with urllib.request.urlopen(req) as response:
        print("Success!")
except urllib.error.HTTPError as e:
    print(e.code)
    print(e.read().decode())
