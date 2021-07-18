from quart import Quart, request, render_template, redirect
from datetime import datetime
from math import ceil
import peertube
import html2text

h2t = html2text.HTML2Text()
h2t.ignore_links = True

# Wrapper, only containing information that's important for us, and in some cases provides simplified ways to get information
class VideoWrapper:
    def __init__(self, a, quality):
        self.name = a["name"]
        self.channel = a["channel"]
        self.description = a["description"]
        self.thumbnailPath = a["thumbnailPath"]

        self.category = a["category"]
        self.licence = a["licence"]
        self.language = a["language"]
        self.privacy = a["privacy"]
        self.tags = a["tags"]

        self.views = a["views"]
        self.likes = a["likes"]
        self.dislikes = a["dislikes"]

        self.embedPath = a["embedPath"]
        self.commentsEnabled = a["commentsEnabled"]

        self.resolutions = []
        self.video = None

        self.files = a["files"]
        if len(self.files) == 0:
            self.files = ((a["streamingPlaylists"])[0])["files"]

        self.default_res = None

        for entry in self.files:
            resolution = (entry["resolution"])["id"]
            self.resolutions.append(entry["resolution"])

            # chose the default quality
            if resolution != 0 and quality == None:
                if self.default_res == None:
                    self.default_res = resolution
                    self.video = entry["fileUrl"]
                elif abs(720 - resolution) < abs(720 - self.default_res):
                    self.default_res = resolution
                    self.video = entry["fileUrl"]

            if str(resolution) == str(quality):
                self.video = entry["fileUrl"]

        if quality == None:
            self.quality = self.default_res
        else:
            self.quality = quality

        self.no_quality_selected = not self.video


# Helper Class for using caches
class Cache:
    def __init__(self):
        self.dict = {}

    def get(self, arg, func):
        if arg in self.dict:
            last_time_updated = (self.dict[arg])[1]
            time_diff = datetime.now() - last_time_updated

            if time_diff.days > 0:
                self.dict[arg] = [
                    func(arg),
                    datetime.now()
                ]
        else:
            self.dict[arg] = [
                func(arg),
                datetime.now()
            ]

        return (self.dict[arg])[0]


cached_instance_names = Cache()
cached_account_infos = Cache()
cached_video_channel_infos = Cache()

# cache the instance names so we don't have to send a request to the domain every time someone
# loads any site 
def get_instance_name(domain):
    return cached_instance_names.get(domain, peertube.get_instance_name)


# simple wrapper that is used inside the cached_account_infos
def get_account(info):
    info = info.split("@")
    return peertube.account(info[1], info[0])

def get_account_info(name):
    return cached_account_infos.get(name, get_account)


# simple wrapper that is used inside the cached_video_channel_infos
def get_video_channel(info):
    info = info.split("@")
    return peertube.video_channel(info[1], info[0])

def get_video_channel_info(name):
    return cached_video_channel_infos.get(name, get_video_channel)




app = Quart(__name__)

@app.route("/")
async def main():
    return await render_template(
        "index.html",
    )

@app.route("/search", methods = ["POST"])
async def simpleer_search_redirect():
    query = (await request.form)["query"]
    return redirect("/search/" + query)

@app.route("/search/<string:query>", defaults = {"page": 1})
@app.route("/search/<string:query>/<int:page>")
async def simpleer_search(query, page):
    results = peertube.sepia_search(query, (page - 1) * 10)
    return await render_template(
        "simpleer_search_results.html",


        results = results,
        query = query,

        # details for pagination
        page=page,
        pages_total=ceil(results["total"] / 10),
    )



@app.route("/<string:domain>/")
async def instance(domain):
    return redirect("/" + domain + "/videos/trending")

@app.route("/<string:domain>/videos/local", defaults = {"page": 1})
@app.route("/<string:domain>/videos/local/<int:page>")
async def instance_videos_local(domain, page):
    vids = peertube.get_videos_local(domain, (page - 1) * 10)
    return await render_template(
        "instance/local.html",
        domain=domain,
        instance_name=get_instance_name(domain),

        videos = vids,

        # details for pagination
        page=page,
        pagination_url="/" + domain + "/videos/local/",
        pages_total=ceil(vids["total"] / 10),
    )

@app.route("/<string:domain>/videos/trending", defaults = {"page": 1})
@app.route("/<string:domain>/videos/trending/<int:page>")
async def instance_videos_trending(domain, page):
    vids = peertube.get_videos_trending(domain, (page - 1) * 10)
    return await render_template(
        "instance/trending.html",
        domain=domain,
        instance_name=get_instance_name(domain),

        videos = vids,

        # details for pagination
        page=page,
        pagination_url="/" + domain + "/videos/trending/",
        pages_total=ceil(vids["total"] / 10),
    )


@app.route("/<string:domain>/videos/most-liked", defaults = {"page": 1})
@app.route("/<string:domain>/videos/most-liked/<int:page>")
async def instance_videos_most_liked(domain, page):
    vids = peertube.get_videos_most_liked(domain, (page - 1) * 10)
    return await render_template(
        "instance/most-liked.html",
        domain=domain,
        instance_name=get_instance_name(domain),

        videos = vids,

        # details for pagination
        page=page,
        pagination_url="/" + domain + "/videos/most-liked/",
        pages_total=ceil(vids["total"] / 10),
    )


@app.route("/<string:domain>/videos/recently-added", defaults = {"page": 1})
@app.route("/<string:domain>/videos/recently-added/<int:page>")
async def instance_videos_recently_added(domain, page):
    vids = peertube.get_videos_recently_added(domain, (page - 1) * 10)
    return await render_template(
        "instance/recently-added.html",
        domain=domain,
        instance_name=get_instance_name(domain),

        videos = vids,

        # details for pagination
        page=page,
        pagination_url="/" + domain + "/videos/recently-added/",
        pages_total=ceil(vids["total"] / 10),
    )




@app.route("/<string:domain>/search", methods=["POST"])
async def search_redirect(domain):
    query = (await request.form)["query"]
    return redirect("/" + domain + "/search/" + query)


@app.route("/<string:domain>/search/<string:term>", defaults = {"page": 1})
@app.route("/<string:domain>/search/<string:term>/<int:page>")
async def search(domain, term, page):
    results = peertube.search(domain, term, (page - 1) * 10)
    return await render_template(
        "search_results.html",
        domain=domain,
        instance_name=get_instance_name(domain),

        results=results,
        search_term=term,

        # details for pagination
        page=page,
        pagination_url="/" + domain + "/search/" + term + "/",
        pages_total=(results["total"] / 10)
    )

@app.route("/<string:domain>/videos/watch/<string:id>/")
async def video(domain, id):
    data = peertube.video(domain, id)
    quality = request.args.get("quality")
    embed = request.args.get("embed")
    vid = VideoWrapper(data, quality)
    quality = int(vid.quality)

    # only make a request for the comments if commentsEnabled
    comments = ""
    if data["commentsEnabled"]:
        comments = peertube.get_comments(domain, id)

        # Strip the HTML from the comments and convert them to plain text
        new_comments = {"total": comments["total"], "data": []}
        for comment in comments["data"]:
            text = h2t.handle(comment["text"]).strip().strip("\n")
            comment["text"] = text
            new_comments["data"].append(comment)
        comments = new_comments
            


    return await render_template(
        "video.html",
        domain=domain,
        instance_name=get_instance_name(domain),

        video=vid,
        comments=comments,
        quality=quality,
        embed=embed,
    )


def build_channel_or_account_name(domain, name):
    if '@' in name:
        return name
    return name + "@" + domain

# --- Accounts ---

@app.route("/<string:domain>/accounts/<string:name>")
async def accounts_redirect(domain, name):
    return redirect("/" + domain + "/accounts/" + name + "/video-channels")

@app.route("/<string:domain>/accounts/<string:name>/video-channels", defaults = {"page": 1})
@app.route("/<string:domain>/accounts/<string:name>/video-channels/<int:page>")
async def account__video_channels(domain, name, page):
    video_channels = peertube.account_video_channels(domain, name, (page - 1) * 10)
    return await render_template(
        "accounts/video_channels.html",
        domain=domain,
        instance_name=get_instance_name(domain),

        name = name,
        account = get_account_info(build_channel_or_account_name(domain, name)),
        video_channels = video_channels,

        # details for pagination
        page=page,
        pagination_url="/" + domain + "/accounts/" + name + "/video-channels/",
        pages_total=ceil(video_channels["total"] / 10)
    )

@app.route("/<string:domain>/accounts/<string:name>/videos", defaults = {"page": 1})
@app.route("/<string:domain>/accounts/<string:name>/videos/<int:page>")
async def account__videos(domain, name, page):
    vids = peertube.account_videos(domain, name, (page - 1) * 10)
    return await render_template(
        "accounts/videos.html",
        domain=domain,
        instance_name=get_instance_name(domain),

        name = name,
        account = get_account_info(build_channel_or_account_name(domain, name)),
        videos = vids,

        # details for pagination
        page=page,
        pagination_url="/" + domain + "/accounts/"  + name + "/videos/",
        pages_total=ceil(vids["total"] / 10)
    )

@app.route("/<string:domain>/accounts/<string:name>/about")
async def account__about(domain, name):
    return await render_template(
        "accounts/about.html",
        domain=domain,
        instance_name=get_instance_name(domain),

        name = name,
        account = get_account_info(build_channel_or_account_name(domain, name)),
        about = peertube.account(domain, name)
    )

# --- Video-Channels ---

@app.route("/<string:domain>/video-channels/<string:name>")
async def video_channels_redirect(domain, name):
    return redirect("/" + domain + "/video-channels/" + name + "/videos")

@app.route("/<string:domain>/video-channels/<string:name>/videos", defaults = {"page": 1})
@app.route("/<string:domain>/video-channels/<string:name>/videos/<int:page>")
async def video_channels__videos(domain, name, page):
    vids = peertube.video_channel_videos(domain, name, (page - 1) * 10)
    return await render_template(
        "video_channels/videos.html",
        domain=domain,
        instance_name=get_instance_name(domain),

        name = name,
        video_channel = get_video_channel_info(build_channel_or_account_name(domain, name)),
        page=page,
        pagination_url="/" + domain + "/video-channels/" + name + "/videos/",
        pages_total=ceil(vids["total"] / 10),
        videos = vids,
    )

@app.route("/<string:domain>/video-channels/<string:name>/video-playlists", defaults = {"page": 1})
@app.route("/<string:domain>/video-channels/<string:name>/video-playlists/<int:page>")
async def video_channels__video_playlists(domain, name, page):
    video_playlists = peertube.video_channel_video_playlists(domain, name, (page - 1) * 10)
    return await render_template(
        "video_channels/video_playlists.html",
        domain=domain,
        instance_name=get_instance_name(domain),

        name = name,
        video_channel = get_video_channel_info(build_channel_or_account_name(domain, name)),
        video_playlists = video_playlists,

        page=page,
        pagination_url="/" + domain + "/video-channels/" + name + "/video-playlists/",
        pages_total=ceil(video_playlists["total"] / 10)
    )

@app.route("/<string:domain>/video-channels/<string:name>/about")
async def video_channels__about(domain, name):
    return await render_template(
        "video_channels/about.html",
        domain=domain,
        instance_name=get_instance_name(domain),

        name = name,
        video_channel = get_video_channel_info(build_channel_or_account_name(domain, name)),
        about = peertube.video_channel(domain, name)
    )

if __name__ == "__main__":
    app.run()
