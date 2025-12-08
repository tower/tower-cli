use tower_uv::Uv;

#[tokio::test]
async fn test_uv_wrapper_exists() {
    // Set the UV_WRAPPER_PATH to point to the binary built by cargo
    std::env::set_var("UV_WRAPPER_PATH", env!("CARGO_BIN_EXE_uv-wrapper"));

    // Test that the uv-wrapper binary is available and valid
    let uv = Uv::new(None, false)
        .await
        .expect("Failed to create a Uv instance");
    assert!(uv.is_valid().await);

    // Verify we can get the path
    assert!(uv.uv_path.exists(), "uv-wrapper binary should exist at {:?}", uv.uv_path);
}
