use futures_util::stream::Stream;
use std::sync::{Arc, Mutex};
use std::{
    pin::Pin,
    task::{Context, Poll},
};

pub struct ProgressStream<R> {
    inner: R,
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
        Ok(Self {
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

                Poll::Ready(Some(Ok(chunk)))
            }
            other => other,
        }
    }
}
