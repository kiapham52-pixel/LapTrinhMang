import json
import socket


HEADER_LEN = 4


def _recv_exact(sock, length):
    chunks = bytearray()
    while len(chunks) < length:
        try:
            chunk = sock.recv(length - len(chunks))
        except socket.timeout:
            return None
        if not chunk:
            return None
        chunks.extend(chunk)
    return bytes(chunks)


def send_json(sock, payload):
    try:
        message = json.dumps(payload, ensure_ascii=False).encode('utf-8')
        length = len(message).to_bytes(HEADER_LEN, byteorder='big')
        sock.sendall(length + message)
    except Exception:
        raise


def recv_json(sock):
    try:
        header = _recv_exact(sock, HEADER_LEN)
        if header is None:
            return None
        length = int.from_bytes(header, byteorder='big')
        raw = _recv_exact(sock, length)
        if raw is None:
            return None
        text = raw.decode('utf-8')
        return json.loads(text)
    except json.JSONDecodeError:
        return {'status': 'error', 'message': 'Invalid JSON'}
    except socket.timeout:
        return {'status': 'error', 'message': 'Connection timed out'}
    except ConnectionResetError:
        return {'status': 'error', 'message': 'Connection reset by peer'}
