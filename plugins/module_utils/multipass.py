
from .multipass_sdk import MultipassClientSDK 
from .multipass_api import MultipassClientAPI 

def get_existing_mounts(vm_name):
    vm = Multipass().create_client().get_vm(vm_name)
    return vm.info().get('info').get(vm_name).get("mounts")
        

class Multipass:
    def __init__(self, multipass_host="", multipass_user="", multipass_pass="", multipass_cmd="multipass"):
        self.multipass_cmd = multipass_cmd
        self.multipass_host = multipass_host

    def create_client(self):
        if not self.multipass_host:
            return MultipassClientSDK(multipass_cmd=self.multipass_cmd)
        else:
            return MultipassClientAPI(self.multipass_host)