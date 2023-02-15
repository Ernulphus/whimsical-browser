import socket
import ssl

# 
def request (url):
    """Open a socket, send an HTTP request to url, and return head and body of response."""
    scheme, url = url.split("://", 1)
    assert scheme in ['http', 'https', 'file', 'data'], \
        "Unknown scheme {}".format(scheme)

    # Old code for only http
    # assert url.startswith("http://")
    # url = url[len("http://"):]

    host, path = url.split('/', 1)
    path = '/' + path

    # Create a socket for exchanging data with another computer
    # These are actually the default arguments, but just to be explicit:
    s = socket.socket(
        family=socket.AF_INET,      # Address Family - internet (rather than bluetooth, eg)
        type=socket.SOCK_STREAM,    # Type - Stream of data (rather than datagrams, eg)
        proto=socket.IPPROTO_TCP,   # protocol - IP/TCP (rather than QUIC eg)
    )

    port = 80 if scheme == 'http' else 443 # Typical port 80 for http and 443 for https
    if ':' in host: # Check for custom ports, like example.org:8080/
        host, port = host.split(':', 1)
        port = int(port)
    s.connect((host,port)) # Connect to host on designated port

    # Wrap socket in secure context
    if scheme == 'https':
        ctx = ssl.create_default_context()
        s = ctx.wrap_socket(s, server_hostname=host)

    # encode() turns the string into a bytestream [decode() turns it back]
    request = s.send('GET {} HTTP/1.0\r\n'.format(path).encode('utf8') + \
            encodeHeaders({ # Exercise 1.1 Make it easy to add headers
            'Host':host,
            'Connection':'close', 
            'User-Agent':"Bony00's Whimsical Browsing Machine",
            }))

    # print(request) # 47 -> number of bytes sent out

    # makefile() is like open() but from a socket
    response = s.makefile('r', encoding='utf8', newline='\r\n') # Note: shouldn't hardcode utf8

    # Print entire response
    # for statusline in response:
    #     print(statusline, end='')

    statusline = response.readline()
    version, status, explanation = statusline.split(' ', 2)
    assert status == '200', '{}: {}'.format(status,explanation)
    # Don't check that the version is the same, 1.1 responses are A-OK

    # Populate a dictionary with the response headers
    headers = {}
    while True:
        line = response.readline()
        if line == '\r\n': break
        header, value = line.split(':', 1)
        headers[header.lower()] = value.strip()

    # Don't handle compressed pages
    assert 'transfer-encoding' not in headers
    assert 'content-encoding' not in headers

    body = response.read() # Everything after the headers, i.e., the data
    s.close # Wrap up the socket

    return headers, body

def show(body):
    """ Show all text in the page (strips HTML tags and head section) """
    in_angle = False
    in_body = False
    tag_name = "" # Gets populated as a tag name is scanned
    entity = 0 # Becomes true when an & is read, so that next char determines the symbol
    entity_name = ""
    for c in body:
        if entity = 1:
            entity_name += c
            entity = 2
        elif entity = 2:
            entity_name += c
            print({ # This is better than before but still messes up on all entities beyond <>
                'lt':'<', 'gt':'>',
                'qu':'"', 'ap':"'",
                'co':'©', 're':'®',
                'nb':' ',
                'ce':'¢', 'po':'£', 'ye':'¥', 'eu':'€',
            }[entity_name], end='')
            entity_name = ''
            entity = 0
        elif c == '<':
            in_angle = True
            tag_name = ""
        elif c == '>':
            in_angle = False
            if tag_name == "body":
                in_body = True
            elif tag_name == "/body": # Just to ignore footers
                in_body = False
        elif in_angle:
            tag_name += c
        elif not in_angle and in_body:
            if c == '&':
                entity = 1
                continue    
            print(c, end='')
            

def load(url):
    """ Load a web page by requesting it and displaying the HTML response. """
    headers, body = request(url)
    show(body)

def encodeHeaders(headers):
    """ Exercise 1: Make it easy to add further headers """
    # headers should be a dictionary
    finalString = ""
    for key in headers:
        finalString += key + ": " + headers[key] + '\r\n'
    finalString += "\r\n" 
    return finalString.encode('utf8')
    # \r is a carriage return - doubled at the end for the empty line to finish request

# If in main, load command line argument url
if __name__ == '__main__':
    import sys
    load(sys.argv[1])