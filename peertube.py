from bs4 import BeautifulSoup
import requests
import json

def get_instance_name(domain):
    soup = BeautifulSoup(requests.get("https://" + domain).text, "lxml")
    title = soup.find('title')
    if title:
        return title.text
    else:
        return "PeerTube Instance"

def video(domain, id):
    video_url = "https://" + domain + "/api/v1/videos/" + id
    video_object = json.loads(requests.get(video_url).text)
    return video_object

def search(domain, term, start = 0, count = 10):
    search_url = "https://" + domain + "/api/v1/search/videos?start=" + str(start) + "&count=" + str(count) + "&search=" + term + "&sort=-match&searchTarget=local"
    search_object = json.loads(requests.get(search_url).text)

    amount = search_object["total"]
    results = search_object["data"]

    return amount, results

def get_comments(domain, id):
    url = "https://" + domain + "/api/v1/videos/" + id + "/comment-threads"
    return json.loads(requests.get(url).text)

# --- Accounts ---

def account_video_channels(domain, name):
    url = "https://" + domain + "/api/v1/accounts/" + name + "/video-channels"
    return json.loads(requests.get(url).text)

def account_videos(domain, name):
    url = "https://" + domain + "/api/v1/accounts/" + name + "/videos"
    return json.loads(requests.get(url).text)

def account(domain, name):
    url = "https://" + domain + "/api/v1/accounts/" + name
    return json.loads(requests.get(url).text)

# --- Video Channels ---

def video_channel_videos(domain, name):
    url = "https://" + domain + "/api/v1/video-channels/" + name + "/videos"
    return json.loads(requests.get(url).text)

def video_channel_video_playlists(domain, name):
    url = "https://" + domain + "/api/v1/video-channels/" + name + "/video-playlists"
    return json.loads(requests.get(url).text)

def video_channel(domain, name):
    url = "https://" + domain + "/api/v1/video-channels/" + name
    return json.loads(requests.get(url).text)

if __name__ == "__main__":
    #name = get_instance_name("videos.lukesmith.xyz")
    #print(name)

    #com = get_comments("videos.lukesmith.xyz", "d1bfb082-b203-43dc-9676-63d28fe65db5")
    #print(json.dumps(com, indent=2))

    #vid = video("diode.zone", "c4f0d71b-bd8b-4641-87b0-6d9edd4fa9ce")
    #print(json.dumps(vid, indent=2))

    _, results = search("diode.zone", "test")
    print(json.dumps(results, indent=2))

    #video_channels = account_video_channels("peer.tube", "mouse@peertube.dsmouse.net")
    #print(json.dumps(video_channels, indent=2))
