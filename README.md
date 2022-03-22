<h1 align="center">
  Graw
</h1>

<p align="center">CLI tool to download only files or directories that you need from <b>github</b> or <b>gitlab</b></br>without need to clone the git repository</p>

## ⚡️ Quick start

First, [download](https://www.python.org/downloads/) and install **Python**. Version `3.7` or higher is required.

Installation is done by using the `pip install`

```bash
pip install graw
```
### How to Use graw ?

- `graw https://LINK-FOR-GITHUB-OR-GITLAB-FILE` — to download one file from github repository
- `graw https://LINK-FOR-GITHUB-OR-GITLAB-DIRECTORY` — to download one directory from github repository
- `graw -f https://LINK-FOR-GITHUB-OR-GITLAB` — to download and overwrite exists content
- `graw -r https://LINK-FOR-GITHUB-OR-GITLAB-DIRECTORY` — to download directory recursive [ all nested files ]
- `graw https://LINK-FOR-GITHUB-OR-GITLAB-DIRECTORY -t TYPE1 TYPE2 ... ` — to download only files match extension types like `-t py`

## ⭐️ Project assistance

If you want to say **thank you** or/and support active development of `graw`:

- Add a [GitHub Star](https://github.com/iamsajjad/graw) to the project.
- Write interesting articles about project on [Dev.to](https://dev.to/), [Medium](https://medium.com/) or personal blog.
- Join development by creating **Pull Request**

Together, we can make this project **better** every day! 😘

## ⚠️ License

`Graw` is free and open-source software licensed under the [MIT License](https://github.com/iamsajjad/graw/blob/master/LICENSE)
