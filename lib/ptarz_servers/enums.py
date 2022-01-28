from enum import Enum
from colorama import init, Fore, Style

class ELog(Enum):
    INFO = {'str': 'INFO', 'color': Fore.GREEN, 'style': Style.NORMAL}
    ERROR = {'str': 'ERR', 'color': Fore.RED, 'style': Style.BRIGHT}
    WARN = {'str': 'WARN', 'color': Fore.YELLOW, 'style': Style.BRIGHT}
    DONE = {'str': 'DONE', 'color': Fore.GREEN, 'style': Style.BRIGHT}
    ACTION = {'str': '----->', 'color': Fore.CYAN, 'style': Style.BRIGHT}

class EExit(Enum):
    SUCCESS = 0
    FAILURE = 1

class EInstanceStatus(Enum):
    PROVISIONING = {'message': 'A {prefix} server instance {instance_name} with IP {instance_ip} is currently provisioning server resources\nPls be patient. Shintel parts are being made',\
        'log_type': ELog.WARN}
    STAGING = {'message': 'A {prefix} server instance {instance_name} with IP {instance_ip} is currently booting up\nPls be patient. It can take a few minutes to boot up',\
        'log_type': ELog.WARN}
    # for running, we can probably ssh in or expose an api to determine true server status, so its not done yet 
    RUNNING = {'message': 'A {prefix} server instance {instance_name} with IP {instance_ip} is currently running',\
        'log_type': ELog.INFO}
    STOPPING = {'message': 'A {prefix} server instance {instance_name} with IP {instance_ip} is currently stopping.\nIt might have crashed or the hypervisor might have demanded it be shutdown\nU can try running this kiddie script again after a minute or check the status using the console command: gcloud compute instances --filter="name:({prefix})"',\
        'log_type': ELog.WARN}
    REPAIRING = {'message': '',\
        'log_type': ELog.WARN}
    TERMINATED = {'message': '',\
        'log_type': ELog.INFO}

class EDiskStatus(Enum):
    READY = {'message': '{}',\
        'log_type': ELog.INFO}
    UPLOADING = {'message': '{}',\
        'log_type': ELog.INFO}
    CREATING = {'message': '{}',\
        'log_type': ELog.INFO}
    RESTORING = {'message': '{}',\
        'log_type': ELog.INFO}
    FAILED = {'message': '{}',\
        'log_type': ELog.INFO}
    DELETING = {'message': '{}',\
        'log_type': ELog.INFO}

class EOperationStatus(Enum):
    DONE = 'DONE'
    PENDING = 'PENDING'
    RUNNING = 'RUNNING'

# The status of disk creation. 

# READY
# UPLOADING
# CREATING: Disk is provisioning. 
# RESTORING: Source data is being copied into the disk.
# FAILED: Disk creation failed. READY: Disk is ready for use. 
# DELETING: Disk is deleting.
