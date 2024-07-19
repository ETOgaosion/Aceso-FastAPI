from pssh.clients import ParallelSSHClient, SSHClient

clientAll = ParallelSSHClient(["192.168.2.11", "192.168.2.20", "192.168.2.21", "192.168.2.22"], pkey="/root/.ssh/id_rsa")
output_search = clientAll.run_command("nvidia-smi")
client11 = SSHClient("192.168.2.11", pkey="/root/.ssh/id_rsa")

clientAll.join()
print(output_search)
for host_out in output_search:
    for line in host_out.stdout:
        print(line)

#output_search = clientAll.run_command("")
#
clientAll.join(output_search)
#print(output_search)
#for host_out in output_search:
#    for line in host_out.stdout:
#        print(line)
output = clientAll.run_command("uname -a")
for host_out in output:
    for line in host_out.stdout:
        print(line)

output = client11.run_command("nvidia-smi")
for line in output.stdout:
    print(line)
