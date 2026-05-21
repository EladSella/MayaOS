import urllib.request
import json
import base64

# Create a tiny 1x1 base64 pixel
b64_pixel = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
data = "data:image/png;base64," + b64_pixel

req = urllib.request.Request(
    "http://localhost:8000/api/analyze_food",
    data=json.dumps({"image": data}).encode("utf-8"),
    headers={"Content-Type": "application/json"}
)

try:
    with urllib.request.urlopen(req) as response:
        print("Success:", response.read().decode("utf-8"))
except urllib.error.HTTPError as e:
    print("Error HTTP code:", e.code)
    print("Error body:", e.read().decode("utf-8"))
except Exception as e:
    print("Other error:", str(e))
