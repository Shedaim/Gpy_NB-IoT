import socket
import machine
import lib.logging as logging

log = logging.getLogger("HTTP")

class HTTP():

    def __init__(self):
        self.host = None
        self.port = None
        self.path = None

    def http_to_packet(self, type, content_type, message):
        if self.host is None or self.port is None or self.path is None:
            return False
        packet = ''
        packet += type + ' ' + self.path + " HTTP/1.1" + '\r\n'
        packet += "Host: " + self.host + '\r\n'
        packet += 'Accept: */*' + '\r\n'
        packet += "Content-Type:" + str(content_type) + '\r\n'
        packet += "Content-Length: " + str(len(message)) + '\r\n\r\n'
        packet += message + '\r\n'
        return packet

    # Send a POST message to a remote HTTP server and recieve the answer
    def send_post_message(self, packet):
        addr = socket.getaddrinfo(self.host, self.port)[0][-1]
        log.info('Sending HTTP message to address: {0}:{1}'.format(self.host, self.port))
        s = socket.socket()
        try:
            s.connect(addr)
        except OSError as e:
            log.exception("Could not connect socket to " + str(self.host))
            return False
        s.send(bytes(packet, 'utf8'))
        log.info('Sent HTTP request to {0} on port {1}'.format(self.host, self.port))
        s.close()
        return True

    # Send a GET message to a remote HTTP server and recieve the answer
    def send_get_message(self, packet):
        while True:
            data = s.recv(4096)
            if data:
                log.info("HTTP message recieved.")
                return str(data, 'utf8')
            else:
                log.warning("Did not get response to HTTP GET request.")
                s.close()
                return False
        s.close()
        return True

# Listens on a specific port for HTTP messages and returns a simple "page"
def listen_http(port):
    html = """<!DOCTYPE html>
    <html>
        <head> <title>ESP8266 Pins</title> </head>
        <body> <h1>ESP8266 Pins</h1>
            <table border="1"> <tr><th>Pin</th><th>Value</th></tr> %s </table>
        </body>
    </html>
    """
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
