from quart import Quart, request, render_template
import peertube

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



        self.resolutions = []
        self.video = None

        for entry in a["files"]:
            resolution = (entry["resolution"])["id"]
            self.resolutions.append(entry["resolution"])

            if str(resolution) == str(quality):
                self.video = entry["fileUrl"]

        self.no_quality_selected = not self.video


app = Quart(__name__)

@app.route('/')
async def main():
    return await render_template('index.html')

@app.route('/<string:domain>')
async def domain_main(domain):
    return await render_template('domain_index.html')

@app.route('/<string:domain>/search/<string:term>')
async def search(domain, term):
    amount, results = peertube.search(domain, term)
    return await render_template('search_results.html', domain=domain, amount=amount, results=results)

@app.route('/<string:domain>/watch/<string:id>/')
async def video(domain, id):
    data = peertube.video(domain, id)
    quality = request.args.get("quality")
    if quality == None:
        quality = "best"
    vid = VideoWrapper(data, quality)

    return await render_template('video.html', video=vid, quality=quality)

if __name__ == "__main__":
    app.run()
