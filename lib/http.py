import socket
import machine
import lib.logging as logging

log = logging.getLogger("HTTP")

REMOTE_SERVER_IP = '172.17.60.2'
REMOTE_SERVER_PORT = 80
REMOTE_SERVER_PATH = '/'

def http_config(remote_ip, remote_port, remote_path):
    log.info("Updated HTTP configuration")
    global REMOTE_SERVER_IP
    REMOTE_SERVER_IP = remote_ip
    global REMOTE_SERVER_PORT
    REMOTE_SERVER_PORT = remote_port
    global REMOTE_SERVER_PATH
    REMOTE_SERVER_PATH = remote_path

# Send a GET message to a remote HTTP server and recieve the answer
def http_msg(msg, type="GET", ip=REMOTE_SERVER_IP, port=REMOTE_SERVER_PORT, path=REMOTE_SERVER_PATH):
    addr = socket.getaddrinfo(ip, port)[0][-1]
    s = socket.socket()
    try:
        s.connect(addr)
    except OSError as e:
        log.exception(e)
    s.send(bytes('{0} {1} HTTP/1.1\r\nHost: {2}:{3}\r\n{4}'.format(type, path, ip, port, msg), 'utf8'))
    log.info('Sent HTTP request to {0} on port {1}'.format(REMOTE_SERVER_IP, REMOTE_SERVER_PORT))
    if type == "GET":
        while True:
            data = s.recv(4096)
            if data:
                log.info("HTTP message recieved.")
                return str(data, 'utf8')
            else:
                log.warning("Did not get response to HTTP GET request.")
                return False
                break
    s.close()

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
