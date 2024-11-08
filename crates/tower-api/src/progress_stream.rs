use std::{pin::Pin, task::{Context, Poll}};
use futures_util::stream::Stream;
use std::sync::{Arc, Mutex};

use crate::TowerError;

pub struct ProgressStream<R> {
    inner: R,
    progress: Arc<Mutex<u64>>,
    total_size: u64,
}

impl<R> ProgressStream<R> {
    pub async fn new(inner: R, total_size: u64) -> Result<Self, TowerError> {
        Ok(Self {
            inner,
            progress: Arc::new(Mutex::new(0)),
            total_size,
        })
    }
}

impl<R: Stream<Item = Result<bytes::Bytes, std::io::Error>> + Unpin> Stream for ProgressStream<R> {
    type Item = Result<bytes::Bytes, std::io::Error>;

    fn poll_next(mut self: Pin<&mut Self>, cx: &mut Context<'_>) -> Poll<Option<Self::Item>> {
        match Pin::new(&mut self.inner).poll_next(cx) {
            Poll::Ready(Some(Ok(chunk))) => {
                let chunk_size = chunk.len() as u64;
                let mut progress = self.progress.lock().unwrap();
                *progress += chunk_size;

                // Print progress percentage
                println!("Progress: {:.2}%", (*progress as f64 / self.total_size as f64) * 100.0);

                Poll::Ready(Some(Ok(chunk)))
            }
            other => other,
        }
    }
}
