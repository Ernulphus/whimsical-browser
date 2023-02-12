import socket 

url = 'http://example.org/index.html'

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
response = s.makefile('r', encoding='utf8', newline='\r\n')

for statusline in response:
    print(statusline, end='')