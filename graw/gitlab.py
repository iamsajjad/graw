
import os
import re
import sys
import shutil
from dataclasses import dataclass
import requests

RAW_FORMAT = "https://gitlab.com/api/v4/projects/{}%2F{}/repository/files/{}/raw?ref={}"
API_FORMAT = "https://gitlab.com/api/v4/projects/{}%2F{}/repository/tree/?path={}&ref={}&per_page=9999"
GITLAB_URL_PARTS = r"^(https://gitlab.com)/([a-zA-Z0-9-_/]*)/-/(blob|tree)/([a-zA-Z0-9-_]*)/([a-zA-Z0-9-_./]*)$"

# authorization = f'token {token}'
headers = {
    "user-agent": "graw-0.1.0",
    # "Authorization" : authorization,
}

# set recursion limit to higher number to handle large sub directory
sys.setrecursionlimit(10000)

# create session for talking to gitlab api
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

def get_filename(url):
    return url.replace("%2F", "/").split("/")[-2]

def to_blob(path):
    return RAW_FORMAT.format(API.org, API.repo, "%2F".join(path.split("/")), API.branch)

def to_tree(path):
    return API_FORMAT.format(API.org, API.repo, path, API.branch)

def to_api(url):

    url = url[:-1] if url.endswith("/") else url

    fields = re.findall(GITLAB_URL_PARTS, url)[0]

    # gitlab have concept of nested groups or subgroups
    API.org = "%2F".join(fields[1].split("/")[:-1])

    API.repo = fields[1].split("/")[-1]
    API.path = "/".join(fields[4].split("/"))
    API.branch = fields[3]
    API.node = len(fields[4].split("/")) - 1

    return API_FORMAT.format(API.org, API.repo, API.path, API.branch)

def makepath(url, force):
    fields = url.split("/")
    dirpath = "/".join(fields[9].split("%2F")[API.node:-1])

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

    # print(Target.directories)
    return "{}/".format(dirpath)

def download(url, args, type="tree"):
    filename = get_filename(url)

    if type == "tree":
        placeholder = f"{makepath(url, args.force)}{filename}"
    else:
        placeholder = filename

    print("GET : {}".format(placeholder))

    remotefile = requests.get(url, stream=True, headers=headers)
    with open(placeholder, "wb") as localfile:
        remotefile.raw.decode_content = True
        shutil.copyfileobj(remotefile.raw, localfile)

    Target.files += 1

    return filename

def fetch(point, args):

    # send request to the api
    response = requests.get(url=point).json()

    # if the link for directory
    if response != []:
        for node in response:
            if node["type"] == "blob":
                if any([node["name"].endswith(i) for i in args.types]) or args.types[0] == "*":
                    download(to_blob((node["path"])), args, type="tree")

            elif node["type"] == "tree" and args.recursive:
                fetch(to_tree(node["path"]), args)
            else:
                pass
    else:
        # if the link for single file
        filename = API.path.split("/")[-1]
        if os.path.isfile(filename) and not args.force:
            if input("Overwrite exist file `{}` [y/n] :  ".format(filename)).lower() in ["yes", "y"]:
                download(to_blob(API.path), args, type="blob")
            else:
                exit(0)
        else:
            download(to_blob(API.path), args, type="blob")

def gitlab(target, args):
    fetch(to_api(target), args)
    print("{} raw file collected.".format(Target.files))

