import os
import base64

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from dotenv import load_dotenv

load_dotenv()


_key = os.getenv("MESSAGE_ENCRYPTION_KEY")

if not _key:
    raise RuntimeError("MESSAGE_ENCRYPTION_KEY is not configured.")

try:
    KEY = base64.urlsafe_b64decode(_key)
except Exception as exc:
    raise RuntimeError("Invalid MESSAGE_ENCRYPTION_KEY.") from exc

if len(KEY) != 32:
    raise RuntimeError("MESSAGE_ENCRYPTION_KEY must decode to 32 bytes.")


def encrypt_message(message):
    nonce = os.urandom(12)

    aesgcm = AESGCM(KEY)

    ciphertext = aesgcm.encrypt(
        nonce,
        message.encode("utf-8"),
        None
    )

    return ciphertext, nonce


def decrypt_message(ciphertext, nonce):
    aesgcm = AESGCM(KEY)

    plaintext = aesgcm.decrypt(
        nonce,
        ciphertext,
        None
    )

    return plaintext.decode("utf-8")