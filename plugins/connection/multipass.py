# (c) 2023 Kenneth KOFFI <@theko2fi>
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os
import pty
import shutil
import subprocess
import fcntl
import getpass

import ansible.constants as C
from ansible.errors import AnsibleError, AnsibleFileNotFound
import selectors
from ansible.module_utils.common.text.converters import to_text, to_bytes, to_native
from ansible.plugins.connection import ConnectionBase
from ansible.utils.display import Display
from ansible.utils.path import unfrackpath

display = Display()


class Connection(ConnectionBase):
    ''' Local based connections '''

    transport = 'theko2fi.multipass.multipass'
    has_pipelining = True

    def __init__(self, *args, **kwargs):

        super(Connection, self).__init__(*args, **kwargs)
        self.cwd = None
        #self.default_user = getpass.getuser()
        self.default_user = "ubuntu"

    def _connect(self):
        ''' connect to the multipass VM; nothing to do here '''

        # Because we haven't made any remote connection we're running as
        # the local user, rather than as whatever is configured in remote_user.
        self._play_context.remote_user = self.default_user

        if not self._connected:
            display.vvv(u"ESTABLISH LOCAL CONNECTION FOR USER: {0}".format(self._play_context.remote_user), host=self._play_context.remote_addr)
            self._connected = True
        return self

    def exec_command(self, cmd, in_data=None, sudoable=True):
        ''' run a command on the multipass VM '''

        super(Connection, self).exec_command(cmd, in_data=in_data, sudoable=sudoable)

        display.debug("in multipass.exec_command()")

        executable = C.DEFAULT_EXECUTABLE.split()[0] if C.DEFAULT_EXECUTABLE else None

        if not os.path.exists(to_bytes(executable, errors='surrogate_or_strict')):
            raise AnsibleError("failed to find the executable specified %s."
                               " Please verify if the executable exists and re-try." % executable)
        
        multipass_cmd = 'multipass exec {0} -- '.format(self.get_option('remote_addr'))

        display.vvv(u"EXEC {0}".format(to_text(multipass_cmd + cmd)), host=self._play_context.remote_addr)
        display.debug("opening command with Popen()")

        if isinstance(cmd, (str, bytes)):
            cmd = to_bytes(multipass_cmd + cmd)
        else:
            cmd = map(to_bytes, multipass_cmd + cmd)

        master = None
        stdin = subprocess.PIPE
        if sudoable and self.become and self.become.expect_prompt():
            # Create a pty if sudoable for privlege escalation that needs it.
            # Falls back to using a standard pipe if this fails, which may
            # cause the command to fail in certain situations where we are escalating
            # privileges or the command otherwise needs a pty.
            try:
                master, stdin = pty.openpty()
            except (IOError, OSError) as e:
                display.debug("Unable to open pty: %s" % to_native(e))

        p = subprocess.Popen(
            cmd,
            shell=isinstance(cmd, (str, bytes)),
            executable=executable,
            cwd=self.cwd,
            stdin=stdin,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        # if we created a master, we can close the other half of the pty now
        if master is not None:
            os.close(stdin)

        display.debug("done running command with Popen()")

        if self.become and self.become.expect_prompt() and sudoable:
            fcntl.fcntl(p.stdout, fcntl.F_SETFL, fcntl.fcntl(p.stdout, fcntl.F_GETFL) | os.O_NONBLOCK)
            fcntl.fcntl(p.stderr, fcntl.F_SETFL, fcntl.fcntl(p.stderr, fcntl.F_GETFL) | os.O_NONBLOCK)
            selector = selectors.DefaultSelector()
            selector.register(p.stdout, selectors.EVENT_READ)
            selector.register(p.stderr, selectors.EVENT_READ)

            become_output = b''
            try:
                while not self.become.check_success(become_output) and not self.become.check_password_prompt(become_output):
                    events = selector.select(self._play_context.timeout)
                    if not events:
                        stdout, stderr = p.communicate()
                        raise AnsibleError('timeout waiting for privilege escalation password prompt:\n' + to_native(become_output))

                    for key, event in events:
                        if key.fileobj == p.stdout:
                            chunk = p.stdout.read()
                        elif key.fileobj == p.stderr:
                            chunk = p.stderr.read()

                    if not chunk:
                        stdout, stderr = p.communicate()
                        raise AnsibleError('privilege output closed while waiting for password prompt:\n' + to_native(become_output))
                    become_output += chunk
            finally:
                selector.close()

            if not self.become.check_success(become_output):
                become_pass = self.become.get_option('become_pass', playcontext=self._play_context)
                os.write(master, to_bytes(become_pass, errors='surrogate_or_strict') + b'\n')

            fcntl.fcntl(p.stdout, fcntl.F_SETFL, fcntl.fcntl(p.stdout, fcntl.F_GETFL) & ~os.O_NONBLOCK)
            fcntl.fcntl(p.stderr, fcntl.F_SETFL, fcntl.fcntl(p.stderr, fcntl.F_GETFL) & ~os.O_NONBLOCK)

        display.debug("getting output with communicate()")
        stdout, stderr = p.communicate(in_data)
        display.debug("done communicating")

        # finally, close the other half of the pty, if it was created
        if master:
            os.close(master)

        display.debug("done with multipass.exec_command()")
        return (p.returncode, to_text(stdout, encoding='utf-8'), to_text(stderr, encoding='utf-8'))

    def put_file(self, in_path, out_path):
        ''' transfer a file from local to the multipass VM '''

        super(Connection, self).put_file(in_path, out_path)

        in_path = unfrackpath(in_path, basedir=self.cwd)
        #out_path = unfrackpath(out_path, basedir=self.cwd)

        display.vvv(u"PUT {0} TO {1}:{2}".format(in_path, self.get_option('remote_addr'), out_path), host=self._play_context.remote_addr)
        if not os.path.exists(to_bytes(in_path, errors='surrogate_or_strict')):
            raise AnsibleFileNotFound("file or module does not exist: {0}".format(to_native(in_path)))
        try:
            with open(in_path, 'rb') as filedata:
                transfer_process = subprocess.Popen(
                    ['multipass', 'transfer', '-', '{0}:{1}'.format(self.get_option('remote_addr'), out_path)],
                    stdin=filedata,
                    stdout=subprocess.PIPE
                )
                transfer_process.communicate()

        except shutil.Error:
            raise AnsibleError("failed to copy: {0} and {1} are the same".format(to_native(in_path), to_native(out_path)))
        except IOError as e:
            raise AnsibleError("failed to transfer file to {0}: {1}".format(to_native(out_path), to_native(e)))
        except Exception as e:
            raise AnsibleError("failed to transfer file {0} to {1}:{2}\nError: {3}".format(
                to_native(in_path), to_native(self.get_option('remote_addr')), to_native(out_path), to_native(e)
                )
            )

    def fetch_file(self, in_path, out_path):
        ''' fetch a file from the multipass VM to local -- for compatibility '''

        super(Connection, self).fetch_file(in_path, out_path)
        
        #in_path = unfrackpath(in_path, basedir=self.cwd)
        #out_path = unfrackpath(out_path, basedir=self.cwd)

        display.vvv("local src is: {}".format(out_path), host=self._play_context.remote_addr)

        display.vvv(u"FETCH {0}:{1} TO {2}".format(self.get_option('remote_addr'), in_path, out_path), host=self._play_context.remote_addr)

        try:
            cat_returncode, cat_stdout, cat_stderr = self.exec_command(cmd='cat {0}'.format(in_path))
            with open(out_path, 'wb') as filedata:
                filedata.write(cat_stdout)
        except Exception as e:
            raise AnsibleError("failed to transfer file {0}:{1} to {2}\nError: {3}".format(
                to_native(self.get_option('remote_addr')), to_native(in_path) , to_native(out_path), to_native(e)
                )
            )

    def close(self):
        ''' terminate the connection; nothing to do here '''
        self._connected = False



DOCUMENTATION = '''
author:
    - Kenneth KOFFI (@theko2fi)
name: theko2fi.multipass.multipass
short_description: Run tasks in Multipass virtual machines
description:
    - Run commands or put/fetch files to an existing multipass VM.
    - Uses the multipass CLI to execute commands in the virtual machine.
notes:
    - The C(theko2fi.multipass.multipass) connection plugin does not support using
      the ``remote_user`` and ``ansible_user`` variables to configure the remote
      user. Remote commands will often default to running as ``ubuntu`` user.
options:
    remote_addr:
        description:
            - The name of the VM you want to access.
        default: inventory_hostname
        vars:
            - name: inventory_hostname
            - name: ansible_host
            - name: ansible_multipass_host
'''

EXAMPLES = '''
# sample inventory.yml file where `foo` is the name of the Multipass VM:
all:
  hosts:
    foo:
      ansible_host: foo
      ansible_connection: theko2fi.multipass.multipass
      ansible_python_interpreter: /usr/bin/python3

# Execution: ansible-playbook -i inventory.yml playbook.yml
# The playbook tasks will get executed on the multipass VM
'''