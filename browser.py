import socket
import ssl
import tkinter

WIDTH, HEIGHT = 800, 600 # Super Video Graphics Array size
HSTEP, VSTEP = 13, 18 # To be replaced with specific font metrics


class Browser:
    def __init__(self):
        self.window = tkinter.Tk() # Create a window
        self.canvas = tkinter.Canvas(
            self.window,
            width=WIDTH,
            height=HEIGHT
        )
        self.canvas.pack() # Position canvas inside window
    
    def load(self, url):
        """ Load a web page by requesting it and displaying the HTML response. """
        # self.canvas.create_rectangle(10, 20, 400, 300) # x,y top left corner and x,y bottom right
        # self.canvas.create_oval(100, 100, 150, 150) # oval fits rectangle defined by points
        # self.canvas.create_text(200, 150, text="Welcome!") # Justify left by default
        headers, body = request(url)
        cursor_x, cursor_y = HSTEP, VSTEP

        text = lex(body)
        for c in text:
            self.canvas.create_text(cursor_x, cursor_y, text=c)
            cursor_x += HSTEP
            if cursor_x >= WIDTH - HSTEP:
                cursor_x = HSTEP
                cursor_y += VSTEP

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

def layout(text):
    display_list = []
    cursor_x, cursor_y = HSTEP, VSTEP
    for c in text:
        display_list.append((cursor_x, cursor_y, c))


def lex(body):
    text = ''
    accepted_entities = {
                    'lt':'<', 'gt':'>',
                    'quot':'"', 'apos':"'",
                    'copy':'©', 'reg':'®',
                    'nbsp':' ', 'amp':'&',
                    'cent':'¢', 'pound':'£', 
                    'yen':'¥', 'euro':'€',
                }
    """ Show all text in the page (strips HTML tags and head section) """
    in_angle = False
    in_body = False
    tag_name = "" # Gets populated as a tag name is scanned
    in_entity = False
    entity_name = ""
    # Loop to populate text with the web page (no tags)
    for c in body:
        # Entity handling
        if in_entity:
            if c == ';':
                in_entity = False
                if entity_name in accepted_entities:
                    text += accepted_entities[entity_name]
                entity_name = ''
            else:
                entity_name += c
        # End entity handling
        # Tag filtering
        elif c == '<':
            in_angle = True
            tag_name = ""
        elif c == '>':
            in_angle = False
            if "body" in tag_name: # Ignore header
                in_body = True
            elif "/body" in tag_name: # Ignore footer
                break
        elif in_angle:
            tag_name += c # Note: also gets tag attributes
        elif not in_angle and in_body:
            if c == '&': # Send loop into entity mode
                entity = True
                continue    
            text += c
    # End loop
    return text
            
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
    Browser().load(sys.argv[1]) # Create broser and load with command line url
    tkinter.mainloop() # Start the process of redrawing the screen
