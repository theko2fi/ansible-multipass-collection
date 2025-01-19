
from .multipass_sdk import MultipassClientSDK 
from .multipass_api import MultipassClientAPI 
        

class Multipass:
    def __init__(self, multipass_host="", multipass_user="", multipass_pass="", multipass_cmd="multipass"):
        self.multipass_cmd = multipass_cmd
        self.multipass_host = multipass_host

    def create_client(self):
        if not self.multipass_host:
            return MultipassClientSDK(multipass_cmd=self.multipass_cmd)
        else:
            return MultipassClientAPI(self.multipass_host)