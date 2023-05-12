import socket
import ssl
import tkinter
import tkinter.font


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


WIDTH, HEIGHT = 800, 600 # Super Video Graphics Array size
HSTEP, VSTEP = 13, 18 # To be replaced with specific font metrics
SCROLL_STEP = 100

FONTS = {}

def get_font(size, weight, slant):
    key = (size, weight, slant)
    if key not in FONTS:
        font = tkinter.font.Font(size=size, weight=weight, slant=slant)
        FONTS[key] = font
    return FONTS[key]

class Text:
    def __init__(self, text, parent):
        self.text = text
        self.children = []
        self.parent = parent
    
    def __repr__(self):
        return repr(self.text)

class Element:
    def __init__(self, tag, attributes, parent):
        self.tag = tag
        self.children = []
        self.parent = parent
        self.attributes = attributes

    def __repr__(self):
        return "<" + self.tag + ">"

def print_tree(node, indent=0):
    print(" " * indent, node)
    for child in node.children:
        print_tree(child, indent + 2)

class HTMLParser:
    def __init__(self, body):
        self.body = body
        self.unfinished = []
    

    def parse(self):
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
        for c in self.body:
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
                if text: self.add_text(text)
                text = ""
                tag_name = ""
            elif c == '>':
                in_angle = False
                if "body" in tag_name: # Ignore header
                    in_body = True
                elif "/body" in tag_name: # Ignore footer
                    break
                self.add_tag(tag_name)
            elif in_angle:
                tag_name += c # Note: also gets tag attributes
            elif not in_angle and in_body:
                if c == '&': # Send loop into entity mode
                    entity = True
                    continue    
                text += c
        # End loop
        return self.finish()
    
    def get_attributes(self, text):
        parts = text.split()
        tag = parts[0].lower()
        attributes = {}
        for attrpair in parts[1:]:
            if "=" in attrpair:
                key, value = attrpair.split("=", 1)
                if len(value) > 2 and value[0] in ["'", "\""]:
                    value = value[1:-1] # Strip quotes from attribute value
                attributes[key.lower()] = value
            else:
                attributes[attrpair.lower()] = ""
        return tag, attributes

    def add_text(self, text):
        if text.isspace(): return # Skip whitespace-only text nodes
        self.implicit_tags(None)
        parent = self.unfinished[-1]
        node = Text(text, parent)
        parent.children.append(node)

    SELF_CLOSING_TAGS = [
        "area", "base", "br", "col", "embed", "hr", "img", "input",
        "link", "meta", "param", "source", "track", "wbr",
    ]

    def add_tag(self, tag):
        tag, attributes = self.get_attributes(tag)
        if tag.startswith("!"): return # Get rid of doctype and comments
        self.implicit_tags(tag)
        if tag.startswith("/"):
            if len(self.unfinished) == 1: 
                return # Last tag finishes tree
            node = self.unfinished.pop()
            parent = self.unfinished[-1]
            parent.children.append(node)
        elif tag in self.SELF_CLOSING_TAGS:
            parent = self.unfinished[-1]
            node = Element(tag, attributes, parent)
            parent.children.append(node)
        else:
            parent = self.unfinished[-1] if self.unfinished else None # First tag has no parent
            node = Element(tag, attributes, parent)
            self.unfinished.append(node)

    HEAD_TAGS = [
        "base", "basefont", "bgsound", "noscript",
        "link", "meta", "title", "style", "script",
    ]

    def implicit_tags(self, tag):
        while True:
            open_tags = [node.tag for node in self.unfinished]
            if open_tags == [] and tag != "html":
                self.add_tag("html")
            elif open_tags == ["html"] and tag not in ["head", "body", "/html"]:
                if tag in self.HEAD_TAGS:
                    self.add_tag("head")
                else:
                    self.add_tag("body")
            elif open_tags == ["html", "head"] and tag not in ["/head"] + self.HEAD_TAGS:
                self.add_tag("/head")
            else:
                break

    def finish(self):
        if len(self.unfinished) == 0:
            self.add_tag("html")
        while len(self.unfinished) > 1:
            node = self.unfinished.pop()
            parent = self.unfinished[-1]
            parent.children.append(node)
        return self.unfinished.pop() 

class Layout:
    """A display list of the entire page layout."""
    def __init__(self, tokens):
        self.weight = "normal"
        self.style = "roman"
        self.size = 16
        self.cursor_x, self.cursor_y = HSTEP, VSTEP
        
        self.line = []
        self.display_list = []
        self.recurse(tokens)
        # for tok in tokens:
        #     if isinstance(tok, Text):
        #         self.text(tok)
        #     else: 
        #         self.tag(tok)
        self.flush()

    def recurse(self, tree):
        if isinstance(tree, Text):
            self.text(tree)
        else:
            self.open_tag(tree.tag)
            for child in tree.children:
                self.recurse(child)
            self.close_tag(tree.tag)

    def open_tag(self, tag):
        if tag == "i": self.style = "italic"
        elif tag == "b": self.weight = "bold"
        elif tag == "small": self.size -= 2
        elif tag == "big": self.size += 4
        elif tag == "br": self.flush()
        elif tag == "h1":
            self.size += 8
            self.weight = "bold"

    def close_tag(self, tag):
        if tag == "i": self.style = "roman"
        elif tag == "b": self.weight = "normal"
        elif tag == "small": self.size += 2
        elif tag == "big": self.size -= 4
        elif tag == "h1":
            self.size -= 8
            self.weight = "normal"
            self.flush()
            self.cursor_y += VSTEP # Small gap after header
        elif tag == "p":
            self.flush()
            self.cursor_y += VSTEP # Small gap btwn paragraphs

    def text(self, tok):
        font = get_font(self.size, self.weight, self.style)
        
        for word in tok.text.split():
            w = font.measure(word)
            if self.cursor_x + w >= WIDTH - HSTEP:
                self.flush()
            self.line.append((self.cursor_x, word, font))
            self.cursor_x += w + font.measure(" ")

    def flush(self):
        if not self.line: return
        metrics = [font.metrics() for x, word, font in self.line]
        max_ascent = max([metric["ascent"] for metric in metrics])
        baseline = self.cursor_y + (1.25 * max_ascent) # Should really be 1.125 above and below
        for x, word, font in self.line:
            y = baseline - font.metrics("ascent")
            self.display_list.append((x, y, word, font))
        self.cursor_x = HSTEP
        self.line = []
        max_descent = max([metric["descent"] for metric in metrics])
        self.cursor_y = baseline + (1.25 * max_descent)
  
class Browser:
    def __init__(self):
        self.window = tkinter.Tk() # Create a window
        self.window.bind("<Down>", self.scrolldown)
        self.window.bind("<Up>", self.scrollup)
        self.canvas = tkinter.Canvas(
            self.window,
            width=WIDTH,
            height=HEIGHT
        )
        self.window.bind("<Configure>", self.resize)
        self.canvas.pack() # Position canvas inside window
        self.scroll = 0
        self.tokens = []
        # Set a font (which in Tk has a set size, style, and weight)
        self.times = tkinter.font.Font(
            family = "Times",
            size=16,
            weight="normal",
            slant="roman",
        )
        self.font1 = tkinter.font.Font(family="Times", size=16)
        self.font2 = tkinter.font.Font(family="Times", size=16, slant="italic")

        # print(self.times.metrics())
        # print(self.times.measure("Hi!"))

    def load(self, url):
        """ Load a web page by requesting it and displaying the HTML response. """
        # self.canvas.create_rectangle(10, 20, 400, 300) # x,y top left corner and x,y bottom right
        # self.canvas.create_oval(100, 100, 150, 150) # oval fits rectangle defined by points
        # self.canvas.create_text(200, 150, text="Welcome!") # Justify left by default
        headers, body = request(url)
        self.nodes = HTMLParser(body).parse()
        self.display_list = Layout(self.nodes).display_list
        self.draw()

    def draw(self):
        self.canvas.delete("all")
        # x, y = 200, 200 # Testing using different fonts
        # self.canvas.create_text(x, y, text="Hello, ", font=self.font1, anchor='nw')
        # x += self.font1.measure("Hello, ")
        # self.canvas.create_text(x, y, text="world!", font=self.font2, anchor='nw')
        
        for x, y, c, f in self.display_list:
            if y > self.scroll + HEIGHT: continue # Don't draw characters that are below the viewport
            if y + VSTEP < self.scroll: continue # Don't draw characters whose bottom edges are above the viewport
            self.canvas.create_text(x,y - self.scroll, text=c, font=f, anchor='nw')

    def scrolldown(self, e):
        self.scroll += SCROLL_STEP
        self.draw()

    def scrollup(self, e):
        if self.scroll > -100:
            self.scroll -= SCROLL_STEP
        self.draw()

    def resize(self, e):
        global WIDTH, HEIGHT
        WIDTH, HEIGHT = e.width, e.height
        self.canvas.pack(fill='both', expand=True)
        self.display_list = Layout(self.nodes).display_list
        self.draw()
          
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
    Browser().load(sys.argv[1]) # Create browser and load with command line url
    tkinter.mainloop() # Start the process of redrawing the screen
