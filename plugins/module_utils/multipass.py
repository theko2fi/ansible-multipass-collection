import subprocess

from ansible_collections.theko2fi.multipass.plugins.module_utils.haikunator import Haikunator
import os
import json
import time
from shlex import split as shlexsplit
from .errors import SocketError, MountNonExistentError, MountExistsError

def get_existing_mounts(vm_name):
    vm = MultipassClient().get_vm(vm_name)
    return vm.info().get('info').get(vm_name).get("mounts")

# Added decorator to automatically retry on unpredictable module failures
def retry_on_failure(ExceptionsToCheck, max_retries=5, delay=5, backoff=2):
    def decorator(func):
        def wrapper(*args, **kwargs):
            mdelay = delay
            for _ in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except ExceptionsToCheck as e:
                    print(f"Error occurred: {e}. Retrying...")
                    time.sleep(delay)
                    mdelay *= backoff
            return func(*args, **kwargs)
        return wrapper
    return decorator


class MultipassVM:
    def __init__(self, vm_name, multipass_cmd):
        self.cmd = multipass_cmd
        self.vm_name = vm_name

    # Will retry to execute info() if SocketError occurs
    @retry_on_failure(ExceptionsToCheck=SocketError)
    def info(self):
        cmd = [self.cmd, "info", self.vm_name, "--format", "json"]
        out = subprocess.Popen(cmd, 
           stdout=subprocess.PIPE, 
           stderr=subprocess.PIPE)
        stdout,stderr = out.communicate()
        exitcode = out.wait()
        stderr_cleaned = stderr.decode(encoding="utf-8").strip().splitlines()
        if(exitcode != 0):
            # we raise a NameError if the VM doesn't exist
            if 'instance "{0}" does not exist'.format(self.vm_name) in stderr_cleaned:
                raise NameError("Multipass info command failed: {0}".format(stderr_cleaned[1]))
            if "Socket error" in stderr.decode(encoding="utf-8"):
                raise SocketError("Multipass info command failed: {0}".format(stderr_cleaned[0]))
            else:
                raise Exception("Multipass info command failed: {0}".format(stderr.decode(encoding="utf-8")))
        return json.loads(stdout)

    def delete(self, purge=False):
        cmd = [self.cmd, "delete", self.vm_name]
        if purge:
            cmd.append("--purge")
        out = subprocess.Popen(cmd, 
           stdout=subprocess.PIPE, 
           stderr=subprocess.PIPE)
        stdout,stderr = out.communicate()
        exitcode = out.wait()
        stderr_cleaned = stderr.decode(encoding="utf-8").strip().splitlines()
        if(exitcode != 0):
            # we raise a NameError if the VM doesn't exist
            if 'instance "{0}" does not exist'.format(self.vm_name) in stderr_cleaned:
                raise NameError(stderr_cleaned[1])
            else:
                raise Exception("Error deleting Multipass VM {0}\n {1}".format(
                    self.vm_name, stderr.decode(encoding="utf-8")
                    )
                )

    def shell(self):
        raise Exception("The shell command is not supported in the Multipass SDK. Consider using exec.")

    def exec(self, cmd_to_execute, working_directory=""):
        cmd = [self.cmd, "exec", self.vm_name]
        if working_directory:
          cmd += ["--working-directory", working_directory]

        cmd += ["--"]
        cmd += shlexsplit(cmd_to_execute)

        out = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout,stderr = out.communicate()

        exitcode = out.wait()
        if(exitcode != 0):
            raise Exception("Multipass exec command failed: {0}".format(stderr.decode(encoding="utf-8")))
        return stdout, stderr

    def stop(self):
        cmd = [self.cmd, "stop", self.vm_name]
        try:
            subprocess.check_output(cmd)
        except:
            raise Exception("Error stopping Multipass VM {0}".format(self.vm_name))

    def start(self):
        cmd = [self.cmd, "start", self.vm_name]
        try:
            subprocess.check_output(cmd)
        except:
            raise Exception("Error starting Multipass VM {0}".format(self.vm_name))

    def restart(self):
        cmd = [self.cmd, "restart", self.vm_name]
        try:
            subprocess.check_output(cmd)
        except:
            raise Exception("Error restarting Multipass VM {0}".format(self.vm_name))

class MultipassClient:
    """
    Multipass client
    """
    def __init__(self, multipass_cmd="multipass"):
        self.cmd = multipass_cmd

    def launch(self, vm_name=None, cpu=1, disk="5G", mem="1G", networks=[], image=None, cloud_init=None):
        if(not vm_name):
            # similar to Multipass's VM name generator
            vm_name = Haikunator().haikunate(token_length=0)
        cmd = [self.cmd, "launch", "-c", str(cpu), "-d", disk, "-n", vm_name, "-m", mem]
        if(cloud_init):
            cmd.append("--cloud-init")
            cmd.append(cloud_init)
        for network in networks:
            network_str = f"name={network['name']}"

            # Add optional parameters if they exist
            if 'mode' in network and network['mode']:
                network_str += f",mode={network['mode']}"

            if 'mac' in network and network['mac']:
                network_str += f",mac={network['mac']}"

            cmd.append("--network")
            cmd.append(network_str)
        if(image and not image == "ubuntu-lts"):
            cmd.append(image)
        try:
            subprocess.check_output(cmd)
        except:
            raise Exception("Error launching Multipass VM {0}".format(vm_name))
        return MultipassVM(vm_name, self.cmd)

    def transfer(self, src, dest):
        cmd = [self.cmd, "transfer", src, dest]
        try:
            subprocess.check_output(cmd)
        except:
            raise Exception("Multipass transfer command failed.")

    def get_vm(self, vm_name):
        return MultipassVM(vm_name, self.cmd)

    def purge(self):
        cmd = [self.cmd, "purge"]
        try:
            subprocess.check_output(cmd)
        except:
            raise Exception("Purge command failed.")

    def list(self):
        cmd = [self.cmd, "list", "--format", "json"]
        out = subprocess.Popen(cmd, 
           stdout=subprocess.PIPE, 
           stderr=subprocess.STDOUT)
        stdout,stderr = out.communicate()
        exitcode = out.wait()
        if(not exitcode == 0):
            raise Exception("Multipass list command failed: {0}".format(stderr))
        return json.loads(stdout)

    def find(self):
        cmd = [self.cmd, "find", "--format", "json"]
        out = subprocess.Popen(cmd, 
           stdout=subprocess.PIPE, 
           stderr=subprocess.STDOUT)
        stdout,stderr = out.communicate()
        exitcode = out.wait()
        if(not exitcode == 0):
            raise Exception("Multipass find command failed: {0}".format(stderr))
        return json.loads(stdout)

    def mount(self, src, target, mount_type='classic', uid_maps=[], gid_maps=[]):
        mount_options = ["--type", mount_type]
        for uid_map in uid_maps:
            mount_options.extend(["--uid-map", uid_map])
        for gid_map in gid_maps:
            mount_options.extend(["--gid-map", gid_map])
        cmd = [self.cmd, "mount"] + mount_options + [src, target]
        out = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        _,stderr = out.communicate()
        exitcode = out.wait()
        stderr_cleaned = stderr.decode(encoding="utf-8").splitlines()
        if(not exitcode == 0):
            for error_msg in stderr_cleaned:
                if 'is already mounted' in error_msg:
                    raise MountExistsError
            raise Exception("Multipass mount command failed: {0}".format(stderr.decode(encoding="utf-8").rstrip()))

    def umount(self, mount):
        cmd = [self.cmd, "umount", mount]
        out = subprocess.Popen(cmd, 
           stdout=subprocess.PIPE, 
           stderr=subprocess.PIPE)
        _,stderr = out.communicate()
        exitcode = out.wait()
        stderr_cleaned = stderr.decode(encoding="utf-8").splitlines()
        if(not exitcode == 0):
            for error_msg in stderr_cleaned:
                if 'is not mounted' in error_msg:
                    raise MountNonExistentError
            raise Exception("{}".format(stderr.decode(encoding="utf-8").rstrip()))

    def recover(self, vm_name):
        cmd = [self.cmd, "recover", vm_name]
        try:
            subprocess.check_output(cmd)
        except:
            raise Exception("Multipass recover command failed.")

    def suspend(self):
        cmd = [self.cmd, "suspend"]
        try:
            subprocess.check_output(cmd)
        except:
            raise Exception("Multipass suspend command failed.")

    def get(self, key):
        cmd = [self.cmd, "get", key]
        out = subprocess.Popen(cmd,
           stdout=subprocess.PIPE,
           stderr=subprocess.PIPE)
        stdout,stderr = out.communicate()
        exitcode = out.wait()
        if(exitcode != 0):
            raise Exception("Multipass get command failed: {0}".format(stderr.decode(encoding="utf-8")))
        # remove trailing "\r\n" when returning the stdout
        return stdout.rstrip()
