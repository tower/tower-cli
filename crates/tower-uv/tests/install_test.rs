use tower_uv::{install::get_default_uv_bin_dir, Uv};

#[tokio::test]
async fn test_installing_uv() {
    // Ensure there is no `uv` in the directory that we will install it to by default.
    let default_uv_bin_dir = get_default_uv_bin_dir().unwrap();
    let _ = tokio::fs::remove_dir_all(&default_uv_bin_dir).await;

    // Now if we instantiate a Uv instance, it should install the `uv` binary.
    let uv = Uv::new().await.expect("Failed to create a Uv instance");
    assert!(uv.is_valid().await);
}
