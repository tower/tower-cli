use serde::Deserialize;
use tower_package_core::{build_package, Entry, PackageInputs, Parameter};
use wasm_bindgen::prelude::*;

#[derive(Deserialize)]
#[serde(rename_all = "camelCase")]
struct JsEntry {
    archive_name: String,
    bytes: serde_bytes::ByteBuf,
}

impl From<JsEntry> for Entry {
    fn from(e: JsEntry) -> Self {
        Entry {
            archive_name: e.archive_name,
            bytes: e.bytes.into_vec(),
        }
    }
}

#[derive(Deserialize)]
#[serde(rename_all = "camelCase")]
struct JsInputs {
    app_files: Vec<JsEntry>,
    module_files: Vec<JsEntry>,
    towerfile_bytes: serde_bytes::ByteBuf,
    invoke: String,
    parameters: Vec<Parameter>,
    schedule: Option<String>,
    import_paths: Vec<String>,
}

/// Build a Tower app bundle from in-memory file contents.
///
/// Input shape (camelCase):
///   {
///     appFiles: [{ archiveName: string, bytes: Uint8Array }, ...],
///     moduleFiles: [{ archiveName: string, bytes: Uint8Array }, ...],
///     towerfileBytes: Uint8Array,
///     invoke: string,
///     parameters: [{ name, description?, default, hidden }, ...],
///     schedule?: string,
///     importPaths: string[]
///   }
///
/// Returns the gzipped tar archive as a Uint8Array, byte-identical across
/// runs for the same inputs.
#[wasm_bindgen(js_name = buildBundle)]
pub fn build_bundle(inputs: JsValue) -> Result<Vec<u8>, JsError> {
    let js: JsInputs = serde_wasm_bindgen::from_value(inputs)
        .map_err(|e| JsError::new(&format!("invalid inputs: {}", e)))?;

    let core_inputs = PackageInputs {
        app_files: js.app_files.into_iter().map(Entry::from).collect(),
        module_files: js.module_files.into_iter().map(Entry::from).collect(),
        towerfile_bytes: js.towerfile_bytes.into_vec(),
        invoke: js.invoke,
        parameters: js.parameters,
        schedule: js.schedule,
        import_paths: js.import_paths,
    };

    let built = build_package(core_inputs)
        .map_err(|e| JsError::new(&format!("build failed: {}", e)))?;
    Ok(built.bytes)
}
