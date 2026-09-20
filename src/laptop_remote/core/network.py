import socket

def get_local_ip():
    def _usable(ip):
        if not ip:
            return False
        if ip.startswith(('127.', '169.254.', '0.', '255.')):
            return False
        return True

    for target in ('8.8.8.8', '10.255.255.255'):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect((target, 1))
            ip = s.getsockname()[0]
            if _usable(ip):
                return ip
        except Exception:
            pass
        finally:
            s.close()
            
    try:
        for info in socket.getaddrinfo(socket.gethostname(), None,
                                       socket.AF_INET, socket.SOCK_DGRAM):
            ip = info[4][0]
            if _usable(ip):
                return ip
    except Exception:
        pass
    return '127.0.0.1'

def get_cert_paths():
    """Get persistent paths for auto-generated SSL certificates."""
    import os
    from .config import get_executable_dir
    cert_dir = os.path.join(get_executable_dir(), '.certs')
    os.makedirs(cert_dir, exist_ok=True)
    return os.path.join(cert_dir, 'cert.pem'), os.path.join(cert_dir, 'key.pem')

def setup_ssl_context(cert_file=None, key_file=None):
    """
    Returns (cert_file, key_file) or 'adhoc' for Flask/SocketIO SSL context.
    Automatically generates a self-signed certificate if none are provided.
    """
    import os
    import shutil
    import subprocess

    if cert_file and key_file and os.path.exists(cert_file) and os.path.exists(key_file):
        return cert_file, key_file

    cert_path, key_path = get_cert_paths()
    if os.path.exists(cert_path) and os.path.exists(key_path):
        return cert_path, key_path

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
        except Exception:
            pass

    # Try cryptography library if installed
    try:
        from cryptography import x509
        from cryptography.x509.oid import NameOID
        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.primitives.asymmetric import rsa
        from cryptography.hazmat.primitives import serialization
        import datetime

        key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, 'remotedeck.local')])
        now = datetime.datetime.now(datetime.timezone.utc)
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
        with open(key_path, 'wb') as f:
            f.write(key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.TraditionalOpenSSL,
                encryption_algorithm=serialization.NoEncryption()
            ))
        with open(cert_path, 'wb') as f:
            f.write(cert.public_bytes(serialization.Encoding.PEM))
        return cert_path, key_path
    except Exception:
        pass

    # Fallback to adhoc
    return 'adhoc'
