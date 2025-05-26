use log::kv::{Key, Value};

pub struct RunContext {
    run_id: String,
}

impl log::kv::ToValue for RunContext {
    fn to_value(&self) -> Value {
        Value::from(self.run_id.as_str())
    }
}

impl log::kv::ToKey for RunContext {
    fn to_key(&self) -> Key {
        Key::from("tower.run_id")
    }
}

impl RunContext {
    pub fn new(run_id: String) -> Self {
        Self { run_id }
    }
}
