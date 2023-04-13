# File: proxy.py
# Author: Phubeth (Pete) Mettaprasert
# Date: 11/04/2023
# Description: This is a proxy server that listens for connections from
#              clients. If the request is valid, the server checks the cache
#              for the file. If the file is in the cache, the proxy returns the
#              file to the client from the cache. If the file is not in the
#              cache, the proxy sends the request to the server. If the server
#              returns a 200 status code, the proxy stores the file in the cache
#              and sends the response to the client. Otherwise, the file is not
#              stored in the cache and the proxy sends the appropriate response
#              back to the client.

from socket import *
from urllib.parse import urlparse
import sys
from pathlib import Path


class ProxyServer:
    """
    This class represents a proxy server. It will listen for connections on a
    designated port number. When a connection is accepted, it will then take
    a request from the client. Once the request is received,it will either check
    the cache for the file or send a request to the server. If the file is in
    the cache,the proxy server will send back the file from the cache.
    If the file is not in the cache, the proxy server will send the request to
    the actual server. Depending on the status code of the response, the proxy
    server will either store the response in the cache and send it back to
    the client or respond with a 404 or 500 error.

    Attributes
    ----------
    port_num : int
        The port number that the proxy server will listen on.

    proxy_socket : socket
        The socket that the proxy server will listen on.

    request_method : str
        The method of the request sent from the client. Only GET is allowed.


    request_url_parsed : urlparse
        The parsed URL of the request sent from the client. Uses the urlparse
        function from the urllib.parse module.

    request_version : str
        The version of the request sent from the client. Only HTTP/1.0 or
        lower is allowed.

    Methods
    -------
    start_server()
        Runs the proxy server.

    create_socket()
        Creates a socket and returns a socket object.

    bind_socket(socket, port_num)
        Binds the socket to the port number.

    listen_for_connections(socket)
        Listens for connections on the socket.

    accept_connection(socket)
        Accepts a connection on the socket.

    handle_request(client_socket)
        Handles the request sent from the client.

    send_request_to_server()
        Sends the request to the server.

    parse_request(request)
        Parses the request sent from the client.

    check_request_validity()
        Checks if the request is valid.

    get_status_code()
        Gets the status code from the response from the server.

    add_length_and_cache_to_header(response, in_cache)
        Adds the Content-Length (if it doesn't exist) and Cache-Hit headers to
        the response from the server.

    store_response_in_cache()
        Stores the response from the server in the cache.

    create_500_response(response)
        Creates a 500 response.

    check_file_in_cache()
        Checks the cache for the file.

    get_response_from_cache()
        Gets the response from the cache.

    """

    def __init__(self, port_num):
        """
        Parameters
        ----------
        port_num : int
            The port number that the proxy server will listen on.
        """
        self.port_num = port_num

        # Create cache directory if it doesn't exist.
        if not Path("./cache").is_dir():
            Path("./cache").mkdir()

    def start_server(self):
        """
        Runs the proxy server. Accept connection will call the handle_request as
        well.
        """
        self.proxy_socket = self.create_socket()
        self.bind_socket(self.proxy_socket, self.port_num)
        self.listen_for_connections(self.proxy_socket)
        self.accept_connection(self.proxy_socket)

    def create_socket(self):
        """
        Creates a socket and returns a socket object.

        Returns
        -------
        socket : socket
            A socket object.
        """
        try:
            proxy_socket = socket(AF_INET, SOCK_STREAM)
            return proxy_socket
        except error as e:
            print("Error creating socket: " + str(e))
            sys.exit(1)

    def bind_socket(self, socket, port_num):
        """
        Binds the socket to the port number. Provides linear searching for
        next available port number if the port number is already in use.

        Parameters
        ----------
        socket : socket
            The socket that the server will bind to the port number.

        port_num : int
            The port number that the proxy server will listen on.
        """

        while True:
            try:
                socket.bind(("", port_num))
                break
            except error as e:
                print("Unable to bind socket to port " + str(port_num))
                port_num += 1
                print("Trying port " + str(port_num) + "...")

        print("Socket running on port " + str(port_num))

    def listen_for_connections(self, socket):
        """
        Listens for connections on the socket.

        Parameters
        ----------
        socket : socket
            The socket that will listen for connections.
        """
        try:
            socket.listen(5)
        except error as e:
            print("Error listening on socket: " + str(e))
            sys.exit(1)

    def accept_connection(self, socket):
        """
        Accepts a connection on the socket and calls the handle_request method.

        Parameters
        ----------
        socket : socket
            The socket that the proxy server will listen on.
        """
        while True:
            print("Listening for connections and waiting for connection...")

            try:
                client_socket, client_address = socket.accept()
                print("Received connection from IP: %s, Port: %s" %
                      (client_address[0], client_address[1]))

                print("\n******* Ready to Serve *******\n")

                self.handle_request(client_socket)

            except error as e:
                print("Error accepting connection, please try again.")

            print("\nReady for the new connection...\n")

    def handle_request(self, client_socket):
        """
        This method will handle the request from the client. There are 2
        choices after the request is received. The first choice is to check
        if the file is in the cache. If the file is in the cache, the proxy
        server will send the file from the cache to the client. If the file
        is not in the cache, the proxy server will send the request to the
         actual server. Depending on the status code of the response, the proxy
        server will either store the response in the cache and send it back
        to the client or take the response that is either a 404 or 500 error
        and send it back to the client.

        Parameters
        ----------
        client_socket : socket
            The socket that the client is connected to.
        """

        print("Waiting for request from client...\n")

        try:
            request = client_socket.recv(1024).decode("utf-8")

        except error as e:

            print("Error receiving request from client.\nPlease try again.")
            client_socket.close()
            return

        print("Request received from client:\n" + request.encode())

        if not self.check_request_validity(request):
            response_500 = self.create_500_response(None)
            print("Request is invalid. Sending 500 response to client.")
            client_socket.send(response_500.encode("utf-8"))
            client_socket.close()
            return

        self.parse_request(request)

        if (self.check_file_in_cache()):
            print("File is in cache...")
            cached_response = self.get_response_from_cache()
            mod_response = self.add_length_and_cache_to_header(
                cached_response, True)

            print("Sending file from cache to client...")
            client_socket.send(mod_response.encode("utf-8"))

        else:

            print("File is not in cache...")

            response_from_server = self.send_request_to_server()

            # If we get an error sending the request to the server, send a 500
            if response_from_server is None:
                response = self.create_500_response(None)
                print("Error sending request to server. Sending 500 response to client.")
                client_socket.send(response.encode())
                client_socket.close()
                return

            status_code = self.get_status_code(response_from_server)

            if status_code == 200:
                print("Response has been received from server with status code: 200")
                print("Storing response in cache...")
                self.store_response_in_cache(response_from_server)
                response = self.add_length_and_cache_to_header(
                    response_from_server, False)
                client_socket.send(response.encode())

            elif status_code == 404:
                print("Response has been received from server with status "
                      "code: 404")
                print("Unable to store response in cache...")
                response = self.add_length_and_cache_to_header(response_from_server, False)
                client_socket.send(response.encode())

            else:
                print("Response has been received from server with status "
                      "code: 500")
                print("Unable to store response in cache...")
                response = self.create_500_response(response_from_server)
                client_socket.send(response.encode())

        print("Response sent to client. All done!")
        print("Closing connection with client...\n")
        client_socket.close()

    def parse_request(self, request):
        """
        Parses the request sent from the client using urllib.parse.

        Parameters
        ----------
        request : str
            The request sent from the client.
        """

        request_split = request.split(" ")
        self.request_method = request_split[0].strip()
        request_url = request_split[1].strip()
        self.request_version = request_split[2].strip()

        self.request_url_parsed = urlparse(request_url)

        # If the port is not specified, add port 80 to the netloc.
        if self.request_url_parsed.port is None:
            self.request_url_parsed = self.request_url_parsed._replace(
                netloc=self.request_url_parsed.netloc + ":80")

            self.url_parsed = urlparse(self.url_parsed.geturl())

    def check_request_validity(self, request):
        """
        Checks if the request is valid.

        Parameters
        ----------
        request : str
            The request sent from the client.

        Returns
        -------
        bool
            True if the request is valid, False otherwise.
        """

        request_split = request.split("\r\n")

        if len(request_split) != 3:
            return False

        if request_split[0].strip() != "GET":
            return False

        if request_split[2].strip()[0:5] != "HTTP/":
            return False

        # is not equal to HTTP/1.1 or HTTP/1.0 or HTTP/0.9
        if request_split[2].strip() != "HTTP/1.1" and \
                request_split[2].strip() != "HTTP/1.0" and \
                request_split[2].strip() != "HTTP/0.9":
            return False

        if "http://" not in request_split[1].strip():
            return False

        return True

    def create_500_response(self, response):
        """
        Creates a 500 response for the client.

        Parameters
        ----------

        response : str
            The response that will be sent to the client.

        Returns
        -------
        str
            The 500 response that will be sent to the client.
        """

        if (response is None):

            response500 = "HTTP/1.1 500 Internal Server Error\r\n" \
                          "Content-Length: 0\r\n" \
                          "Connection: close\r\n" \
                          "Cache-Hit: 0\r\n\r\n"

            return response500


        else:

            response_split = response.split("\r\n")
            response_split[0] = "HTTP/1.1 500 Internal Server Error"

            last_line_of_headers = response_split.index("")

            # Reconstruct the response
            response500 = ""

            for i in range(last_line_of_headers + 1):
                response500 += response_split[i] + "\r\n"

            response500 += "\r\n"

            for i in range(last_line_of_headers + 1, len(response_split)):
                response500 += response_split[i]

            # Add the Content-Length(if not in header) and Cache-Hit header
            modified_response = self.add_length_and_cache_to_header(
                response500, False)

            return modified_response

    def add_length_and_cache_to_header(self, response, in_cache):
        """
        This method will add the Content-Length if it is not in the header
        and add the Cache-Hit header if the response is in the cache.

        Parameters
        ----------
        response : str
            The response sent from the server.

        in_cache : bool
            True if the response is in the cache, False otherwise.

        Returns
        -------
        response : str
            The response with the Content-Length and Cache-Hit headers added.
        """

        response_split = response.split("\r\n")

        # Keep track of the last line of the headers
        last_line_of_headers = response_split.index("")

        # If the Content-Length is not in the header add a Content-Length
        if not any("Content-Length" in line for line in
                   response_split[0:last_line_of_headers]):

            content_length = 0

            # Calculate the content length
            for i in range(last_line_of_headers + 1, len(response_split)):
                content_length += len(response_split[i])

            response_split.insert(last_line_of_headers, "Content-Length: " +
                                  str(content_length))

            last_line_of_headers += 1

        # If Connection-Close is not in the header add a Connection-Close
        if not any("Connection: close" in line for line in
                     response_split[0:last_line_of_headers]):
            response_split.insert(last_line_of_headers, "Connection: close")
            last_line_of_headers += 1

        # Add cache hit header
        if in_cache:
            response_split.insert(last_line_of_headers, "Cache-Hit: 1")
        else:
            response_split.insert(last_line_of_headers, "Cache-Hit: 0")

        # Reconstruct the response
        response = ""

        # Add the headers.
        for line in response_split[0:last_line_of_headers + 1]:
            response += line + "\r\n"

        response += "\r\n"

        # Attach the body
        for line in response_split[last_line_of_headers + 1:]:
            response += line

        return response

    def check_file_in_cache(self):
        """
        This method will check if the file is in the cache.

        Returns
        -------
        bool
            True if the file is in the cache, False otherwise.
        """

        path = "./cache/" + self.request_url_parsed.hostname + \
               self.request_url_parsed.path

        file = Path(path)

        if file.is_file():
            return True
        else:
            return False

    def get_response_from_cache(self):
        """
        This method will get the response from the cache.

        Returns
        -------
        response : str
            The response from the cache.

        """

        path = "./cache/" + self.request_url_parsed.hostname + \
               self.request_url_parsed.path

        try:
            with open(path, "rb") as file:
                response = file.read().decode("utf-8")

        except:
            print("Error reading file from cache")
            sys.exit()

        return response

    def send_request_to_server(self):
        """
        This method will send the request to the server.

        Returns
        -------
        response : str
            The response from the server. If no response is received, returns
            None.

        """

        request_socket = self.create_socket()

        try:
            request_socket.connect((self.request_url_parsed.hostname,
                                    self.request_url_parsed.port))
        except:
            return None

        request = self.request_method + " "
        if self.url_parsed.path != "":
            request += self.url_parsed.path
        else:
            request += "/"

        request += " " + self.request_version + "\r\n"
        request += "Host: " + self.request_url_parsed.hostname + "\r\n"
        request += "Connection: close\r\n\r\n"

        print("Sending request to server: \n" + request)

        try:
            request_socket.sendall(request.encode())
        except:
            return None

        response = b''

        while True:
            try:
                data = request_socket.recv(4096)
            except:
                return None

            if not data:
                break

            response += data

        return response.decode("utf-8")

    def get_status_code(self, response):
        """
        This method will get the status code from the response.

        Parameters
        ----------
        response : str
            The response from the server.

        Returns
        -------
        status_code : str
            The status code from the response.

        """

        response_split = response.split("\r\n")
        status_code = response_split[0].split(" ")[1]
        return status_code

    def store_response_in_cache(self, response):
        """
        This method will store the response in the cache.

        Parameters
        ----------
        response : str
            The response from the server.

        """

        path = "./cache/" + self.request_url_parsed.hostname + \
               self.request_url_parsed.path

        path_split = path.split("/")
        path_to_file = "./cache/"

        # For every directory in the path, create it if it does not exist
        for i in range(len(path_split) - 1):
            path_to_file += path_split[i]

            directory = Path(path_to_file)
            if not directory.is_dir():
                directory.mkdir(parents=True, exist_ok=True)

            path_to_file += "/"

        # Add the file name to the path
        path_to_file += path_split[-1]


        # Writing only the body of the response to the file
        response_split = response.split("\r\n")
        last_line_of_headers = response_split.index("")
        try:
            with open(path_to_file, "wb") as file:
                for line in response_split[last_line_of_headers + 1:]:
                    file.write(line.encode())

        except:
            print("Unable to write to cache, due to file cannot be both"
                  " a directory and a file at the same time")
            sys.exit()


def get_port_num():
    """
    This function will get the port number from the command line arguments.

    Returns
    -------
    port_num : int
        The port number.

    """

    if len(sys.argv) < 2:
        print("Port number not given.")
        sys.exit()

    port = int(sys.argv[1])

    return port

def main():
    port_num = get_port_num()
    proxy_server = ProxyServer(port_num)
    proxy_server.start_server()

if __name__ == "__main__":
    main()




