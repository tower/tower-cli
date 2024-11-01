use tower_cli::App;

#[tokio::main]
async fn main() {
    App::new().run().await;
}
