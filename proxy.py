import socket
import sys
import threading

# This is a pretty hex dumping function directly taken from the comments here:
# http://code.activestate.com/recipes/142812-hex-dumper/
def hexdump(src, length=16):
    result = []
    digits = 2
    for i in range(0, len(src), length):
        s = src[i:i+length]
        hexa = ' '.join([f"{x:02X}" for x in s])
        text = ''.join([chr(x) if 0x20 <= x < 0x7F else '.' for x in s])
        result.append(f"{i:04X}   {hexa:<{length*(digits+1)}}   {text}")
    print("\n".join(result))

def receive_from(connection):
    buffer = b""
    # We set a 2-second timeout; depending on your target, this may need to be adjusted 
    connection.settimeout(2)
    try:
        # Keep reading into the buffer until there's no more data or we time out
        while True:
            data = connection.recv(4096)
            if not data:
                break
            buffer += data
    except:
        pass
    return buffer

# Modify any requests destined for the remote host
def request_handler(buffer):
    # Perform packet modifications
    return buffer

# Modify any response destined for the local host
def response_handler(buffer):
    # Perform packet modifications
    return buffer

# Perform all sending and receiving of bits to either side of the data stream
def proxy_handler(client_socket, remote_host, remote_port, receive_first):
    # Connect to the remote host
    remote_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    remote_socket.connect((remote_host, remote_port))

    # Receive data from the remote end if necessary
    if receive_first:
        remote_buffer = receive_from(remote_socket)
        hexdump(remote_buffer)

        # Send it to our response handler
        remote_buffer = response_handler(remote_buffer)

        # If we have to send to our local client, send it
        if len(remote_buffer):
            print(f"[<==] Sending {len(remote_buffer)} bytes to local host.")
            client_socket.send(remote_buffer)

    # Now let's loop and read from the local, send to remote, send to local
    while True:
        # Read from the local
        local_buffer = receive_from(client_socket)

        if len(local_buffer):
            print(f"[==>] Received {len(local_buffer)} bytes from localhost.")
            hexdump(local_buffer)

            # Send it to our request handler
            local_buffer = request_handler(local_buffer)

            # Send off the data to the remote host
            remote_socket.send(local_buffer)
            print("[==>] Sent to remote.")

        # Receive back the response
        remote_buffer = receive_from(remote_socket)

        if len(remote_buffer):
            print(f"[<==] Received {len(remote_buffer)} bytes from remote.")
            hexdump(remote_buffer)

            # Send the response to the local socket
            client_socket.send(remote_buffer)
            print("[<===] Sent to localhost.")

        # If no more data on either side, close the connection
        if not len(local_buffer) or not len(remote_buffer):
            client_socket.close()
            remote_socket.close()
            print("[*] No more data. Closing connections.")
            break

# This function sets up the server loop
def server_loop(local_host, local_port, remote_host, remote_port, receive_first):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        server.bind((local_host, local_port))
    except Exception as e:
        print(f"[!!] Failed to listen on {local_host}:{local_port}")
        print("[!!] Check for other listening socket or correct permissions.")
        sys.exit(0)
    print(f"[*] Listening on {local_host}:{local_port}")

    server.listen(5)

    while True:
        client_socket, addr = server.accept()
        print(f"[==>] Received incoming connection from {addr[0]}:{addr[1]}")

        # Start a thread to talk to the remote host
        proxy_thread = threading.Thread(target=proxy_handler, args=(client_socket, remote_host, remote_port, receive_first))
        proxy_thread.start()

def main():
    # No fancy command-line parsing here
    if len(sys.argv[1:]) != 5:
        print("Usage: ./proxy.py [localhost] [localport] [remotehost] [remoteport] [receivefirst]")
        print("Example: ./proxy.py 127.0.0.1 9000 example.com 80 True")
        sys.exit(0)

    # Setup local listening parameters
    local_host = sys.argv[1]
    local_port = int(sys.argv[2])

    # Setup remote target
    remote_host = sys.argv[3]
    remote_port = int(sys.argv[4])

    # This tells our proxy to connect and receive data before sending to the remote host
    receive_first = sys.argv[5].lower() == 'true'

    # Now spin up our listening socket
    server_loop(local_host, local_port, remote_host, remote_port, receive_first)

if __name__ == "__main__":
    main()
