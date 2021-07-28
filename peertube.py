from bs4 import BeautifulSoup
import requests
import json

# --- Sepiasearch ---
def sepia_search(query, start=0, count=10):
    url = "https://search.joinpeertube.org/api/v1/search/videos?search=" + query + "&start=" + str(start) + "&count=" + str(count)
    return json.loads(requests.get(url).text)

# --- ----


def get_instance_name(domain):
    soup = BeautifulSoup(requests.get("https://" + domain).text, "lxml")
    title = soup.find('title')
    if title:
        return title.text
    else:
        return "PeerTube Instance"

def video(domain, id):
    url = "https://" + domain + "/api/v1/videos/" + id
    return json.loads(requests.get(url).text)

def video_captions(domain, id):
    url = "https://" + domain + "/api/v1/videos/" + id + "/captions"
    return json.loads(requests.get(url).text)

def video_captions_download(domain, id, lang):
    # URL is hardcoded to prevent further proxying. URL may change with updates, see captions API
    # eg. https://kolektiva.media/api/v1/videos/9c9de5e8-0a1e-484a-b099-e80766180a6d/captions
    url = "https://" + domain + "/lazy-static/video-captions/" + id + '-' + lang + ".vtt"
    return requests.get(url).text

def search(domain, term, start=0, count=10):
    url = "https://" + domain + "/api/v1/search/videos?start=" + str(start) + "&count=" + str(count) + "&search=" + term + "&sort=-match&searchTarget=local"
    return json.loads(requests.get(url).text)

def get_comments(domain, id):
    url = "https://" + domain + "/api/v1/videos/" + id + "/comment-threads"
    return json.loads(requests.get(url).text)

def get_videos_trending(domain, start=0, count=10):
    url = "https://" + domain + "/api/v1/videos?sort=-trending&start=" + str(start) + "&count=" + str(count)
    return json.loads(requests.get(url).text)

def get_videos_most_liked(domain, start=0, count=10):
    url = "https://" + domain + "/api/v1/videos?sort=-likes&start=" + str(start) + "&count=" + str(count)
    return json.loads(requests.get(url).text)

def get_videos_recently_added(domain, start=0, count=10):
    url = "https://" + domain + "/api/v1/videos?sort=-publishedAt&start=" + str(start) + "&count=" + str(count)
    return json.loads(requests.get(url).text)

def get_videos_local(domain, start=0, count=10):
    url = "https://" + domain + "/api/v1/videos?sort=-publishedAt&filter=local&start=" + str(start) + "&count=" + str(count)
    return json.loads(requests.get(url).text)

# --- Accounts ---

def account_video_channels(domain, name, start=0, count=10):
    url = "https://" + domain + "/api/v1/accounts/" + name + "/video-channels?start=" + str(start) + "&count=" + str(count)
    return json.loads(requests.get(url).text)

def account_videos(domain, name, start=0, count=10):
    url = "https://" + domain + "/api/v1/accounts/" + name + "/videos?start=" + str(start) + "&count=" + str(count)
    return json.loads(requests.get(url).text)

def account(domain, name):
    url = "https://" + domain + "/api/v1/accounts/" + name
    return json.loads(requests.get(url).text)

# --- Video Channels ---

def video_channel_videos(domain, name, start=0, count=10):
    url = "https://" + domain + "/api/v1/video-channels/" + name + "/videos?start=" + str(start) + "&count=" + str(count)
    return json.loads(requests.get(url).text)

def video_channel_video_playlists(domain, name, start=0, count=10):
    url = "https://" + domain + "/api/v1/video-channels/" + name + "/video-playlists?start=" + str(start) + "&count=" + str(count)
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
