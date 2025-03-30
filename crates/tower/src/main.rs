use tower_cmd::App;

#[tokio::main]
async fn main() {
    App::new().run().await;
}
