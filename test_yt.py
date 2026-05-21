import urllib.request
import re
import random

def test():
    url = 'https://www.youtube.com/results?search_query=5+minute+guided+meditation'
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    html = urllib.request.urlopen(req).read().decode('utf-8')
    video_ids = re.findall(r'"videoId":"([a-zA-Z0-9_-]{11})"', html)
    unique_ids = list(dict.fromkeys(video_ids))[:10]
    print('Found IDs:', unique_ids)

if __name__ == "__main__":
    test()
