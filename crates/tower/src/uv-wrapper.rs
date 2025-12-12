fn main() -> std::process::ExitCode {
    unsafe { uv::main(std::env::args_os()) }
}
