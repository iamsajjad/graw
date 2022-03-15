use clap::{App, Arg};

pub fn matches() -> clap::ArgMatches {
    return App::new("graw")
        .version("v0.1.0")
        .author("Sajjad alDalwachee. <sajjad.aldalwachee@gmail.com> ")
        .about("Clone raw file or subdirectory from Github repositories ")
        .arg(
            Arg::with_name("file")
                .short('f')
                .long("file")
                .value_name("URL")
                .help("Clone single raw file ")
                .takes_value(true),
        )
        .arg(
            Arg::with_name("dir")
                .short('d')
                .long("dir")
                .value_name("URL")
                .help("Clone subdirectory content ")
                .takes_value(true),
        )
        .arg(
            Arg::with_name("req")
                .short('r')
                .long("requests")
                .value_name("NUMBER")
                .help("Number of concourent requests at atime ")
                .takes_value(true),
        )
        .get_matches();
}
