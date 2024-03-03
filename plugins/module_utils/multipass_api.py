from ansible_collections.theko2fi.multipass.plugins.module_utils.haikunator import Haikunator
import requests

class MultipassVM_by_API:
    def __init__(self, vm_name, multipass_host):
        self.vm_name = vm_name
        self.multipass_host = multipass_host
    
    def info(self):
        response = requests.get(url=f"{self.multipass_host}/instances/{self.vm_name}")
        if response.status_code == 200:
            # Assuming the server returns JSON
            return response.json()
        else:
            print("Error occurred. Status code:", response.status_code)
            print("Response content:", response.text)
    
    def start(self):
        return requests.post(url=f"{self.multipass_host}/instances/{self.vm_name}/start")

    def stop(self):
        return requests.post(url=f"{self.multipass_host}/instances/{self.vm_name}/stop")

    def delete(self, purge=False):
        return requests.delete(url=f"{self.multipass_host}/instances/{self.vm_name}", params={'purge': purge})


class MultipassClientAPI:

    def __init__(self, multipass_host):
        self.multipass_host=multipass_host

    def launch(self, vm_name=None, cpu=1, disk="5G", mem="1G", image=None, cloud_init=None):
        if(not vm_name):
            # similar to Multipass's VM name generator
            vm_name = Haikunator().haikunate(token_length=0)
        data = {
            "name": vm_name,
            "cpu": cpu,
            "mem": mem,
            "disk": disk,
            "cloud_init": cloud_init,
            "image": image
        }
        response = requests.post(url=f"{self.multipass_host}/instances", json=data)

        return MultipassVM_by_API(vm_name=vm_name, multipass_host=self.multipass_host)

    def get_vm(self, vm_name):
        return MultipassVM_by_API(vm_name, self.multipass_host)
    
    def recover(self, vm_name):
        return requests.post(url=f"{self.multipass_host}/instances/{vm_name}/recover")