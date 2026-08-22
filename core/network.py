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
