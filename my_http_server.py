import socket, re, logging, os


# Setup basic variables.
webroot_path = os.getcwd() + '\webroot\\'  # Website path.
default_url = webroot_path + 'index.html'  # Default index.html path.
http_version = 'HTTP/1.1'  # Http version used.

# Setup logging to a log.txt file.
log = logging.getLogger(__name__)
log.level = logging.DEBUG
fh = logging.FileHandler(filename='log.txt', mode='w')
log.addHandler(fh)
log.info(
    'my_http_server_log_file:\n\tWebsite path: {}\n\tDefault URL: {}\n'.format(webroot_path, default_url))
fh.setFormatter(logging.Formatter('%(asctime)s  %(levelname)s: %(message)s'))
log.addHandler(fh)


def validate_http_request(client_socket):
    """  Receives the socket to the client and determines
        weather it is valid HTTP request, if valid isolate and
        return the sent method and resource string.

    :param  client_socket:The connection socket to the client:
           the web browser sending the request.

    :return:  If the request is valid return True + the
             resource string stated in the request.
             If not valid return False. """

    # A (partial) list of valid http protocol request methods.
    valid_request_methods = ['GET', 'HEAD', 'POST', 'PUT', 'DELETE', 'TRACE', 'OPTIONS', 'CONNECT', 'PATCH']

    # Client http request.
    request = client_socket.recv(1024)

    #  Using regex to determine if the request is valid:
    # if re.match() returns a match object the request is valid
    # if re.match() returns None the request is not a valid http request.
    request = re.match(r'(.+) (.+) HTTP/1.1\r\n(.*:.*)\r\n*', request)
    method = 'GET'
    resource = default_url

    try:
        if request.group(1) in valid_request_methods:
            if request.group(2) == '/':
                pass
            else:
                method = request.group(1)
                resource = webroot_path + request.group(2)

                log.info(
                    'Request found to be valid\n\tMethod: {}\n\tResource: {}'.format(request.group(1),
                                                                                     request.group(2)))

                # Cut last '/' char if exists.
                if resource[-1] == '/':
                    resource = resource[:-1]

                # Replace '/' with '\\' for windows compatibility.
                resource = resource.replace('/', '\\')
        else:
            log.info('Request found to be invalid.')
            return False, '', ''

        return True, method, resource

    except (IndexError, AttributeError, TypeError) as e:
        log.critical('{}\n\tResource: {}'.format(e.message, resource))


def handle_client_request(client_socket, method, resource):
    """  Receives the socket to the client, the http
        method and resource requested,
        checks to see if the resource is available:
        if available sends an appropriate response,
        if not closes the connection to the client.

    :param:  client_socket: The connection socket to the client:
           the web browser sending the request.

           method: the http protocol method sent from the client.

            resource: the web page, file or other resource requested
           by the client. """

    #  Capture all GET variables in to a dictionary:
    # regex to extract the string following the '?' character.
    # List comprehension to create a list of of couples: ((k, v), (k, v)...(k, v))
    # dict() -> Creates a dictionary from a the list.

    try:
        received_get_variables = dict([i.split('=') for i in (re.search(r'\?(.*)', resource).group(1)).split('&')])

        # Calculates the area of a triangle.
        if re.match(r'.*calculate-area.*', resource):
            h = float(received_get_variables['height'])
            w = float(received_get_variables['width'])
            a = h * w / 2

            client_socket.send('<h1>Area of a triangle = ( ' + str(h) + ' x ' +
                               str(w) + ' ) / 2 = ' + str(a) + '</h1>')
            return

        # Perform additive calculation.
        elif re.match(r'.*calculate-next.*', resource):
            s = ''
            sum = 0

            for k, v in received_get_variables.items():
                s += v + ' +'
                sum += int(v)

            client_socket.send('<h1>' + s[:-1] + ' = ' + str(sum) + '</h1>')
            return
    except AttributeError:
        log.info('No parameters sent.')

    # Seek wab page resource.
    resource_type = resource[resource.rfind('.') + 1:]

    if not os.path.isfile(resource):
        # Resource not found, send code 404.
        log.warning('404 Resource {} not found in server:'.format(resource))

        status_code = '404'
        phrase = 'Not Found'
        headers = ''
        body = '<h1> Error 404 File Not Found.</h1>'
    else:
        #  Resource found, send code 200, define headers
        # and send requested resource back to client.
        log.info('200 Resource {} found in server.'.format(resource))

        status_code = '200'
        phrase = 'OK'

        # Define headers.
        content_length = os.stat(resource).st_size  # The length of the file sent.

        #  Determine file type and open it accordingly:
        # binary textual for txt and html, binary for the rast.
        if resource_type == 'html' or resource_type == 'txt':
            content_type = 'text/html; charset=utf-8'
            web_page = open(resource, 'r')
        elif resource_type == 'jpg' or resource_type == 'jpeg':
            content_type = 'image/jpeg'
            web_page = open(resource, 'rb')
        elif resource_type == 'js':
            content_type = 'text/javascript; charset=UTF-8'
            web_page = open(resource, 'rb')
        elif resource_type == 'css':
            content_type = 'text/css'
            web_page = open(resource, 'rb')
        elif resource_type == 'ico':
            content_type = 'image/x-icon'
            web_page = open(resource, 'rb')
        else:
            content_type = ''
            web_page = ''

        # Concatenate the headers.
        headers = 'Content-Length: {}\r\nContent-Type: {}'.format(content_length,
                                                                  content_type)
        body = web_page.read()

    response_status = '{} {} {}'.format(http_version, status_code, phrase)  # Example: HTTP/1.1 200 OK

    # Send response to client: status line, headers and body (if any).
    client_socket.send(response_status + '\r\n' + headers + '\r\n\r\n' + body)

    log.info('Response sent to server: {}'.format(resource))

    # If file is open: close it.
    try:
        web_page.close()
    except (AttributeError, UnboundLocalError):
        pass


def main():
    #  Create a socket to listen to port 80: the standard port
    # for HTTP requests in the TCP and UDP protocols.
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(('0.0.0.0', 80))
    server_socket.listen(1)

    while True:
        log.info('Listening on port 80.')

        # Accept and create a connection socket to the client.
        client_socket, client_address = server_socket.accept()

        log.info('Connection to {} accepted, socket to client created.'.format(client_address))

        #  If the client sent a valid http request,
        # proceed to handle the request.
        try:
            is_valid, method, resource = validate_http_request(client_socket)
        except TypeError:
            pass

        if is_valid:
            handle_client_request(client_socket, method, resource)


if __name__ == '__main__':
    main()
