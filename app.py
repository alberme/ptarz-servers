# Copyright: Albert Martinez
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files

# pip install -r requirements.txt

import traceback, os, subprocess, asyncio
from sys import version_info
from glob import glob
from pprint import pformat
from contextlib import suppress
from typing import List

from lib.ptarz_servers.enums import ELog, EExit
from lib.ptarz_servers.util import log, run_compute_resource, reduce_iterable

import googleapiclient.discovery
from googleapiclient.errors import HttpError
# from ptars_servers.server import runs

def init() -> int:
    if version_info <= (3,5,0):
        log("You are using a non-supported version of python", logtype=ELog.ERROR)
        exit(1)
    try:
        import googleapiclient
        log("found gcloud API")
    except ImportError:
        log("gcloud API package not installed, installing now", logtype=ELog.WARN)
        return_code = subprocess.call(["pip", "install", "google-api-python-client"])
        log(return_code)

    auth_path = glob(os.path.join(os.getcwd(), 'auth/ptars-servers*.json'))
        
    if not bool(auth_path):
        log("Authentication file was not found, exiting", logtype=ELog.ERROR)
        done(1)
    else:
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = auth_path.pop()

def done(exit_code: EExit, exception=None):
    if exit_code is not EExit.SUCCESS:
        log('Something went wrong.%s' % ('\n\n'+traceback.format_exc() if bool(exception) else ''), logtype=ELog.ERROR)
    else:
        log('Server is now booting up', logtype=ELog.DONE)
    exit(exit_code)

async def test(compute):
    loop = asyncio.get_event_loop()
    __compute_disk_funcs__ = [
        # {
        # 'func': reduce_iterable,
        # 'params': [compute, 'disks', {'project': 'ptars-servers', 'zone': 'us-west2-a'},\
        #     lambda disk: disk.name.startswith(f"sdtd-boot") and not 'name' in disk],
        # 'onFinish': lambda result: True
        #     reduce_iterable(compute_instance['disks'],\
        #     lambda disk: disk['boot'] and log(f"Found boot disk {disk['deviceName']} attached to this serber instance" and True))
        # },
        {
        'func': run_compute_resource,
        'params': [compute, 'disks', 'list', {'project': 'ptars-servers', 'zone': 'us-west2-a'},\
            lambda disk: disk.name.startswith(f"sdtd-boot") and not 'name' in disk],
        'onFinish': lambda disk: f"Found disk {disk['name']}" if disk else "Found no sdtd disks"
        },
        {
        'func': run_compute_resource,
        'params': [compute, 'snapshots', 'list', {'project': 'ptars-servers'},\
            lambda snap: snap['name'].startswith('sdtd')],
        'onFinish': lambda snap: f"Found disk {snap['name']}" if snap else "Found no sdtd snaps"
        }
    ]
    compute_disk_tasks: List[asyncio.Task] = [loop.create_task(compute_task(**func)) for func in __compute_disk_funcs__]
    result: List[tuple] = await asyncio.gather(*compute_disk_tasks)
    
    for task_res, finish_res in result:
        log(f"({task_res},{finish_res})")
    # lets just use gather and let all the tasks run

    # compute_snapshot = await run_compute_resource(compute, 'snapshots', 'list', {'project': 'ptars-servers'}, lambda snap: snap['name'].startswith('sdtd'))
    # log(f"found {compute_snapshot['name']}" if compute_snapshot else 'no snap found', logtype=ELog.ACTION)
    # disk_res = await run_compute_resource(compute, 'disks', 'insert', {'project': 'ptars-servers', 'zone': 'us-west2-a', 'body': {'name': 'test-disk' ,'sourceSnapshot': F"global/snapshots/{compute_snapshot['name']}"}})
    # # result = await run_api_resource(compute, 'zoneOperations', 'wait', {'project': 'ptars-servers', 'zone': 'us-west2-a', 'operation': disk_res['id']})
    # log(disk_res)

# onFinish(return_value)
async def compute_task(func, params: list, onFinish=lambda task_result: None):
    import inspect
    
    task_result = await func(*params) if inspect.iscoroutinefunction(func) else func(*params)
    callback_result = onFinish(task_result)
    
    return (task_result, callback_result)

async def sleep(id):
    await asyncio.sleep(2+id)
    log(f"awake with id {id}")

    return id

if __name__ == "__main__":
    try:        
        init()
        compute = googleapiclient.discovery.build('compute', 'v1')
        asyncio.run(test(compute))
        # run("sdtd") # youre gonna wanna grab the prefix name from cmd args
    except asyncio.CancelledError as e:
        log(e)
    except Exception as e:
        done(EExit.FAILURE, e)
        