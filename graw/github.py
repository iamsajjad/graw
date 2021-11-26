
import os
import sys
import shutil
from dataclasses import dataclass
import requests

API_FORMAT = "https://api.github.com/repos/{}/{}/contents/{}?ref={}"

# authorization = f'token {token}'
headers = {
    "user-agent": "graw-0.1.0",
    "Accept": "application/vnd.github.v3+json",
    # "Authorization" : authorization,
}

# set recursion limit to higher number to handle large sub directory
sys.setrecursionlimit(10000)

# create session for talking to github api
session = requests.session()


@dataclass
class API:

    org: str = ""
    repo: str = ""
    path: str = ""
    branch: str = ""

    # index of the directory that the user need to download
    node: int = 0


@dataclass
class Target:

    files: int = 0

def to_api(url):
    if url.endswith("/"):
        url = url[:-1]

    fields = url.split("/")

    API.org = fields[3]
    API.repo = fields[4]
    API.path = "/".join(fields[7:])
    API.branch = fields[6]
    # -2 because github user content dot have word `blob` in the url
    API.node = len(fields) - 2

    # print(fields)
    return API_FORMAT.format(API.org, API.repo, API.path, API.branch)

def makepath(url, force):
    fields = url.split("/")
    dirpath = "/".join(fields[API.node:-1])

    # print(fields)
    if dirpath == "":
        # target is single file
        return dirpath

    # target is directory
    node = dirpath.split("/")[0]
    if Target.files == 0 and os.path.isdir(node) and not force:
        if input("Overwrite exist directory `{}` [y/n] :  ".format(node)).lower() in ["yes", "y"]:
            shutil.rmtree(node)
        else:
            exit(0)

    os.makedirs(dirpath, exist_ok=True)

    return "{}/".format(dirpath)

def download(url, args):
    filename = url.split('/')[-1]
    placeholder = "{}{}".format(makepath(url, args.force), filename)

    print("GET : {}".format(placeholder))

    remotefile = requests.get(url, stream=True, headers=headers)

    with open(placeholder, "wb") as localfile:
        remotefile.raw.decode_content = True
        shutil.copyfileobj(remotefile.raw, localfile)

    Target.files += 1

    return filename

def fetch(point, args):
    # send request to the api
    response = session.get(url=point, headers=headers).json()

    # if the link for directory
    if type(response) == list:
        for node in response:
            if node["type"] == "file":
                # types flags
                if any([node["name"].endswith(i) for i in args.types]) or args.types[0] == "*":
                    download(node["download_url"], args)
            elif node["type"] == "dir" and args.recursive:
                fetch(node["url"], args)
            else:
                pass
    else:
        # if the link for single file
        filename = response["name"]
        if os.path.isfile(filename) and not args.force:
            if input("Overwrite exist file `{}` [y/n] :  ".format(filename)).lower() in ["yes", "y"]:
                download(response["download_url"], args)
            else:
                exit(0)
        else:
            download(response["download_url"], args)

def github(target, args):
    fetch(to_api(target), args)
    print("{} raw file collected.".format(Target.files))

