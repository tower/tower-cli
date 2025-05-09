use snafu::prelude::*;

#[derive(Debug, Snafu)]
pub enum Error {
    #[snafu(display("invalid message"))]
    InvalidMessage,

    #[snafu(display("invalid encoding"))]
    InvalidEncoding,

    #[snafu(display("cryptography error"))]
    CryptographyError,

    #[snafu(display("base64 error"))]
    Base64Error,
}

impl From<std::string::FromUtf8Error> for Error {
    fn from(_error: std::string::FromUtf8Error) -> Self {
        Self::InvalidEncoding
    }
}

impl From<aes_gcm::Error> for Error {
    fn from(_error: aes_gcm::Error) -> Self {
        Self::CryptographyError
    }
}

impl From<rsa::Error> for Error {
    fn from(_error: rsa::Error) -> Self {
        Self::CryptographyError
    }
}

impl From<base64::DecodeError> for Error {
    fn from(_error: base64::DecodeError) -> Self {
        Self::Base64Error
    }
}
