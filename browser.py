import socket 

# 
def request (url):
    """Open a socket, send an HTTP request to url, and return head and body of response."""
    assert url.startswith("http://")
    url = url[len("http://"):]

    host, path = url.split('/', 1)
    path = '/' + path

    # Create a socket for exchanging data with another computer
    # These are actually the default arguments, but just to be explicit:
    s = socket.socket(
        family=socket.AF_INET,      # Address Family - internet (rather than bluetooth, eg)
        type=socket.SOCK_STREAM,    # Type - Stream of data (rather than datagrams, eg)
        proto=socket.IPPROTO_TCP,   # protocol - IP/TCP (rather than QUIC eg)
    )

    s.connect((host,80)) # Connect to host on port 80

    # encode() turns the string into a bytestream [decode() turns it back]
    request = s.send('GET {} HTTP/1.0\r\n'.format(path).encode('utf8') + \
            'Host: {}\r\n\r\n'.format(host).encode('utf8'))
    # \r is a carriage return - doubled at the end for the empty line to finish request

    print(request) # 47 -> number of bytes sent out

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
        line = response.resdline()
        if line == '\r\n': break
        header, value = line.split(':', 1)
        headers[header.lower()] = value.strip()

    assert 'transfer-encoding' not in headers
    assert 'content-encoding' not in headers

    body = response.read() # Everything after the headers, i.e., the data
    s.close # Wrap up the socket

    return headers, body