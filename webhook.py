import base64
import json
from datetime import datetime
import secrets
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.hashes import Hash, SHA256
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat
from cryptography.hazmat.backends import default_backend
import requests
import config


def get_public_key() -> bytes:
    """
    Retrieve the raw public key.
    
    :return: Bytes of key
    """
    key = Ed25519PrivateKey.from_private_bytes(config.WEBHOOK_KEY)
    return key.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw)


def send_newpaste(url: str) -> None:
    """
    Send a notification to the configured webhook.

    No-ops if no webhook is configured.

    :param url: URL of new paste
    :return: None
    """
    if not config.WEBHOOK_ENABLE:
        return
    key = Ed25519PrivateKey.from_private_bytes(config.WEBHOOK_KEY)
    digest = Hash(SHA256(), backend=default_backend())
    data = {"type": "newpaste",
            "url": url,
            "nonce": secrets.token_hex(),
            "date": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")}
    json_data = json.dumps(data)
    digest.update(json_data.encode("utf-8"))
    sig = base64.b64encode(key.sign(digest.finalize()))
    headers = {"Content-Type": "application/json; charset=utf-8",
               "X-Webhook-Version": "1.0.0",
               "X-Webhook-Signature": sig}
    try:
        requests.post(config.WEBHOOK_URL, json_data, headers=headers, timeout=3)
    except requests.exceptions.RequestException:
        pass
