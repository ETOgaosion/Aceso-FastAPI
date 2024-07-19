from pssh.clients import ParallelSSHClient

clientAll = ParallelSSHClient(["192.168.2.11", "192.168.2.20", "192.168.2.21", "192.168.2.22"], pkey="/root/.ssh/id_rsa")
output1 = clientAll.run_command("docker exec -it aceso-ae bash")

clientAll.join()
print(output1)
for host_out in output1:
    for line in host_out.stdout:
        print(line)

output2 = clientAll.run_command("bash /workspace/scripts/aces_gpt_search.sh")

clientAll.join()
print(output2)
for host_out in output2:
    for line in host_out.stdout:
        print(line)
#output_search = clientAll.run_command("")
#
#clientAll.join(output_search)
#print(output_search)
#for host_out in output_search:
#    for line in host_out.stdout:
#        print(line)
#output = clientAll.run_command("uname -a")
#for host_out in output:
#    for line in host_out.stdout:
#        print(line)
