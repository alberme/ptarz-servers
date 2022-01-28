import googleapiclient.discovery
import itertools, asyncio, inspect
from functools import reduce
from uuid import uuid4

from lib.ptarz_servers.enums import ELog, EExit, EInstanceStatus
from lib.ptarz_servers.util import log, spinner, run_compute_resource, reduce_iterable

# onFinish(return_value)
async def compute_task(func, params: list, onFinish=lambda task_result: False):
    result = await func(*params) if inspect.iscoroutinefunction(func) else func(*params)
    onFinish(result)
    
    return result

async def populate_resources(compute, resources: dict):
    loop = asyncio.get_event_loop()
    __compute_instance_funcs__ = [
    {'func': run_compute_resource,\
        'params': [ compute, 'instances', 'list', {'project': 'ptarz-serverz', 'zone': 'us-west2-a'}, lambda instance: instance['name'].startswith(game_prefix) ],\
        'onFinish': lambda result: True  }
    ]
    __compute_disk_funcs__ = [
    {'func': reduce_iterable,\
        'params': [ resources['instance']['disks'], lambda disk: disk['boot'] and log(f"Found boot disk {disk['deviceName']} attached to this serber instance" and True) ],\
        'onFinish': lambda result: True if result else False }
    ]


    compute_disk_tasks = [loop.create_task(compute_task(**func)) for func in __compute_disk_funcs__]

# TODO consider returning EExit enum
async def run(game_prefix: str) -> int:
    loop = asyncio.get_event_loop()
    compute = googleapiclient.discovery.build('compute', 'v1')
    # compute_instance, compute_snapshot, compute_disk, compute_template, compute_instance_status = {}, {}, {}, {}, {}
    resources = {
        'template': {},
        'instance': {},
        'snapshot': {},
        'disk': {},
    }
    # boot disk
    # 
    

    #sdk_installed = bool(os.getenv("Path").find("google-cloud-sdk"))
    
    # search for an existing VM
    # TODO: you will want to decide between preemptible and normal instance in the predicate when its time
    resources['instance'] = await run_compute_resource(compute, 'instances', 'list', {'project': 'ptarz-serverz', 'zone': 'us-west2-a'},\
        lambda instance: instance['name'].startswith(game_prefix))
    
    # create a vm if one does not exist
    if not resources['instance']:
        log(f"Could not find an existing {game_prefix} serber instance, attempting to create one", ELog.WARN)
        log('Searching VM templates', ELog.ACTION)
        # TODO: search game_prefix vm template
    resources['instance']['EInstanceStatus'] = EInstanceStatus[resources['instance']['status']]

    # VM is still being provisioned or booting up, tell user to be patient
    if resources['instance']['EInstanceStatus'] is not EInstanceStatus.TERMINATED\
        or resources['instance']['EInstanceStatus'] is not EInstanceStatus.RUNNING:
        # maybe later you'll wanna create different exit enums based on statuses
        return EExit.SUCCESS
    # VM is running, check status of the server process
    elif resources['instance']['EInstanceStatus'] is EInstanceStatus.RUNNING:
        pass
        # call a function to ssh and check the server status
    # VM is in terminated state, use this VM as the server
    else:
        log(f"Using server instance {resources['instance']['name']}", logtype=ELog.ACTION)

    # TODO: lets try and use asyncio.Tasks to loop find a compute disk
    # pretty much run the tasks and the loop must return a compute disk from future.result()



    # # check for a boot disk on instance
    # if 'disks' in compute_instance:
    #     log(f"Checking for attached boot disk on {compute_instance['name']}", logtype=ELog.ACTION)
    #     compute_disk = reduce_iterable(compute_instance['disks'],\
    #         lambda disk: disk['boot'] and log(f"Found boot disk {disk['deviceName']} attached to this serber instance" and True))
    #     # for disk in compute_instance['disks']:
    #     #     # another edge case, the boot disk doesnt start with game_prefix
    #     #     if disk.boot and disk.deviceName.startswith(game_prefix):
    #     #         log('Found %s persistent boot disk attached to this serber instance' % game_prefix)
    #     #         compute_disk = disk
    #     #         break

    # # no boot disk found attached, search for an existing detached boot disk
    # if not compute_disk:
    #     log(f"No boot disk found attached to {compute_instance['name']}")
    #     log(f"Searching for a detached {game_prefix} boot disk", logtype=ELog.ACTION)
    #     # disks = list_resource(compute, 'disks', {'project': 'ptarz-serverz', 'zone': 'us-west2-a'})
    #     compute_disk = get_resource(compute, 'disks', {'project': 'ptarz-serverz', 'zone': 'us-west2-a'},\
    #         lambda disk: disk.name.startswith(f"{game_prefix}-boot") and not 'name' in disk)

    #     # if 'disks' in disks:
    #         # also gonna wanna check the users attr
    #         # compute_disk = reduce(lambda result, disk: disk if not result and disk.name.startswith(f"{game_prefix}-boot") else result,
    #         #     compute_instance['disks'], {})
    #         # for disk in disks:
    #         #     if disk.deviceName.startswith(game_prefix):
    #         #         log('Found %s persistent boot disk attached to this serber instance' % game_prefix)
    #         #         compute_disk = disk
    #         #         break
    # # no detached disk found in disks pool
    # if not compute_disk:
    #     log(f"No detached {game_prefix} boot disk found")
    #     # find a snapshot
    #     log('Searching for a %s snapshot' % game_prefix, ELog.ACTION)
    #     # edit this one further
    #     compute_snapshot = get_resource(compute, 'snapshots', {'project': 'ptarz-serverz', 'zone': 'us-west2-a'},\
    #         lambda snapshot: snapshot['name'].startswith(game_prefix))
    #     if compute_snapshot:
    #         log(f"Creating a {game_prefix} boot disk from snapshot {compute_snapshot['name']}")
    #         response = create_resource(compute, 'disks',\
    #             {'project': 'ptarz-serverz', 'zone': 'us-west2-a', 'name': f"{game_prefix}-boot-disk", 'sourceSnapshot': f"global/snapshots/{compute_snapshot['name']}"})
            
    # else:
    #     log(f"Found {compute_disk['name']} detached")
    #     log(f"Attaching {compute_disk['name']} to server instance {compute_instance['name']}", logtype=ELog.ACTION)
