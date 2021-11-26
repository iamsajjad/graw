
import re
import argparse

from .github import github
from .gitlab import gitlab

parser = argparse.ArgumentParser(description="graw simple way to download raw subdirectory or file from \
                                              github and gitlab repository.")
parser.add_argument("--force", "-f", action="store_true", help="force overwrite exist content")
parser.add_argument("--recursive", "-r", action="store_true", help="clone subdirectory recursively")
parser.add_argument("target", help="github.com or gitlab.con file or subdirectory link", type=str)
parser.add_argument("--types", "-t", nargs="+", default="*", help="clone only files with matched types")

args = parser.parse_args()

TARGET = args.target

GITHUB_NODE = r"^((?:https://)github.com)/[a-zA-Z0-9-_]*/[a-zA-Z0-9-_.]*/(blob|tree)/[a-zA-Z0-9-_.]*/(.*?).$"
GITHUB_REPOSITORY = r"^((?:https://)github.com)/[a-zA-Z0-9-_]*/[a-zA-Z0-9-_.]*(.git)?$"

GITLAB_NODE = r"^((?:https://)gitlab.com)/[a-zA-Z0-9-_/]*/-/(blob|tree)/[a-zA-Z0-9-_]*/[a-zA-Z0-9-_./]*$"
GITLAB_REPOSITORY = r"^((?:https://)gitlab.com)/([a-zA-Z0-9-_/]*)(.git)?$"

def is_github_node(url):
    # check if the link is (file or directory) in github repository link
    regex = re.compile(GITHUB_NODE, re.IGNORECASE)
    return url is not None and bool(regex.search(url))

def is_github_repository(url):
    # check if the link is for github repository
    regex = re.compile(GITHUB_REPOSITORY, re.IGNORECASE)
    return url is None or bool(regex.search(url))

def is_gitlab_node(url):
    regex = re.compile(GITLAB_NODE, re.IGNORECASE)
    return url is not None and bool(regex.search(url))

def is_gitlab_repository(url):
    regex = re.compile(GITLAB_REPOSITORY, re.IGNORECASE)
    return url is None or bool(regex.search(url))

def run():
    try:
        if is_github_node(TARGET):
            github(TARGET, args)
        elif is_gitlab_node(TARGET):
            gitlab(TARGET, args)
        else:
            if is_github_repository(TARGET) or is_gitlab_repository(TARGET):
                print("Use `git clone --depth=1 {}".format(TARGET))
            else:
                print("Please enter a valid github or gitlab file or directory url")
    except KeyboardInterrupt:
        exit(0)

if __name__ == "__main__":
    run()

