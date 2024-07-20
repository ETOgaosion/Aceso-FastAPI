import os
import glob
import asyncio
from fastapi import FastAPI, WebSocket, Request, HTTPException
from fastapi.templating import Jinja2Templates
from typing import Dict
import random

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


# 根路径
@app.get("/")
def read_root():
    return {"message": "Welcome to noob team!"}


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
    return templates.TemplateResponse("logging_10060.html", {"request": request, "context": {"systemname": systemname, "stagename": stagename, "interval": interval}})


# 运行应用
if __name__ == "__main__":
    import uvicorn
    # 按实际修改主机和端口
    uvicorn.run(app, host="0.0.0.0", port=10060)
