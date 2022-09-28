use std::error::Error;
use std::fs;
use std::io::{self, Write};

use futures::StreamExt;
use regex::Regex;
use reqwest::{self, header::ACCEPT, header::USER_AGENT};
use serde::Deserialize;

pub mod cli;
pub mod version;

#[derive(Debug)]
struct Target {
    org: String,
    repo: String,
    path: String,
    branch: String,
    node: usize,
}

#[derive(Deserialize, Debug)]
struct Node {
    path: String,
    r#type: String,
}

#[derive(Deserialize, Debug)]
struct Tree {
    tree: Vec<Node>,
}

#[derive(Deserialize, Debug)]
struct Root {
    sha: String,
}

#[allow(unreachable_code)]
#[allow(clippy::print_literal)]
async fn url_validation(url: &str) {
    let is_node = Regex::new(
        r"https://github.com/[a-zA-Z0-9-_]*/[a-zA-Z0-9-_.]*/(blob)|(tree)/[a-zA-Z0-9-_.]*/(.*?).$",
    )
    .unwrap();
    let is_repo = Regex::new(
        r"https://github.com/([a-zA-Z0-9-_]*)/([a-zA-Z0-9-_.]*)(/tree/([a-zA-Z0-9-_]*))?/?$",
    )
    .unwrap();

    if !is_node.is_match(url) {
        if !is_repo.is_match(url) {
            // not github url
            println!("URL you've provide isn't a valid GitHub file or subdirectory URL.");
        } else {
            // url for github repository
            let caps = is_repo.captures(url).unwrap();

            let source: String = format!(
                "https://github.com/{}/{}.git",
                caps.get(1).map_or("username", |m| m.as_str()),
                caps.get(2).map_or("repository", |m| m.as_str())
            );

            println!(
                "{}\n{}\n{}",
                "You trying to clone all files in the repository use `git clone`",
                "to clone files and changes history or to get only repository",
                "files use `git clone --depth=1` like :"
            );
            println!("    `git clone --depth=1 {}", source);
        }
        std::process::exit(0);
    }
}

async fn get_target(mut url: String) -> Target {
    if url.ends_with('/') {
        url = url[..url.len() - 1].to_string()
    }

    let fields: Vec<&str> = url.split('/').collect();

    let link: Target = Target {
        org: (fields[3]).to_string(),
        repo: (fields[4]).to_string(),
        path: (fields[7..]).join("/"),
        branch: (fields[6]).to_string(),
        node: fields.len() - 2,
    };

    link
}

async fn get_raw_file(target: Target) -> Result<Vec<String>, Box<dyn Error>> {
    let raw_file_link: String = format!(
        "https://raw.githubusercontent.com/{}/{}/{}/{}",
        target.org, target.repo, target.branch, target.path
    );

    // let _ = download(&raw_file_link, "".to_string()).await;
    Ok(vec![raw_file_link])
}
async fn get_raw_tree(target: Target) -> Result<Vec<String>, Box<dyn Error>> {
    let client = reqwest::Client::new();

    let mut files_links: Vec<String> = Vec::new();
    let tree_api = format!(
        "https://api.github.com/repos/{}/{}/git/trees/{}:{}?recursive=true",
        &target.org, &target.repo, &target.branch, &target.path
    );

    let root: Root = client
        .get(tree_api)
        .header(ACCEPT, "application/vnd.github.v3+json")
        .header(USER_AGENT, version::project())
        .send()
        .await?
        .json::<Root>()
        .await?;

    let treeslink = format!(
        "https://api.github.com/repos/{}/{}/git/trees/{}?recursive=true",
        &target.org, &target.repo, &root.sha
    );

    println!("Fetching files under `{}` directory", &target.path);
    let treedata: Tree = client
        .get(treeslink)
        .header(ACCEPT, "application/vnd.github.v3+json")
        .header(USER_AGENT, version::project())
        .send()
        .await?
        .json::<Tree>()
        .await?;

    let mut files: u64 = 0;

    for node in treedata.tree {
        if &node.r#type == "blob" {
            files_links.push(format!(
                "https://raw.githubusercontent.com/{}/{}/{}/{}/{}",
                target.org, target.repo, target.branch, target.path, node.path
            ));
            files += 1;
        }
    }

    println!("{} file to download", files);
    Ok(files_links)
}

async fn create_local_path(url: &str, start: usize, first: bool) -> String {
    let fields: Vec<&str> = url.split('/').collect();

    // last directory before file
    let end: usize = &fields.len() - 1;

    let dirpath: String = (fields[start..end]).join("/");

    // target is single file
    if dirpath.is_empty() {
        return dirpath;
    }

    // target is directory
    let node: String = vec![&dirpath.split('/').next().unwrap()][0].to_string();

    if first && fs::metadata(&node).is_ok() {
        let mut overwrite = String::new();

        print!("Overwrite exist directory `{}` [y/n] : ", &node);
        let _ = io::stdout().flush();
        let _ = io::stdin().read_line(&mut overwrite);

        match &overwrite[..] {
            "y\n" => fs::remove_dir_all(&node).unwrap(),
            _ => std::process::exit(0),
        }
    }

    fs::create_dir_all(&dirpath)
        .unwrap_or_else(|_| panic!("Failed to create file path {}", &dirpath));
    format!("{}/", dirpath)
}

async fn download(url: &str, directory: String) -> Result<(), Box<dyn Error>> {
    let client = reqwest::Client::new();
    let response: reqwest::Response = client
        .get(url)
        .header(ACCEPT, "application/vnd.github.v3+raw")
        .header(USER_AGENT, version::project())
        .send()
        .await
        .expect("----******----");

    let mut dest = {
        let filename = response
            .url()
            .path_segments()
            .and_then(|segments| segments.last())
            .and_then(|name| if name.is_empty() { None } else { Some(name) })
            .unwrap_or("tmp.bin");

        let placeholder: String = format!("{}{}", directory, filename);
        println!("    GET : {}", &placeholder);

        fs::File::create(placeholder)?
    };

    let content = response.text().await?;
    io::copy(&mut content.as_bytes(), &mut dest)?;
    Ok(())
}

#[tokio::main]
async fn main() {
    let user_args = cli::matches();

    let mut args: Vec<(String, String)> = Vec::new();
    if let Some(f) = user_args.value_of("file") {
        args.push(("file".to_string(), f.to_string()));
    }

    if let Some(d) = user_args.value_of("dir") {
        args.push(("dir".to_string(), d.to_string()));
    }

    for arg in args {
        url_validation(&arg.1).await;
        let target: Target = get_target(arg.1).await;
        let start = target.node;

        let mut files_links: Vec<String> = vec![];

        if arg.0 == "file" {
            files_links = match get_raw_file(target).await {
                Ok(v) => v,
                Err(e) => panic!("{:?}", e),
            };
        } else if arg.0 == "dir" {
            files_links = match get_raw_tree(target).await {
                Ok(v) => v,
                Err(e) => panic!("{:?}", e),
            };
        }

        let first: bool = false;
        // let mut tasks: Vec<JoinHandle<Result<(), ()>>> = vec![];

        let fetches = futures::stream::iter(files_links.into_iter().map(|file_link| async move {
            let directory: String = create_local_path(&file_link, start, first).await;
            download(&file_link, directory)
                .await
                .expect("Problem while downloading");
        }))
        .buffer_unordered(60)
        .collect::<Vec<()>>();
        fetches.await;

        // first = false;
    }
}
