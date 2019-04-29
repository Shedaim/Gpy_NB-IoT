import socket
import logging

log = logging.getLogger("HTTP")

TELEMETRY_PATH = '/api/v1/token/telemetry'
SUBSCRIBE_PATH = '/api/v1/token/attributes/updates'
ATTRIBUTES_PATH = '/api/v1/token/attributes'


class HTTP:

    def __init__(self):
        self.host = None
        self.port = None
        self.sock = None

    def connect(self):
        addr = socket.getaddrinfo(self.host, self.port)[0][-1]
        try:
            self.sock = socket.socket()
            self.sock.connect(addr)
        except OSError:
            log.exception("Could not connect socket to " + str(self.host))
            return False

    def disconnect(self):
        self.sock.close()

    def http_to_packet(self, _type, path, content_type, message):
        if self.host is None or self.port is None or path is None:
            log.error('Tried to build an HTTP packet without all the required data.')
            return ''
        lines = list()
        lines.append(' '.join([_type, path, "HTTP/1.1"]))
        lines.append(' '.join(["Host:", "{0}:{1}".format(self.host, str(self.port))]))
        lines.append('Accept: */*')
        if content_type is not None:
            lines.append(' '.join(["Content-Type:", str(content_type)]))
        if message is not None:
            lines.append(' '.join(["Content-Length:", str(len(message))]))
            lines.append(str(message))
        return '\r\n'.join(lines)

    # Send a message to a remote HTTP server and recieve the answer
    def send_message(self, packet):
        self.connect()
        log.info('Sending HTTP message to address: {0}:{1}'.format(self.host, self.port))
        try:
            self.sock.send(bytes(packet, 'utf8'))
        except OSError:
            log.exception("Could not send message over HTTP socket to " + str(self.host))
            self.disconnect()
            return False
        log.info('Sent HTTP POST request to {0} on port {1}'.format(self.host, self.port))
        self.disconnect()
        return True
