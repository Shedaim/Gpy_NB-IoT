import socket
import machine

# Send a GET message to a remote HTTP server and recieve the answer
def http_get(ip, port):
    addr = socket.getaddrinfo(ip, port)[0][-1]
    s = socket.socket()
    try:
        s.connect(addr)
    except OSError as e:
        print (e)
    s.send(bytes('GET HTTP/1.0', 'utf8'))
    while True:
        data = s.recv(4096)
        if data:
            print(str(data, 'utf8'), end='')
        else:
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
    try:
        while True:
            cl, addr = s.accept()
            print('client connected from', addr)
            cl.send(html)
            cl.close()
    except:
        cl.close()

ue.connect(False)
ue.ping("172.17.60.2")
http_get("172.17.60.2", 80)
