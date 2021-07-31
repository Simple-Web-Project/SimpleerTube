from quart import Quart, request, render_template, redirect
from datetime import datetime
from dateutil import parser as dateutil
from math import ceil
import peertube
import html2text
import sys

h2t = html2text.HTML2Text()
h2t.ignore_links = True

# Wrapper, only containing information that's important for us, and in some cases provides simplified ways to get information
class VideoWrapper:
    def __init__(self, a, quality):
        self.name = a["name"]
        self.uuid = a["uuid"]
        self.channel = a["channel"]
        self.description = a["description"]
        self.thumbnailPath = a["thumbnailPath"]

        self.category = a["category"]
        self.licence = a["licence"]
        self.language = a["language"]
        self.captions = a["captions"]
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
    def __init__(self, criteria = lambda diff: diff.days > 0):
        self.dict = {}
        self.criteria = criteria

    def get(self, arg, func):
        if arg in self.dict:
            last_time_updated = (self.dict[arg])[1]
            time_diff = datetime.now() - last_time_updated

            if self.criteria(time_diff):
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

cached_subscriptions = Cache(criteria = lambda diff: diff.total_seconds() > 60)
cached_account_videos = Cache(criteria = lambda diff: diff.total_seconds() > 1800)
cached_channel_videos = Cache(criteria = lambda diff: diff.total_seconds() > 1800)

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

# Get latest remote videos from channel name
def get_latest_channel_videos(name):
    return cached_channel_videos.get(name, latest_channel_videos)

# Refresh latest remote videos from channel name
def latest_channel_videos(name):
    print("[CACHE] Refreshing channel videos for %s" % name)
    (name, domain) = name.split('@')
    return peertube.video_channel_videos(domain, name, 0)

# Get latest remote videos from account name
def get_latest_account_videos(name):
    return cached_account_videos.get(name, latest_account_videos)

# Refresh latest remote videos from account name
def latest_account_videos(name):
    print("[CACHE] Refreshing account videos for %s" % name)
    (name, domain) = name.split('@')
    return peertube.account_videos(domain, name, 0)

# Get local accounts subscriptions, as specified in accounts.list
def get_subscriptions_accounts():
    return cached_subscriptions.get("accounts", load_subscriptions_accounts)

# Refresh local accounts subscriptions
def load_subscriptions_accounts(_):
    return load_subscriptions("accounts")

# Get the latest videos from local accounts subscriptions, ordered by most recent; only return `limit` number of videos
def get_subscriptions_accounts_videos(limit=12):
    latest  = []
    for sub in get_subscriptions_accounts():
        result = get_latest_account_videos(sub)
        if "error" not in result: 
            account_latest = get_latest_account_videos(sub)["data"]
            latest.extend(account_latest)
        else:
            print("[WARN] Unable to get content from account " + sub)

    latest.sort(key = lambda vid: dateutil.isoparse(vid["createdAt"]), reverse=True)
    return latest[0:limit]

# Get local channels subscriptions, as specified in channel.list
def get_subscriptions_channels():
    return cached_subscriptions.get("channels", load_subscriptions_channels)

# Refresh local channels subscriptions
def load_subscriptions_channels(_):
    return load_subscriptions("channels")

# Load subscriptions from a file called `kind`.list (60s cache)
def load_subscriptions(kind):
    print("[CACHE] Refreshing subscriptions %s from %s.list" % (kind, kind))
    try:
        with open(kind + '.list', 'r') as f:
            subscriptions = map(find_subscription, f.read().splitlines())
    except Exception as e:
        print("No `channels.list` file to load for local subscriptions")
        subscriptions = []
    # Remove comment entries and empty lines
    return list(filter(lambda entry: entry != '', subscriptions))

# Builds a unified id@server from one of those syntaxes, additionally stripping extra whitespace and ignoring `#` as comments:
#   - id@server
#   - @id@server
#   - http(s)://server/c/id
#   - http(s)://server/a/id
def find_subscription(request):
    identifier = request
    identifier = identifier.split('#')[0].strip()
    # Comment line is returned as empty string
    if identifier == '': return ''
    if identifier.startswith('@'):
        # Strip @ from identifier
        return identifier[1:]

    if identifier.startswith('http'):
        identifier = identifier[4:]
        # HTTPS?
        if identifier.startswith('s'): identifier = identifier[1:]
        # Remove ://
        identifier = identifier[3:]
        parts = identifier.split('/')
        domain = parts[0]
        if parts[1] == 'a' or parts[1] == 'c':
            # Account or channel found, take the next part
            return parts[2] + '@' + domain
    else:
        # Just check there's an @ in there and it should be fine
        if '@' in identifier:
            return identifier

    # No match was found, we don't understand this URL
    print("[WARN] Identifier not understood from local subscriptions:\n%s" % request)
    return ''

# Get the latest videos from local channels subscriptions, ordered by most recent; only return `limit` number of videos
def get_subscriptions_channels_videos(limit=12):
    latest  = []
    for sub in get_subscriptions_channels():
        result = get_latest_channel_videos(sub)
        if "error" not in result:
            channel_latest = get_latest_channel_videos(sub)["data"]
            latest.extend(channel_latest)
        else:
            print("[WARN] Unable to get content from channel " + sub)
    latest.sort(key = lambda vid: dateutil.isoparse(vid["createdAt"]), reverse=True)
    return latest[0:limit]

# Get the latest videos from local channels and accounts subscriptions combined, ordered by most recent; only return `limit` number of videos; NOTE: duplicates are not handled, why would you add both an account and the corresponding channel?
def get_subscriptions_videos(limit=12):
    latest = get_subscriptions_channels_videos(limit=limit)
    latest.extend(get_subscriptions_accounts_videos(limit=limit))
    # TODO: maybe refactor so we don't have to reorder twice? Or maybe the get_ functions can take a ordered=True argument? In this case here, it would be false, because we sort after
    latest.sort(key = lambda vid: dateutil.isoparse(vid["createdAt"]), reverse=True)
    return latest[0:limit]

# Get the info about local accounts subscriptions
def get_subscriptions_accounts_info():
    return map(lambda sub: get_account_info(sub), get_subscriptions_accounts())

# Get the info about local channels subscriptions
def get_subscriptions_channels_info():
    return map(lambda sub: get_video_channel_info(sub), get_subscriptions_channels())

# Get the info about local subscriptions for accounts and channels, as a tuple of lists
def get_subscriptions_info():
    list = []
    list.extend(get_subscriptions_accounts_info())
    list.extend(get_subscriptions_channels_info())
    return list

app = Quart(__name__)

@app.route("/")
async def main():
    videos = get_subscriptions_videos(limit=12)
    # Inside subscriptions variable, you may find either an account info structure, or a channel info structure. Channels may be recognized due to `ownerAccount` property.
    subscriptions = get_subscriptions_info()
    return await render_template(
        "index.html",
        videos=videos,
        subscriptions=subscriptions,
    )

@app.route("/search", methods = ["POST"])
async def simpleer_search_redirect():
    query = (await request.form)["query"]
    return redirect("/search/" + query)

@app.route("/search", methods = ["GET"])
async def simpleer_search_get_redirect():
    query = request.args.get("query")
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
    # favicon.ico is not a domain name
    if domain == "favicon.ico": return await favicon()
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
    data["captions"] = peertube.video_captions(domain, id)
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

# --- Subtitles/captions proxying ---
@app.route("/<string:domain>/videos/watch/<string:id>/<string:lang>.vtt")
async def subtitles(domain, id, lang):
    try:
        captions = peertube.video_captions(domain, id)
        for entry in captions["data"]:
            if entry["language"]["id"] == lang: return peertube.video_captions_download(domain, entry["captionPath"].split('/')[-1])
        return await render_template(
            "error.html",
            error_number = "404",
            error_reason = "This video has no subtitles/captions inthe requested language"
        ), 404
    except Exception as e:
        return await render_template(
            "error.html",
            error_number = "500",
            error_reason = e
        ), 500

# --- Favicon ---
@app.route("/favicon.ico")
async def favicon():
    return await render_template(
        "error.html",
        error_number = "404",
        error_reason = "We don't have a favicon yet. If you would like to contribute one, please send it to ~metalune/public-inbox@lists.sr.ht"
    ), 404

# --- OpenSearch ---
@app.route("/opensearch.xml")
async def opensearch():
    try:
        with open('opensearch.xml', 'r') as f:
            return f.read().replace('$BASEURL', request.headers["Host"])
    except Exception as e:
        return await render_template(
            "error.html",
            error_number = "500",
            error_reason = e
        ), 500

if __name__ == "__main__":
    if len(sys.argv) == 3:
        interface = sys.argv[1]
        port = sys.argv[2]
    elif len(sys.argv) == 2:
        interface = "127.0.0.1"
        port = sys.argv[1]
    else:
        interface = "127.0.0.1"
        port = "5000"
    app.run(host=interface, port=port)
