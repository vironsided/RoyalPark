from __future__ import annotations

import base64
import hashlib
import secrets
from datetime import datetime, timezone
from decimal import Decimal
from typing import Iterable

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPrivateKey, RSAPublicKey
from cryptography.hazmat.primitives.serialization import load_pem_private_key, load_pem_public_key

from ..config import settings


CREATE_SIGN_FIELDS = ["AMOUNT", "CURRENCY", "TERMINAL", "TRTYPE", "TIMESTAMP", "NONCE", "BACKREF"]
CALLBACK_SIGN_FIELDS = ["AMOUNT", "CURRENCY", "TERMINAL", "TRTYPE", "ORDER", "RRN", "INT_REF"]


def _as_pem(raw: str, key_kind: str) -> str:
    value = (raw or "").strip().replace("\\n", "\n")
    if not value:
        return value
    if "BEGIN" in value:
        return value
    clean = "".join(value.split())
    if key_kind == "private":
        return (
            "-----BEGIN PRIVATE KEY-----\n"
            f"{clean}\n"
            "-----END PRIVATE KEY-----"
        )
    return (
        "-----BEGIN PUBLIC KEY-----\n"
        f"{clean}\n"
        "-----END PUBLIC KEY-----"
    )


def _private_key() -> RSAPrivateKey:
    key_pem = _as_pem(settings.AZERICARD_PRIVATE_KEY, "private").encode("utf-8")
    return load_pem_private_key(key_pem, password=None)


def _public_key() -> RSAPublicKey:
    key_pem = _as_pem(settings.AZERICARD_PUBLIC_KEY, "public").encode("utf-8")
    return load_pem_public_key(key_pem)


def build_signature_content(data: dict, fields: Iterable[str]) -> str:
    # AzeriCard P_SIGN is generated from ordered field values.
    return ";".join(str(data.get(name, "") or "") for name in fields)


def generate_p_sign(data: dict, fields: Iterable[str]) -> str:
    content = build_signature_content(data, fields).encode("utf-8")
    signature = _private_key().sign(content, padding.PKCS1v15(), hashes.SHA256())
    return base64.b64encode(signature).decode("ascii")


def verify_callback_signature(data: dict, signature_field: str = "P_SIGN") -> bool:
    signature_b64 = str(data.get(signature_field, "") or "").strip()
    if not signature_b64:
        return False
    try:
        signature = base64.b64decode(signature_b64)
        content = build_signature_content(data, CALLBACK_SIGN_FIELDS).encode("utf-8")
        _public_key().verify(signature, content, padding.PKCS1v15(), hashes.SHA256())
        return True
    except Exception:
        return False


def build_order_id(terminal_id: str | None = None) -> str:
    tid = "".join(ch for ch in str(terminal_id or settings.AZERICARD_TERMINAL_ID or "") if ch.isdigit())
    date_part = datetime.now(timezone.utc).strftime("%y%m%d")
    rnd = secrets.token_hex(5)
    rnd_digits = "".join(str(int(ch, 16) % 10) for ch in rnd)
    order = f"{tid[:6]}{date_part}{rnd_digits}"
    order = "".join(ch for ch in order if ch.isdigit())
    if len(order) < 6:
        order = (order + "0" * 6)[:6]
    if len(order) > 32:
        order = order[:32]
    return order


def amount_to_gateway(amount: Decimal | float | int | str) -> str:
    val = Decimal(str(amount or "0")).quantize(Decimal("0.01"))
    return format(val, "f")


def build_timestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")


def build_nonce() -> str:
    return hashlib.md5(secrets.token_bytes(24)).hexdigest()[:16]
