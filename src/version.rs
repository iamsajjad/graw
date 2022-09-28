// project informations

pub const NAME: &str = "graw";
pub const VERSION: u8 = 0;
pub const PATCHLEVEL: u8 = 1;
pub const SUBLEVEL: u8 = 0;

pub fn version() -> String {
    format!("v{}.{}.{}", VERSION, PATCHLEVEL, SUBLEVEL)
}

pub fn project() -> String {
    format!("{} v{}.{}.{}", NAME, VERSION, PATCHLEVEL, SUBLEVEL)
}
