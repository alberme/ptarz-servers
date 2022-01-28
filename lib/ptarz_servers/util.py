import os, sys, itertools, asyncio
from socket import timeout as SocketTimeout
from functools import reduce
from uuid import uuid4
from pprint import pformat
from colorama import init, Fore, Style

from googleapiclient.discovery import Resource
from googleapiclient.http import HttpRequest
from googleapiclient.errors import UnknownApiNameOrVersion

from lib.ptarz_servers.enums import ELog, EOperationStatus

init(autoreset = True)

### gcloud compute wrapper functions ###

async def run_compute_resource(compute: Resource, resource_name: str, action_name: str, params: dict, list_predicate=None) -> asyncio.Future:
    response = await http_request(compute, resource_name, action_name, params)
    if response['EOperationStatus'] is not EOperationStatus.DONE:
        await wait_for_operation(compute, {**params, 'operation': response['id']})
    elif action_name.lower().endswith('list'):
        items = response['items'] if 'items' in response else []
        response = reduce_iterable(items, list_predicate) if items and list_predicate else items

    return response

# this is where you will introduce the spinner animation, or maybe not
# scope can be zone, region, global
async def wait_for_operation(compute: Resource, params: dict) -> asyncio.Future:
    valid_params = ['project', 'zone', 'operation']
    e_operation_status = EOperationStatus.PENDING
    # remove unnecessary params
    for param in list(params.keys()):
        if param not in valid_params:
            del params[param]
    
    while e_operation_status is not EOperationStatus.DONE:
        log('Waiting for operation to complete')
        response = await http_request(compute, f"{'zone' if 'zone' in params else 'global'}Operations", 'wait', params)
        e_operation_status = response['EOperationStatus']
    log('Operation complete')

### utility functions ###
async def http_request(compute: Resource, resource_name: str, action_name: str, params: dict, attempts=2):
    loop = asyncio.get_event_loop()
    response = {}
    
    try:
        resource: Resource = getattr(compute, resource_name)()
        if not resource_name.endswith('Operations')\
            and 'GET' not in resource._resourceDesc['methods'][action_name].values()\
            and 'requestId' not in params:
                params['requestId'] = str(uuid4())
        action: HttpRequest = getattr(resource, action_name)(**params)
        
    except (AttributeError, KeyError):
        log(f"Invalid resource name or action passed: {resource_name}.{action_name}", logtype=ELog.ERROR)
        raise UnknownApiNameOrVersion()
    
    while not response and attempts >= 0:
        try:
            response = await loop.run_in_executor(None, lambda: action.execute())
            response['EOperationStatus'] = EOperationStatus(response['status']) if 'progress' in response else EOperationStatus.DONE
        except SocketTimeout:
            #TODO: reduce timeout time
            log('Timeout, retrying request', logtype=ELog.WARN)
            attempts -= 1
    
    return response

def reduce_iterable(source_iter, predicate) -> dict:
    return reduce(lambda result, resource: resource if not result and predicate(resource) else result, source_iter, {})

# parse newlines 
def log(*messages, logtype=ELog.INFO):
    prefix = logtype.value
    messages = [parsed_message for message in messages for parsed_message in pformat(message).strip('\'').split('\n')]
    whitespace_length = 8
    
    for message in messages:
        padding = len(message) + (whitespace_length - len(prefix['str']))
        print(prefix['color'] + prefix['style'] + prefix['str'] + Fore.WHITE + message.rjust(padding))
    
async def spinner(task, message: str, interval: float):
    done = False

    spinner = itertools.cycle(['-', '/', '|', '\\'])
    sys.stdout.write(f"{message}... ")

    while not done:
        try:
            sys.stdout.write(next(spinner))   # write the next character
            sys.stdout.flush()                # flush stdout buffer (actual character display)
            done = await task()
            if done:
                sys.stdout.write('done\n')
            else:
                await asyncio.sleep(interval)
            sys.stdout.write('\b')            # erase the last written char

            if done:
                sys.stdout.write('done\n')
        except KeyboardInterrupt:
            exit(0)