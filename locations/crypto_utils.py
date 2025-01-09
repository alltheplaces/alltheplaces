from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.padding import PKCS7


def decrypt_aes256cbc_pkcs7(ciphertext: bytes, key: str, iv: str) -> bytes:
    """
    Decrypt data that is encrypted with cipher AES256 used in CBC mode with
    PKCS7 padding.
    :param ciphertext: encrypted data as a bytes array
    :param key: hex encoded key matching regular expression ^[0-9a-f]{64}$
    :param iv: hex encoded initialization vector matching regular expression
               ^[0-9a-f]{32}$
    :return: decrypted data (plaintext) as a bytes array
    """
    cipher = Cipher(algorithms.AES256(key=bytes.fromhex(key)), modes.CBC(initialization_vector=bytes.fromhex(iv)))
    decryptor = cipher.decryptor()
    padded_plaintext = decryptor.update(ciphertext) + decryptor.finalize()
    unpadder = PKCS7(block_size=128).unpadder()
    unpadded_plaintext = unpadder.update(padded_plaintext) + unpadder.finalize()
    return unpadded_plaintext
