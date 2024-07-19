import os
import time
import glob
import threading
from typing import Optional
from fastapi import FastAPI, HTTPException
from pssh.clients import ParallelSSHClient, SSHClient
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.responses import PlainTextResponse
from multiprocessing import Process, Value
import asyncio
from fastapi import FastAPI, WebSocket, Request, HTTPException
from fastapi.templating import Jinja2Templates
from typing import Dict
import random

# 定义远程主机列表和凭据(多主机)
hosts = ["192.168.2.11", "192.168.2.20", "192.168.2.21", "192.168.2.22"]
client = ParallelSSHClient(hosts, pkey="/root/.ssh/id_rsa")

# 多主机并行定义
client11_20 = ParallelSSHClient(["192.168.2.11", "192.168.2.20"], pkey="/root/.ssh/id_rsa")
clientAll = ParallelSSHClient(["192.168.2.11", "192.168.2.20", "192.168.2.21", "192.168.2.22"], pkey="/root/.ssh/id_rsa")
# 单主机定义
#(client11, client20, client21, client22) = (paramiko.SSHClient(), paramiko.SSHClient(), paramiko.SSHClient(), paramiko.SSHClient())
client11 = SSHClient("192.168.2.11", pkey="/root/.ssh/id_rsa")
client20 = SSHClient("192.168.2.20", pkey="/root/.ssh/id_rsa")
client21 = SSHClient("192.168.2.21", pkey="/root/.ssh/id_rsa")
client22 = SSHClient("192.168.2.22", pkey="/root/.ssh/id_rsa")


app = FastAPI()
templates = Jinja2Templates(directory="templates")

# 不同的systemname和stagename对应不同的日志路径
LOG_PATHS: Dict[str, Dict[str, str]] = {
    "aceso": {
        "profile": "/root/project/SuperScaler-InfoSuperBahn/profiler/profiled-time-eurosys-new/",
        "search": "/root/project/SuperScaler-InfoSuperBahn/logs/aceso/search/gpt/1_3B/",
        "train": "/root/project/SuperScaler-InfoSuperBahn/logs/aceso/runtime/gpt/1_3B/",
    },
    "megatron": {
        "search": "/root/project/SuperScaler-InfoSuperBahn/logs/megatron/search/gpt/1_3B/",
        "train": "/root/project/SuperScaler-InfoSuperBahn/logs/megatron/runtime/gpt/1_3B/",
    },
    "alpa": {
        "search": "/root/project/SuperScaler-InfoSuperBahn/logs/alpa/search/gpt/1_3B/",
        "train": "/root/project/SuperScaler-InfoSuperBahn/logs/alpa/search/gpt/1_3B/",
    },
}

# 默认间隔时间（秒）
DEFAULT_INTERVAL = 1

DEBUG=True

def print_output(output):
    print(output)
    for line in output.stdout:
        print(line)
    for line in output.stderr:
        print(line)

def debug(client, output):
    if DEBUG:
        client.wait_finished(output)
        print_output(output)

def wait(client, output):
    client.wait_finished(output)
    print_output(output)

def debug_multiple(clients, outputs):
    if DEBUG:
        clients.join()
        for output in outputs:
            print_output(output)

def wait_multiple(clients, outputs):
    clients.join()
    for output in outputs:
        print_output(output)

#def check_output_arr():
#    for output in output_arr:

# 根路径
@app.get("/")
def run_root():
    return {"message": "Welcome to noob team!"}


# 获取clusterinfo
@app.get("/clusterinfo", response_class=PlainTextResponse)
def run_clusterinfo():
    output = ""
    clusterinfo_output = clientAll.run_command("lscpu && nvidia-smi")
    for idx, host_out in enumerate(clusterinfo_output):
        output += f'{hosts[idx]} lscpu && nvidia-smi:'
        for line in host_out.stdout:
            output += line + '\n'
    return output


# ================== Aceso ====================

# ------ Profile ------

def run_aceso_profile_proccess():
    # 执行命令
    # profile_large_dist_p2p.sh两个节点跑
    # profile_large_gpt.sh一个节点跑

    outputs = client11_20.run_command('docker exec aceso-ae bash -c "cd profiler && ./scripts/profile_large_dist_p2p.sh"')
    debug_multiple(client11_20, outputs)
    output = client11.run_command('docker exec aceso-ae bash -c "cd profiler && ./scripts/profile_large_gpt.sh"')
    debug(client11, output)

def run_aceso_profile_common():
    Process(target=run_aceso_profile_proccess).start()
    return {"aceso_profile": True}

@app.get("/run/aceso/profile")
def run_aceso_profile_get(modelsize: str | None = "all"):
    return run_aceso_profile_common()

@app.post("/run/aceso/profile/")
def run_aceso_profile_post(modelsize: str | None = "all"):
    return run_aceso_profile_common()

# ------ Search ------

def run_aceso_search_process():
    # 执行命令
    output = client11.run_command("scp -r /root/project/SuperScaler-InfoSuperBahn/profiler/profiled-time-eurosys-new/ 192.168.2.20:/root/project/SuperScaler-InfoSuperBahn/profiler/profiled-time-eurosys-new/")
    debug(client11, output)
    output = client11.run_command("scp -r /root/project/SuperScaler-InfoSuperBahn/profiler/profiled-time-eurosys-new/ 192.168.2.21:/root/project/SuperScaler-InfoSuperBahn/profiler/profiled-time-eurosys-new/")
    debug(client11, output)
    output = client11.run_command("scp -r /root/project/SuperScaler-InfoSuperBahn/profiler/profiled-time-eurosys-new/ 192.168.2.22:/root/project/SuperScaler-InfoSuperBahn/profiler/profiled-time-eurosys-new/")
    debug(client11, output)

    outputs = clientAll.run_command('docker exec aceso-ae bash -c "./scripts/aceso_gpt_search.sh"')
    debug_multiple(clientAll, outputs)

def run_aceso_search_common():
    Process(target=run_aceso_search_process).start()
    return {"aceso_search": True}

@app.get("/run/aceso/search")
def run_aceso_search_get(modelsize: str | None = "all"):
    return run_aceso_profile_common()

@app.post("/run/aceso/search/")
def run_aceso_search_post(modelsize: str | None = "all"):
    return run_aceso_profile_common()

# ------ Train ------

def run_aceso_train_process():
    outputs = clientAll.run_command('docker exec aceso-ae bash -c "./scripts/aceso_gpt_execute.sh"')
    debug_multiple(clientAll, outputs)

def run_aceso_train_common():
    Process(target=run_aceso_train_process).start()
    # run_aceso_train_process()
    return {"aceso_train": True}

@app.get("/run/aceso/train")
def run_aceso_train_get(modelsize: str | None = "all"):
    return run_aceso_train_common()

@app.post("/run/aceso/train/")
def run_aceso_train_post(modelsize: str | None = "all"):
    return run_aceso_train_common()

# ================== Megatron ====================

# ------ Search ------

def run_megatron_search_process():
    # 执行命令
    outputs = clientAll.run_command('docker exec aceso-ae bash -c "./scripts/megatron_gpt_search.sh"')
    debug_multiple(clientAll, outputs)

def run_megatron_search_common():
    Process(target=run_megatron_search_process).start()
    return {"megatron_search": True}

@app.get("/run/megatron/search")
def run_megatron_search_get(modelsize: str | None = "all"):
    return run_megatron_search_common()

@app.post("/run/megatron/search/")
def run_megatron_search_post(modelsize: str | None = "all"):
    return run_megatron_search_common()

# ------ Train ------

def run_megatron_train_process():
    # 执行命令
    outputs = clientAll.run_command('docker exec aceso-ae bash -c "./scripts/megatron_gpt_execute.sh"')
    debug_multiple(clientAll, outputs)

def run_megatron_train_common():
    Process(target=run_megatron_train_process).start()
    return {"megatron_train": True}
    
@app.get("/run/megatron/train")
def run_megatron_train_get(modelsize: str | None = "all"):
    return run_megatron_train_common()

@app.post("/run/megatron/train/")
def run_megatron_train_post(modelsize: str | None = "all"):
    return run_megatron_train_common()


# ================== Alpa ====================

# ------ Profile ------

def run_alpa_profile_process():
    # 执行命令
    outputs = clientAll.run_command('docker exec aceso-ae bash -c "cd external/alpa && python3 gen_prof_database.py --max-comm-size-intra-node 0 --max-comm-size-inter-node 4"')
    debug_multiple(clientAll, outputs)

def run_alpa_profile_common():
    Process(target=run_alpa_profile_process).start()
    return {"alpa_profile": True}

@app.get("/run/alpa/profile")
def run_alpa_profile_get(modelsize: str | None = "all"):
    return run_alpa_profile_common()

@app.post("/run/alpa/profile/")
def run_alpa_profile_post(modelsize: str | None = "all"):
    return run_alpa_profile_common()

# ------ Search ------

def run_alpa_search_process():
    outputs = clientAll.run_command('docker exec aceso-ae bash -c ".scripts/alpa_gpt_search_execute.sh"')
    debug_multiple(clientAll, outputs)

def run_alpa_search_common():
    Process(target=run_alpa_search_process).start()
    return {"alpa_search": True}

@app.get("/run/alpa/search")
def run_alpa_search_get(modelsize: str | None = "all"):
    return run_alpa_search_common()

@app.post("/run/alpa/search/")
def run_alpa_search_post(modelsize: str | None = "all"):
    return run_alpa_search_common()

# ------ Train ------

def run_alpa_train_process():
    outputs = clientAll.run_command('docker exec aceso-ae bash -c ".scripts/alpa_gpt_search_execute.sh"')
    debug_multiple(clientAll, outputs)

def run_alpa_train_common():
    Process(target=run_alpa_train_process).start()
    return {"alpa_train": True}

@app.get("/run/alpa/train")
def run_alpa_train_get(modelsize: str | None = "all"):
    return run_alpa_train_common()

@app.post("/run/alpa/train/")
def run_alpa_train_post(modelsize: str | None = "all"):
    return run_alpa_train_common()

# ======================= cancel =========================
def cancel_common():
    outputs = clientAll.run_command('pkill -9 aceso*')
    wait_multiple(clientAll, outputs)
    outputs = clientAll.run_command('pkill -9 alpa*')
    wait_multiple(clientAll, outputs)
    outputs = clientAll.run_command('pkill -9 megatron*')
    wait_multiple(clientAll, outputs)
    outputs = clientAll.run_command('pkill -9 python')
    wait_multiple(clientAll, outputs)
    return {"cancel": True}

@app.get("/cancel")
def cancel_get():
    return cancel_common()

@app.post("/cancel")
def cancel_post():
    return cancel_common()

# ======================= Logging =========================


def find_latest_file(log_dir_path: str, file_regex: str) -> str:
    files = glob.glob(log_dir_path + file_regex)
    latest_file = max(files, key=os.path.getctime)
    return latest_file


def get_log_path(systemname: str, stagename: str) -> str:
    if systemname in LOG_PATHS and stagename in LOG_PATHS[systemname]:
        log_dir_path = LOG_PATHS[systemname][stagename]
        if systemname == "aceso":
            match stagename:
                case "profile":
                    log_dir_path += "profiling_gpt_op_tp1.log"
                case "search":
                    log_dir_path = find_latest_file(log_dir_path, "*.log")
                case "train":
                    log_dir_path = find_latest_file(log_dir_path, "full_log*")
        elif systemname == "megatron":
            match stagename:
                case "search":
                    log_dir_path = find_latest_file(log_dir_path, "*.log")
                case "train":
                    log_dir_path = find_latest_file(log_dir_path, "full_log*")
        elif systemname == "alpa":
            match stagename:
                case "search":
                    log_dir_path = find_latest_file(log_dir_path, "*.log")
                case "train":
                    log_dir_path = find_latest_file(log_dir_path, "*.log")
        return log_dir_path
    else:
        raise HTTPException(status_code=404, detail="Log path not found ")

def change_enter_key(lines):
    for i in range(len(lines)):
        if lines[i][-1] == '\n':
            lines[i] = lines[i][: -1] + '<br>'
    return lines


async def read_log_file(path: str, last_lines: int = 0):
    with open(path, 'r') as file:
        lines = file.readlines()
        new_lines = change_enter_key(lines[last_lines:])
        return new_lines, len(lines)


async def read_log_file_directly(path: str, last_lines: int = 0):
    print("hit")
    with open(path, 'r') as file:
        lines = file.readlines()
        tmp_end  = last_lines + random.randint(1, 4) * 4
        end = tmp_end if tmp_end < len(lines) else len(lines)
        new_lines = change_enter_key(lines[last_lines: end])
        return new_lines, len(lines)


async def read_log_test_file(path: str, last_lines: int = 0):
    with open(path, 'r') as file:
        lines = file.readlines()
        new_lines = change_enter_key(lines[last_lines:])
        print(new_lines)
        return new_lines, len(lines)


@app.websocket("/logws/{systemname}/{stagename}/{interval}")
async def websocket_endpoint_log(websocket: WebSocket,
                                 systemname: str,
                                 stagename: str,
                                 interval: int = 1):
    await websocket.accept()
    print(f'systemname: {systemname}, stagename: {stagename}')
    # 跟踪日志行数
    lines = 0
    log_file_path = get_log_path(systemname, stagename)
    print(log_file_path)
    try:
        while True:
            if systemname == "alpa":
                logs, lines = await read_log_file_directly(log_file_path, lines)
            else:
                logs, lines = await read_log_file(log_file_path, lines)
            if logs:
                await websocket.send_text(logs)
            if interval > 0:
                await asyncio.sleep(interval)
            else:
                break
    except Exception as e:
        print(e)
    finally:
        await websocket.close()


@app.websocket("/logtest")
async def websocket_test(websocket: WebSocket):
    print('hit')
    await websocket.accept()
    # 跟踪日志行数
    lines = 0
    log_file_path = 'test.txt'
    try:
        while True:
            logs, lines = await read_log_test_file(log_file_path, lines)
            if logs:
                await websocket.send_text(logs)
            await asyncio.sleep(1)
    except Exception as e:
        print(f'error: {e}')
    finally:
        await websocket.close()


@app.get("/log/{systemname}/{stagename}/{interval}")
def read_log(request: Request, systemname: str, stagename: str, interval: int = 1):
    return templates.TemplateResponse("logging.html", {"request": request, "context": {"systemname": systemname, "stagename": stagename, "interval": interval}})



# 获取结果
@app.get("/result")
def run_result():
    return FileResponse('/root/project/SuperScaler-InfoSuperBahn/figures/fig7a.png')

# 运行应用
if __name__ == "__main__":
    import uvicorn
    # 按实际修改主机和端口
    uvicorn.run(app, host="0.0.0.0", port=10060)