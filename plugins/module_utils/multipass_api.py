from ansible_collections.theko2fi.multipass.plugins.module_utils.haikunator import Haikunator
import requests, time
from .errors import SocketError, MountExistsError, MountNonExistentError


class APIClient:
    pass

class APIErrorHandler:

    @staticmethod
    def handle_error(response, vm_name=None):
        """
        Handles errors from API responses.
        Args:
            response: The response object from the API.
            vm_name: Optional; Name of the VM for context in error messages.
        Raises:
            Appropriate exceptions based on the response error message.
        """
        if response.status_code == 200:
            return response.json()
        
        err_msg = response.json().get("message", "An unknown error occurred.")
        
        if vm_name and f'instance "{vm_name}" does not exist' in err_msg:
            raise NameError(err_msg)
        elif "Socket error" in err_msg:
            raise SocketError(err_msg)
        elif "is already mounted" in err_msg:
            raise MountExistsError(err_msg)
        elif "is not mounted" in err_msg:
            raise MountNonExistentError(err_msg)
        else:
            raise Exception(err_msg)

def wait(task_id, timeout=300):

    retry = 0
    while retry <= timeout:
        response = requests.get(
            url=f"http://localhost:9990/status",
            params={"task_id": task_id}
        )
        if response.json()["status"] in ["SUCCESS", "FAILURE"]:
            break
        else:
            time.sleep(1)
            retry = retry + 1


class MultipassVM_by_API:
    def __init__(self, vm_name, multipass_host):
        self.vm_name = vm_name
        self.multipass_host = multipass_host

    def info(self):
        response = requests.get(url=f"{self.multipass_host}/instances/{self.vm_name}")
        return APIErrorHandler.handle_error(response, self.vm_name)

    def delete(self, purge=False):
        response = requests.delete(url=f"{self.multipass_host}/instances/{self.vm_name}", params={'purge': purge})
        APIErrorHandler.handle_error(response, self.vm_name)

    def stop(self):
        response = requests.post(url=f"{self.multipass_host}/instances/{self.vm_name}/stop")
        APIErrorHandler.handle_error(response, self.vm_name)

    def start(self):
        response = requests.post(url=f"{self.multipass_host}/instances/{self.vm_name}/start")
        response_data = APIErrorHandler.handle_error(response, self.vm_name)
        try:
            wait(task_id=response_data["task_id"])
        except Exception as e:
            raise Exception(f"Failed to wait for VM to start: {str(e)}")

    def restart(self):
        response = requests.post(url=f"{self.multipass_host}/instances/{self.vm_name}/restart")
        APIErrorHandler.handle_error(response, self.vm_name)


class MultipassClientAPI:

    def __init__(self, multipass_host):
        self.multipass_host = multipass_host

    def launch(self, vm_name=None, cpu=1, disk="5G", mem="1G", image=None, cloud_init=None):
        if not vm_name:
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
        response_data = APIErrorHandler.handle_error(response)
        wait(task_id=response_data["task_id"])
        return MultipassVM_by_API(vm_name=vm_name, multipass_host=self.multipass_host)

    def get_vm(self, vm_name):
        return MultipassVM_by_API(vm_name, self.multipass_host)
    
    def purge(self):
        pass

    def list(self):
        response = requests.get(url=f"{self.multipass_host}/instances")
        return APIErrorHandler.handle_error(response)

    def find(self):
        pass

    def mount(self, src, target, mount_type='classic', uid_maps=[], gid_maps=[]):
        vm_name, target_path = target.split(":")
        data = {
            "source": src,
            "target": target_path,
            "uid_map": uid_maps,
            "gid_map": gid_maps
        }
        response = requests.put(url=f"{self.multipass_host}/instances/{vm_name}/mount", json=data)
        APIErrorHandler.handle_error(response, vm_name)

    def umount(self, mount):
        vm_name, *target_path = mount.split(":")
        params = {"target": target_path[0]} if target_path else None
        response = requests.delete(url=f"{self.multipass_host}/instances/{vm_name}/umount", params=params)
        APIErrorHandler.handle_error(response, vm_name)

    def recover(self, vm_name):
        response = requests.post(url=f"{self.multipass_host}/instances/{vm_name}/recover")
        APIErrorHandler.handle_error(response, vm_name)
    
    def suspend(self):
        pass

    def get(self, key):
        response = requests.get(url=f"{self.multipass_host}/configs/?key={key}")
        return APIErrorHandler.handle_error(response)
    
    def get_existing_mounts(self, vm_name):
        vm = self.get_vm(vm_name)
        return vm.info().get('info', {}).get(vm_name, {}).get("mounts", {})