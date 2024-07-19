import paramiko

# Define the server and credentials
hostname = '192.168.2.20'
port = 22
username = 'root'
key_path = '/root/.ssh/id_rsa'

# Create an SSH client
ssh = paramiko.SSHClient()

# Automatically add the server's host key
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

try:
    # Load the private key
    private_key = paramiko.RSAKey.from_private_key_file(key_path)

    # Connect to the server using the private key
    ssh.connect(hostname, port, username, pkey=private_key)

    # Execute a command on the remote server
    stdin, stdout, stderr = ssh.exec_command('ls -l')

    # Read the command's output
    print(stdout.read().decode())
except Exception as e:
    print(f"An error occurred: {e}")
finally:
    # Close the connection
    ssh.close()

