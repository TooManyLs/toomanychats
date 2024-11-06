from datetime import UTC, datetime, timezone, timedelta
import os
from pathlib import Path

from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.backends import default_backend

from gui.widgets.utils.tools import SERVER_DIR

def generate_cert():
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )

    subject = issuer = x509.Name([
        x509.NameAttribute(NameOID.COMMON_NAME, u"toomanychats"),
    ])
    cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(private_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime.now(timezone.utc))
        .not_valid_after(datetime.now(timezone.utc) + timedelta(days=365))
        .sign(private_key, hashes.SHA256())
    )
    ssl_dir = Path(f"{SERVER_DIR}/ssl")
    ssl_dir.mkdir(parents=True, exist_ok=True)

    with open(f"{ssl_dir}/private_key.pem", "wb") as f:
        f.write(private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption(),
        ))

    with open(f"{ssl_dir}/cert.pem", "wb") as f:
        f.write(cert.public_bytes(serialization.Encoding.PEM))

def check_cert(path: str) -> bool:
    if not os.path.exists(path):
        print("Certificate file does not exist")
        return False

    try:
        with open(path, "rb") as cf:
            cert_data = cf.read()
            cert = x509.load_pem_x509_certificate(cert_data, default_backend())

        expiration_date = cert.not_valid_after_utc
        if expiration_date < datetime.now().astimezone(UTC):
            print("Certificate expired")
            return False
    except Exception as e:
        print("An error occurred during certificate validity check")
        print(repr(e))
        return False

    return True
