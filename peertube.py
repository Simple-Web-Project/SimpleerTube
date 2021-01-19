from bs4 import BeautifulSoup
import requests
import json

def get_instance_name(domain):
    soup = BeautifulSoup(requests.get("https://" + domain).text)
    return soup.find('span', class_="instance-name").text

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


if __name__ == "__main__":
    vid = video("diode.zone", "5405dac8-05c1-4512-b842-67be43ce7442")
    print(json.dumps(vid, indent=2))
    #_, results = search("diode.zone", "test")
    #print(json.dumps(results, indent=2))
