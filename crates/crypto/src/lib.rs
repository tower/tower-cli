use aes_gcm::aead::Aead;
use aes_gcm::{Aes256Gcm, Key, KeyInit, Nonce}; // Or Aes256GcmSiv, Aes256GcmHs
use base64::prelude::*;
use rand::rngs::OsRng;
use rand::RngCore;
use rsa::{pkcs8::EncodePublicKey, traits::PublicKeyParts, Oaep, RsaPrivateKey, RsaPublicKey};
use sha2::Sha256;

mod errors;
pub use errors::Error;

/// encrypt encryptes plaintext with a randomly-generated AES-256 key and IV, then encrypts the AES
/// key with RSA-OAEP using the provided public key. The result is a non-URL-safe base64-encoded
/// string.
pub fn encrypt(key: RsaPublicKey, plaintext: String) -> Result<String, Error> {
    // Generate a random 32-byte AES key
    let mut aes_key = [0u8; 32];
    OsRng.fill_bytes(&mut aes_key);

    // Generate a random 12-byte IV
    let mut iv = [0u8; 12];
    OsRng.fill_bytes(&mut iv);

    // Create AES cipher (GCM mode)
    let aes_cipher = Aes256Gcm::new(Key::<Aes256Gcm>::from_slice(&aes_key));

    // Encrypt the message
    let nonce = Nonce::from_slice(&iv); // 12 bytes; unique per message
    let ciphertext = aes_cipher.encrypt(nonce, plaintext.as_bytes())?;

    // Encrypt the AES key with RSA-OAEP
    let padding = Oaep::new::<Sha256>();
    let encrypted_key = key.encrypt(&mut OsRng, padding, &aes_key)?;

    // Combine encrypted key + IV + ciphertext
    let mut result = Vec::new();
    result.extend_from_slice(&encrypted_key);
    result.extend_from_slice(&iv);
    result.extend_from_slice(&ciphertext);

    // Encode the result as base64
    Ok(BASE64_STANDARD.encode(&result))
}

/// decrypt uses `key` to decrypt an AES-256 key that's prepended to the ciphertext. The decrypted
/// key is then used to decrypt the suffix of `ciphertext` which contains the relevant message.
/// It's expected that the message was encrypted using OAEP padding and SHA256 digest.
pub fn decrypt(key: RsaPrivateKey, ciphertext: String) -> Result<String, Error> {
    let decoded = BASE64_STANDARD.decode(ciphertext)?;

    let n = key.size();
    let (ciphered_key, suffix) = decoded.split_at(n);

    let key = key.decrypt(Oaep::new::<Sha256>(), ciphered_key)?;

    let aes_key = Key::<Aes256Gcm>::from_slice(&key);
    let cipher = Aes256Gcm::new(aes_key);

    // Check if the suffix is at least 12 bytes (96 bits) for the IV
    if suffix.len() < 12 {
        return Err(Error::InvalidMessage);
    }

    let (iv, ciphertext) = suffix.split_at(12);
    let nonce = Nonce::from_slice(iv);

    let plaintext = cipher.decrypt(nonce, ciphertext)?;
    Ok(String::from_utf8(plaintext)?)
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
    key.to_public_key_pem(rsa::pkcs8::LineEnding::LF).unwrap()
}

#[cfg(test)]
mod test {
    use super::*;
    use rand::{distributions::Alphanumeric, Rng};
    use rsa::pkcs8::DecodePublicKey;

    #[test]
    fn test_encrypt_decrypt() {
        let (private_key, public_key) = testutils::crypto::get_test_keys();

        let plaintext = "Hello, World!".to_string();
        let ciphertext = encrypt(public_key, plaintext.clone()).unwrap();
        let decrypted = decrypt(private_key, ciphertext).unwrap();

        assert_eq!(plaintext, decrypted);
    }

    #[test]
    fn test_encrypt_decrypt_long_messages() {
        let (private_key, public_key) = testutils::crypto::get_test_keys();

        let plaintext: String = rand::thread_rng()
            .sample_iter(&Alphanumeric)
            .take(5_000)
            .map(char::from)
            .collect();

        let ciphertext = encrypt(public_key, plaintext.clone()).unwrap();
        let decrypted = decrypt(private_key, ciphertext).unwrap();

        assert_eq!(plaintext, decrypted);
    }

    #[test]
    fn test_serialize_public_key() {
        let (_private_key, public_key) = testutils::crypto::get_test_keys();
        let serialized = serialize_public_key(public_key.clone());
        let deserialized = RsaPublicKey::from_public_key_pem(&serialized).unwrap();

        assert_eq!(public_key, deserialized);
    }
}
