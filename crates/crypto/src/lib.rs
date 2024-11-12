use sha2::{Sha256, Digest, digest::DynDigest};
use rand::rngs::OsRng;
use base64::prelude::*;
use rsa::{
    RsaPrivateKey, RsaPublicKey, Oaep,
    traits::PublicKeyParts,
    pkcs1::EncodeRsaPublicKey,
};

/// encrypt manages the process of encrypting long messages using the RSA algorithm and OAEP
/// padding. It takes a public key and a plaintext message and returns the ciphertext.
pub fn encrypt(key: RsaPublicKey, plaintext: String) -> String {
    let mut rng = OsRng;
    let hash = Sha256::new();
    let bytes = key.n().bits() / 8;
    let step = bytes - 2*hash.output_size() - 2;
    let chunks =  plaintext.as_bytes().chunks(step);
    let mut res = vec![];

    for chunk in chunks {
        let padding = Oaep::new::<Sha256>();
        let encrypted = key.encrypt(&mut rng, padding, chunk).unwrap();
        res.extend(encrypted);
    }

    BASE64_STANDARD.encode(res)
}

/// decrypt takes a given RSA Private Key and the relevant ciphertext and decrypts it into
/// plaintext. It's expected that the message was encrypted using OAEP padding and SHA256 digest.
pub fn decrypt(key: RsaPrivateKey, ciphertext: String) -> String {
    let decoded = BASE64_STANDARD.decode(ciphertext.as_bytes()).unwrap();

    let step = key.n().bits() / 8;
    let chunks: Vec<&[u8]> = decoded.chunks(step).collect();
    let mut res = vec![];

    for (_, chunk) in chunks.iter().enumerate() {
        let padding = Oaep::new::<Sha256>();
        let decrypted = key.decrypt(padding, chunk).unwrap();
        res.extend(decrypted);
    }

    String::from_utf8(res).unwrap()
}

/// generate_key_pair creates a new 2048-bit public and private key for use in
/// encrypting/decrypting payloads destined for the Tower service.
pub fn generate_key_pair() -> (RsaPrivateKey, RsaPublicKey) {
    let bits = 2048;
    let private_key = RsaPrivateKey::new(&mut OsRng, bits).unwrap();
    let public_key = RsaPublicKey::from(&private_key);
    (private_key, public_key)
}

/// serialize_public_key takes an RSA public key and serializes it into a PEM-encoded string.
pub fn serialize_public_key(key: RsaPublicKey) -> String {
    key.to_pkcs1_pem(rsa::pkcs1::LineEnding::LF).unwrap()
}

#[cfg(test)]
mod test {
    use super::*;
    use rand::{distributions::Alphanumeric, Rng};
    use rsa::pkcs1::DecodeRsaPublicKey;

    #[test]
    fn test_encrypt_decrypt() {
        let  (private_key, public_key) = testutils::crypto::get_test_keys();

        let plaintext = "Hello, World!".to_string();
        let ciphertext = encrypt(public_key, plaintext.clone());
        let decrypted = decrypt(private_key, ciphertext);

        assert_eq!(plaintext, decrypted);
    }

    #[test]
    fn test_encrypt_decrypt_long_messages() {
        let  (private_key, public_key) = testutils::crypto::get_test_keys();

        let plaintext: String = rand::thread_rng()
            .sample_iter(&Alphanumeric)
            .take(5_000)
            .map(char::from)
            .collect();

        let ciphertext = encrypt(public_key, plaintext.clone());
        let decrypted = decrypt(private_key, ciphertext);

        assert_eq!(plaintext, decrypted);
    }

    #[test]
    fn test_serialize_public_key() {
        let  (_private_key, public_key) = testutils::crypto::get_test_keys();
        let serialized = serialize_public_key(public_key.clone());
        let deserialized = RsaPublicKey::from_pkcs1_pem(&serialized).unwrap();

        assert_eq!(public_key, deserialized);
    }
}
