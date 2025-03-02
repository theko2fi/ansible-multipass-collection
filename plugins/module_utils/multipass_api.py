from ansible_collections.theko2fi.multipass.plugins.module_utils.haikunator import Haikunator
from ansible.module_utils.basic import env_fallback
import requests, time
from .errors import SocketError, MountExistsError, MountNonExistentError, MultipassAPIAuthenticationError


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


def basic_auth_argument_spec(spec=None):
    arg_spec = dict(
        multipass_host = dict(type='str', fallback=(env_fallback, ['MULTIPASS_HOST']), aliases=['multipass_url', 'multipass_api_url', 'multipass_api_host']),
        multipass_username = dict(type='str', fallback=(env_fallback, ['MULTIPASS_USERNAME', 'MULTIPASS_USER']), aliases=['multipass_user', 'multipass_api_username', 'multipass_api_user']),
        multipass_password = dict(type='str', no_log=True, fallback=(env_fallback, ['MULTIPASS_PASSWORD', 'MULTIPASS_PASS']), aliases=['multipass_pass', 'multipass_api_password', 'multipass_api_pass']),
        validate_certs=dict(type='bool', default=True, aliases=['tls_verify']),
        ca_cert=dict(type='path', aliases=['tls_ca_cert', 'cacert_path']),
        client_cert=dict(type='path', aliases=['tls_client_cert', 'cert_path']),
        client_key=dict(type='path', aliases=['tls_client_key', 'key_path']),
    )
    if spec:
        arg_spec.update(spec)
    return arg_spec

def get_access_token(base_url, username, password):
    url = f"{base_url}/login/token"
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    data = {
        "username": username,
        "password": password,
        "grant_type": "password"
    }
    
    response = requests.post(url, headers=headers, data=data)
    
    if response.status_code == 200:
        return response.json()["access_token"]
    else:
        raise MultipassAPIAuthenticationError(f'Multipass API authentication failed: {response.json()["detail"]}')

def wait(task_id, timeout=300):

    retry = 0
    while retry <= timeout:
        response = requests.get(
            url=f"http://localhost:9990/api/v0.1.0/tasks/{task_id}/status"
        )
        if response.json()["status"] in ["SUCCESS", "FAILURE"]:
            break
        else:
            time.sleep(1)
            retry = retry + 1


class MultipassVM_by_API:
    def __init__(self, vm_name, multipass_host, headers):
        self.vm_name = vm_name
        self.headers = headers
        self.multipass_host = multipass_host

    def info(self):
        response = requests.get(url=f"{self.multipass_host}/instances/{self.vm_name}", headers=self.headers)
        return APIErrorHandler.handle_error(response, self.vm_name)

    def delete(self, purge=False):
        response = requests.delete(url=f"{self.multipass_host}/instances/{self.vm_name}", headers=self.headers, params={'purge': purge})
        APIErrorHandler.handle_error(response, self.vm_name)
    
    def exec(self, cmd_to_execute, working_directory=""):
        data = {
            "cmd": cmd_to_execute,
            "working_directory": working_directory
        }
        response = requests.post(url=f"{self.multipass_host}/instances/{self.vm_name}/exec", headers=self.headers, json=data)
        response_data = APIErrorHandler.handle_error(response, self.vm_name)
        return response_data["return_code"], response_data["stdout"], response_data["stderr"]
    
    def stop(self):
        response = requests.post(url=f"{self.multipass_host}/instances/{self.vm_name}/stop", headers=self.headers)
        response_data = APIErrorHandler.handle_error(response, self.vm_name)
        try:
            wait(task_id=response_data["task_id"])
        except Exception as e:
            raise Exception(f"Failed to wait for VM to be stopped: {str(e)}")

    def start(self):
        response = requests.post(url=f"{self.multipass_host}/instances/{self.vm_name}/start", headers=self.headers)
        response_data = APIErrorHandler.handle_error(response, self.vm_name)
        try:
            wait(task_id=response_data["task_id"])
        except Exception as e:
            raise Exception(f"Failed to wait for VM to start: {str(e)}")

    def restart(self):
        response = requests.post(url=f"{self.multipass_host}/instances/{self.vm_name}/restart", headers=self.headers)
        response_data = APIErrorHandler.handle_error(response, self.vm_name)
        try:
            wait(task_id=response_data["task_id"])
        except Exception as e:
            raise Exception(f"Failed to wait for VM to restart: {str(e)}")


class MultipassClientAPI:

    def __init__(self, multipass_host, multipass_user, multipass_pass):
        self.multipass_host = multipass_host
        self.multipass_user = multipass_user
        self.multipass_pass = multipass_pass
        self.token = get_access_token(multipass_host, multipass_user, multipass_pass)
        self.headers = {"Authorization": f"Bearer {self.token}"}

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
        response = requests.post(url=f"{self.multipass_host}/instances", headers=self.headers, json=data)
        response_data = APIErrorHandler.handle_error(response)
        wait(task_id=response_data["task_id"])
        return MultipassVM_by_API(vm_name=vm_name, headers=self.headers, multipass_host=self.multipass_host)

    def get_vm(self, vm_name):
        return MultipassVM_by_API(vm_name=vm_name, headers=self.headers, multipass_host=self.multipass_host)
    
    def purge(self):
        response = requests.delete(url=f"{self.multipass_host}/instances/purge", headers=self.headers)
        APIErrorHandler.handle_error(response)

    def list(self):
        response = requests.get(url=f"{self.multipass_host}/instances", headers=self.headers)
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
        response = requests.put(url=f"{self.multipass_host}/instances/{vm_name}/mount", headers=self.headers, json=data)
        APIErrorHandler.handle_error(response, vm_name)

    def umount(self, mount):
        vm_name, *target_path = mount.split(":")
        params = {"target": target_path[0]} if target_path else None
        response = requests.delete(url=f"{self.multipass_host}/instances/{vm_name}/umount", headers=self.headers, params=params)
        APIErrorHandler.handle_error(response, vm_name)

    def recover(self, vm_name):
        response = requests.post(url=f"{self.multipass_host}/instances/{vm_name}/recover", headers=self.headers)
        APIErrorHandler.handle_error(response, vm_name)
    
    def suspend(self):
        pass

    def get(self, key):
        response = requests.get(url=f"{self.multipass_host}/configs/?key={key}", headers=self.headers)
        return APIErrorHandler.handle_error(response)
    
    def get_existing_mounts(self, vm_name):
        vm = self.get_vm(vm_name)
        return vm.info().get('info', {}).get(vm_name, {}).get("mounts", {})