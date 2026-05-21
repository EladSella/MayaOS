import urllib.request
import json

api_key = "AIzaSyAVgY_AafnKfuGcJNibXcHIHfb6ViFKXRc"
url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"

try:
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req) as response:
        models = json.loads(response.read().decode())
        print([m['name'] for m in models.get('models', []) if 'generateContent' in m.get('supportedGenerationMethods', [])])
except Exception as e:
    print(e)
