from pssh.clients import ParallelSSHClient 

hosts = ['192.168.2.11', '192.168.2.11', '192.168.2.11', '192.168.2.11']
client = ParallelSSHClient(hosts, "root", pkey="~/.ssh/id_rsa")
cmd = 'uname'

output = client.run_command(cmd)
for host_out in output:
    for line in host_out.stdout:
        print(line)
