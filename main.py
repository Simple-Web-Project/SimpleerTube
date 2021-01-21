from quart import Quart, request, render_template, redirect
from datetime import datetime
import peertube

commit = "not found"
with open(".git/refs/heads/main") as file:
    for line in file:
        commit = line
        # we only expect one line
        break

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

        for entry in self.files:
            resolution = (entry["resolution"])["id"]
            self.resolutions.append(entry["resolution"])

            if str(resolution) == str(quality):
                self.video = entry["fileUrl"]

        self.no_quality_selected = not self.video


# Format:
# key: domain
# entry: [ instance_name, last_time_updated ]
cached_instance_names = {}

# cache the instance names so we don't have to send a request to the domain every time someone
# loads any site 
def get_instance_name(domain):
    if domain in cached_instance_names:
        last_time_updated = (cached_instance_names[domain])[1]
        time_diff = datetime.now() - last_time_updated

        # only check once every day
        if time_diff.days != 0:
            cached_instance_names[domain] = [
                peertube.get_instance_name(domain),
                datetime.now()
            ]
    else:
        cached_instance_names[domain] = [
            peertube.get_instance_name(domain),
            datetime.now()
        ]

    return (cached_instance_names[domain])[0]






app = Quart(__name__)

@app.route("/")
async def main():
    return await render_template("index.html")


@app.route("/<string:domain>/")
async def domain_main(domain):
    return await render_template(
        "domain_index.html",
        domain=domain,
        instance_name=get_instance_name(domain),
        commit=commit,
    )


@app.route("/<string:domain>/search", methods=["POST"])
async def search_redirect(domain):
    query = (await request.form)["query"]
    return redirect("/" + domain + "/search/" + query)


@app.route("/<string:domain>/search/<string:term>")
async def search(domain, term):
    amount, results = peertube.search(domain, term)
    return await render_template(
        "search_results.html",
        domain=domain,
        instance_name=get_instance_name(domain),
        commit=commit,

        amount=amount,
        results=results,
        search_term=term,
    )


@app.route("/<string:domain>/watch/<string:id>/")
async def video(domain, id):
    data = peertube.video(domain, id)
    quality = request.args.get("quality")
    embed = request.args.get("embed")
    if quality == None:
        quality = "best"
    vid = VideoWrapper(data, quality)

    # only make a request for the comments if commentsEnabled
    comments = ""
    if data["commentsEnabled"]:
        comments = peertube.get_comments(domain, id)

    return await render_template(
        "video.html",
        domain=domain,
        commit=commit,
        instance_name=get_instance_name(domain),

        video=vid,
        comments=comments,
        quality=quality,
        embed=embed,
    )


if __name__ == "__main__":
    app.run()
