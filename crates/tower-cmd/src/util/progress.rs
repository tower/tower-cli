use futures_util::stream::Stream;
use std::sync::{Arc, Mutex};
use std::{
    pin::Pin,
    task::{Context, Poll},
};

use std::fs::File;
use std::io::Write;

pub struct ProgressStream<R> {
    inner: R,
    file: Arc<Mutex<File>>,
    progress: Arc<Mutex<u64>>,
    progress_cb: Box<dyn Fn(u64, u64) + Send + Sync>,
    total_size: u64,
}

impl<R> ProgressStream<R> {
    pub async fn new(
        inner: R,
        total_size: u64,
        progress_cb: Box<dyn Fn(u64, u64) + Send + Sync>,
    ) -> Result<Self, std::io::Error> {
        let file = File::create("/tmp/input.dat").expect("Failed to create file");

        Ok(Self {
            file: Arc::new(Mutex::new(file)),
            inner,
            progress_cb,
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
                (self.progress_cb)(*progress, self.total_size);

                let mut file = self.file.lock().expect("Lock couldn't be acquired");
                file.write(&chunk).expect("Failed to write to file");

                Poll::Ready(Some(Ok(chunk)))
            }
            other => other,
        }
    }
}
