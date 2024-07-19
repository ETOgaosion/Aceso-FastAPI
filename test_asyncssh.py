import asyncio, asyncssh, sys

async def run_client():
    async with asyncssh.connect('192.168.2.21', username="root", client_keys=["/root/.ssh/id_rsa"], known_hosts=None) as conn:
        result = await conn.run('echo "Hello!"', check=True)
        print(result.stdout, end='')

try:
    asyncio.get_event_loop().run_until_complete(run_client())
except (OSError, asyncssh.Error) as exc:
    sys.exit('SSH connection failed: ' + str(exc))
