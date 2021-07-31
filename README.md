# SimpleerTube

To see active instances, refer to [Our Project Page](https://simple-web.metalune.xyz/projects/simpleertube.html)

For the rest of the documentation, https://simpleertube.metalune.xyz will be used as an example instance.

If you want to visit any page from your PeerTube instance of choice in SimpleerTube, just prepend https://simpleertube.metalune.xyz to the URL.
So, `https://videos.lukesmith.xyz/accounts/luke` becomes `https://simpleertube.metalune.xyz/videos.lukesmith.xyz/accounts/luke`.

If you visit the main page, you can search globally (it uses [Sepia Search](https://sepiasearch.org) in the backend).

## Setup

You need to setup a few dependencies first, usually using pip (`sudo apt install python3-pip` on Debian):

```
$ sudo pip3 install quart bs4 html2text lxml
```

**Note:** If there are other dependencies that are not packaged with your system, please report them to us so they can be added to this README.

Now you can run a development environment like so:

```
$ python3 main.py # Starts on localhost:5000
$ python3 main.py 192.168.42.2 # Starts on 192.168.42.2:5000
$ python3 main.py 7171 # Starts on localhost:7171
$ python3 main.py 192.168.42.2 7171 # Starts on 192.168.42.2:7171
$ python3 main.py ::1 7171 # Also works with IPv6 addresses
```

It is strongly disrecommended to run the production using this command. Instead, please refer to the [Quart deployment docs](https://pgjones.gitlab.io/quart/tutorials/deployment.html).

## TODO-Tracker

We have our TODO-Tracker hosted on todo.sr.ht: [SimpleerTube](https://todo.sr.ht/~metalune/SimpleerTube)

## License

This software is distributed under the AGPLv3 license. You can find a copy in the [LICENSE](LICENSE) file.

