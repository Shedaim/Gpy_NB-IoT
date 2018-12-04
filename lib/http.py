import socket
import machine
import lib.logging as logging

log = logging.getLogger("HTTP")

TELEMETRY_PATH = '/api/v1/token/telemetry'
SUBSCRIBE_PATH_HTTP = '/api/v1/token/attributes/updates'
ATTRIBUTES_PATH = '/api/v1/token/attributes'
REQUEST_ATTR_PATH = '/api/v1/token/attributes'

class HTTP():

    def __init__(self):
        self.host = None
        self.port = None

    def open_socket(self):
        addr = socket.getaddrinfo(self.host, self.port)[0][-1]
        try:
            self.s = socket.socket()
            self.s.connect(addr)
        except OSError as e:
            log.exception("Could not connect socket to " + str(self.host))
            return False

    def http_to_packet(self, type, path, content_type, message):
        if self.host is None or self.port is None or path is None:
            return False
        packet = ''
        packet += type + ' ' + path + " HTTP/1.1" + '\r\n'
        packet += "Host: " + self.host + ':' + str(self.port) + '\r\n'
        packet += 'Accept: */*' + '\r\n'
        if content_type is not None:
            packet += "Content-Type:" + str(content_type) + '\r\n'
        if message is not None:
            packet += "Content-Length: " + str(len(message)) + '\r\n\r\n'
            packet += str(message) + '\r\n'
        return packet

    # Send a message to a remote HTTP server and recieve the answer
    def send_message(self, packet):
        self.open_socket()
        log.info('Sending HTTP message to address: {0}:{1}'.format(self.host, self.port))
        try:
            self.s.send(bytes(packet, 'utf8'))
        except OSError as e:
            log.exception("Could not send message over HTTP socket to " + str(self.host))
            self.s.close()
            return False
        log.info('Sent HTTP POST request to {0} on port {1}'.format(self.host, self.port))
        self.s.close()
        return True

# Listens on a specific port for HTTP messages and returns a simple "page"
def listen_http(port):
    html = "<!DOCTYPE html>"
    addr = socket.getaddrinfo('0.0.0.0', port)[0][-1]
    s = socket.socket()
    s.bind(addr)
    s.listen(1)
    print('listening on', addr)
    log.info('listening on %s', addr)
    try:
        while True:
            cl, addr = s.accept()
            log.info('client connected from %s', addr)
            cl.send(html)
            cl.close()
    except:
        cl.close()
