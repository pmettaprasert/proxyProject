Web Proxy Server with Caching

A lightweight web proxy server in Python that caches web pages to optimize client-server communication.

Quick Overview

Purpose: Relay between web clients and servers, caching responses to speed up repeat requests.
Author: Phubeth (Pete) Mettaprasert
Date: 11/04/2023



Features
Listens on specified port for client connections.
Checks cache for client requests, serving cached responses when available.
For uncached requests, communicates with the target server.
Caches responses with a 200 status code.


Libraries
socket: Network socket operations.
urllib.parse.urlparse: URL parsing.
sys: System interactions.
pathlib.Path: File path management.


Note
Ensure you're familiar with web proxies before deploying this. Dive deeper into proxy functionalities via trusted resources.
