"""Network interface discovery, IP resolution, and SSL context generation."""

import contextlib
import datetime
import importlib.util
import os
import shutil
import socket
import stat
import subprocess

from .config import get_executable_dir, get_user_data_dir
from .logger import logger


def get_local_ip():
    """Resolve the host machine's primary local area network (LAN) IPv4 address."""
    def _usable(ip):
        if not ip:
            return False
        return not ip.startswith(('127.', '169.254.', '0.', '255.'))

    # 1) Try enumerating interfaces via ifaddr (reliable, no socket connects)
    with contextlib.suppress(Exception):
        import ifaddr
        for adapter in ifaddr.get_adapters():
            for ip_info in adapter.ips:
                ip = ip_info.ip
                if isinstance(ip, str) and _usable(ip):
                    return ip

    # 2) Fallback: UDP connect trick
    for target in ('8.8.8.8', '10.255.255.255'):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect((target, 1))
            ip = s.getsockname()[0]
            if _usable(ip):
                return ip
        except Exception as e:
            logger.debug(f"UDP socket connect to {target} failed: {e}")
        finally:
            s.close()

    with contextlib.suppress(Exception):
        for info in socket.getaddrinfo(socket.gethostname(), None,
                                       socket.AF_INET, socket.SOCK_DGRAM):
            ip = info[4][0]
            if _usable(ip):
                return ip

    return '127.0.0.1'


def get_cert_paths():
    """Get persistent paths for auto-generated SSL certificates."""
    try:
        exec_dir = get_executable_dir()
        proj_marker = os.path.join(exec_dir, 'pyproject.toml')
        if os.path.exists(proj_marker) and os.access(exec_dir, os.W_OK):
            cert_dir = os.path.join(exec_dir, '.certs')
        else:
            cert_dir = os.path.join(get_user_data_dir(), 'certs')
        os.makedirs(cert_dir, exist_ok=True)
    except OSError as e:
        logger.debug(f"Error preparing certificate directory: {e}")
        cert_dir = os.path.join(get_user_data_dir(), 'certs')
        with contextlib.suppress(OSError):
            os.makedirs(cert_dir, exist_ok=True)
    return os.path.join(cert_dir, 'cert.pem'), os.path.join(cert_dir, 'key.pem')


def setup_ssl_context(cert_file=None, key_file=None):
    """
    Returns (cert_file, key_file) or 'adhoc' for Flask/SocketIO SSL context.
    Automatically generates a self-signed certificate if none are provided.
    """
    if cert_file and key_file:
        try:
            if os.path.exists(cert_file) and os.path.exists(key_file):
                return cert_file, key_file
        except OSError:
            pass

    cert_path, key_path = get_cert_paths()
    try:
        if os.path.exists(cert_path) and os.path.exists(key_path):
            return cert_path, key_path
    except OSError:
        pass

    # Try generating with openssl CLI if available
    if shutil.which('openssl'):
        try:
            cmd = [
                'openssl', 'req', '-x509', '-newkey', 'rsa:2048',
                '-nodes', '-keyout', key_path, '-out', cert_path,
                '-days', '365', '-subj', '/CN=remotedeck.local'
            ]
            subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
            if os.path.exists(cert_path) and os.path.exists(key_path):
                return cert_path, key_path
        except Exception as e:
            logger.debug(f"OpenSSL generation failed: {e}")

    # Try cryptography library if installed
    try:
        from cryptography import x509
        from cryptography.hazmat.primitives import hashes, serialization
        from cryptography.hazmat.primitives.asymmetric import rsa
        from cryptography.x509.oid import NameOID

        key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, 'remotedeck.local')])
        now = datetime.datetime.now(datetime.UTC)
        cert = (
            x509.CertificateBuilder()
            .subject_name(name)
            .issuer_name(name)
            .public_key(key.public_key())
            .serial_number(x509.random_serial_number())
            .not_valid_before(now)
            .not_valid_after(now + datetime.timedelta(days=365))
            .sign(key, hashes.SHA256())
        )
        fd = os.open(key_path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, stat.S_IRUSR | stat.S_IWUSR)
        with open(fd, 'wb') as f:
            f.write(key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.TraditionalOpenSSL,
                encryption_algorithm=serialization.NoEncryption()
            ))
        with open(cert_path, 'wb') as f:
            f.write(cert.public_bytes(serialization.Encoding.PEM))
        return cert_path, key_path
    except Exception as e:
        logger.debug(f"cryptography certificate generation failed: {e}")

    # Fallback to adhoc only if pyOpenSSL is present
    if importlib.util.find_spec('OpenSSL') is not None:
        return 'adhoc'

    raise RuntimeError(
        "SSL certificate setup failed: unable to generate self-signed certificates. "
        "Please install OpenSSL ('sudo apt install openssl') or "
        "cryptography ('pip install cryptography') to enable --ssl."
    )
