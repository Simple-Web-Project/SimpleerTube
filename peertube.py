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

def comments(domain, id):
    url = "https://" + domain + "/api/v1/videos/" + id + "/comment-threads"
    comments_object = json.loads(requests.get(url).text)
    return comments_object


if __name__ == "__main__":
    name = get_instance_name("videos.lukesmith.xyz")
    print(name)
    #com = comments("videos.lukesmith.xyz", "591bf5dd-b02f-40f7-a2cc-b4929c52cb51")
    #print(json.dumps(com, indent=2))
    #vid = video("diode.zone", "c4f0d71b-bd8b-4641-87b0-6d9edd4fa9ce")
    #print(json.dumps(vid, indent=2))
    #_, results = search("diode.zone", "test")
    #print(json.dumps(results, indent=2))
