#!/usr/bin/python
#
# Copyright (c) 2022, Kenneth KOFFI <@theko2fi>
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import absolute_import, division, print_function
__metaclass__ = type

import os
import base64
from io import BytesIO, open as iopen
from ansible.module_utils.common.text.converters import to_bytes, to_native
import subprocess
from ansible.module_utils.basic import AnsibleModule
from ansible_collections.theko2fi.multipass.plugins.module_utils.multipass import retry_on_failure
from ansible_collections.theko2fi.multipass.plugins.module_utils.errors import (
    SocketError,
    MultipassFileTransferError,
    MultipassContentTransferError
  )


def put_file(remote_addr, in_path, out_path):
    ''' transfer a file from local to the multipass VM '''

    if not os.path.exists(to_bytes(in_path, errors='surrogate_or_strict')):
        raise FileNotFoundError("file or module does not exist: {0}".format(to_native(in_path)))
    
    @retry_on_failure(ExceptionsToCheck=SocketError) #retry on SocketError
    def low_level_code_put_file(in_path, remote_addr, out_path):
      with open(in_path, 'rb') as filedata:
          transfer_process = subprocess.Popen(
              ['multipass', 'transfer', '-', '{0}:{1}'.format(remote_addr, out_path)],
              stdin=filedata,
              stdout=subprocess.PIPE,
              stderr=subprocess.PIPE
          )
          stdout, stderr = transfer_process.communicate()
          exitcode = transfer_process.wait()
          if(exitcode != 0):
            if "Socket error" in stderr.decode(encoding="utf-8"):
              raise SocketError(stderr.decode(encoding="utf-8").strip())
            else:
              raise MultipassFileTransferError(stderr.decode(encoding="utf-8").strip())
      return exitcode
    
    try:
        # This function call actually put file inside the target VM
        low_level_code_put_file(in_path, remote_addr, out_path)
    except Exception as e:
        raise MultipassFileTransferError("failed to transfer file {0} to {1}:{2}\nError: {3}".format(
            to_native(in_path), to_native(remote_addr), to_native(out_path), to_native(e)
            )
        )
    


def put_content(remote_addr, in_content, out_path):
    ''' transfer a local content to the multipass VM '''

    @retry_on_failure(ExceptionsToCheck=SocketError) #retry on SocketError
    def _low_level_code_put_content(remote_addr, out_path, in_content):
      transfer_process = subprocess.Popen(
          ['multipass', 'transfer', '-', '{0}:{1}'.format(remote_addr, out_path)],
          stdin=subprocess.PIPE,
          stdout=subprocess.PIPE,
          stderr=subprocess.PIPE
      )
      _, stderr = transfer_process.communicate(input=in_content)
      exitcode = transfer_process.wait()
      if(exitcode != 0):
        if "Socket error" in stderr.decode(encoding="utf-8"):
          raise SocketError(stderr.decode(encoding="utf-8").strip())
        else:  
          raise MultipassContentTransferError(stderr.decode(encoding="utf-8").strip())
      return exitcode

    try:
      _low_level_code_put_content(remote_addr=remote_addr, out_path=out_path, in_content=in_content)
    except Exception as e:
        raise MultipassFileTransferError("failed to transfer content {0} to {1}:{2}\nError: {3}".format(
            to_native(in_content), to_native(remote_addr), to_native(out_path), to_native(e)
            )
        )

def extract_remotefile(vm_name, filepath):
  cmd = ['multipass', 'exec', vm_name, '--', 'cat', filepath]
  with subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE) as proc:
    return BytesIO(proc.stdout.read())

    

def are_fileobjs_equal(f1, f2):
  '''Given two (buffered) file objects, compare their contents.'''
  blocksize = 65536
  b1buf = b''
  b2buf = b''
  while True:
      if f1 and len(b1buf) < blocksize:
          f1b = f1.read(blocksize)
          if not f1b:
              # f1 is EOF, so stop reading from it
              f1 = None
          b1buf += f1b
      if f2 and len(b2buf) < blocksize:
          f2b = f2.read(blocksize)
          if not f2b:
              # f2 is EOF, so stop reading from it
              f2 = None
          b2buf += f2b
      if not b1buf or not b2buf:
          # At least one of f1 and f2 is EOF and all its data has
          # been processed. If both are EOF and their data has been
          # processed, the files are equal, otherwise not.
          return not b1buf and not b2buf
      # Compare the next chunk of data, and remove it from the buffers
      buflen = min(len(b1buf), len(b2buf))
      if b1buf[:buflen] != b2buf[:buflen]:
          return False
      b1buf = b1buf[buflen:]
      b2buf = b2buf[buflen:]


def transfer_content_into_vm(vm, remote_file, content, dest)->bool:
  # compare local content and remote file object for idempotency
  is_equal = are_fileobjs_equal(f1=remote_file, f2=BytesIO(content))
  
  if not is_equal:
    put_content(remote_addr=vm, in_content=content, out_path=dest)
    changed = True
  else:
    changed = False

  return changed

def transfer_file_into_vm(vm, remote_file, src, dest)->bool:
  # compare local file and remote file objects for idempotency
  with open(src, 'rb') as local_file:
    is_equal = are_fileobjs_equal(f1=remote_file, f2=local_file)
  
  if not is_equal:
    put_file(remote_addr=vm, in_path=src, out_path=dest)
    changed = True
  else:
    changed = False

  return changed


def main():
    module = AnsibleModule(
    	argument_spec=dict(
    	    name = dict(required=True, type=str),
    	    src = dict(required=False, type='path'),
          content = dict(required=False, type=str),
          content_is_b64=dict(type='bool', default=False),
    	    dest = dict(required=True, type=str)
        ),
      mutually_exclusive=[('src', 'content')]
    )
    
    vm = module.params.get('name')
    src = module.params.get('src')
    content = module.params.get('content')
    dest = module.params.get('dest')
    
    if content is not None:
      if module.params['content_is_b64']:
        try:
            content = base64.b64decode(content)
        except Exception as e:  # depending on Python version and error, multiple different exceptions can be raised
            module.fail_json('Cannot Base64 decode the content option: {0}'.format(e))
      else:
        content = to_bytes(content)
    
    try:
      # fetch remote file from the VM
      remote_file = extract_remotefile(vm_name=vm, filepath=dest)

      if content is not None:
        changed = transfer_content_into_vm(vm=vm, remote_file=remote_file, content=content, dest=dest)
      else:
        changed = transfer_file_into_vm(vm=vm, remote_file=remote_file, src=src, dest=dest)

      result = dict(changed=changed)
      
      module.exit_json(**result)
    except Exception as e:
      module.fail_json(msg=str(e))

if __name__ == "__main__":
	main()


DOCUMENTATION = '''
---
module: multipass_vm_transfer_into

short_description: Copy a file into a Multipass virtual machine

version_added: 0.2.0

description:
  - Copy a file into a Multipass virtual machine.
  - Similar to C(multipass transfer).

options:
  name:
    description:
      - The name of the virtual machine to copy files to.
    type: str
    required: true
  src:
    description:
      - Path to a file on the managed node.
      - Mutually exclusive with O(content). One of O(content) and O(src) is required.
    type: str
  content:
    description:
      - The file's content.
      - If you plan to provide binary data, provide it pre-encoded to base64, and set O(content_is_b64=true).
      - Mutually exclusive with O(src). One of O(content) and O(src) is required.
    type: str
  content_is_b64:
    description:
      - If set to V(true), the content in O(content) is assumed to be Base64 encoded and
        will be decoded before being used.
      - To use binary O(content), it is better to keep it Base64 encoded and let it
        be decoded by this option. Otherwise you risk the data to be interpreted as
        UTF-8 and corrupted.
    type: bool
    default: false
  dest:
    description:
      - Path to a file inside the Multipass virtual machine.
      - Must be an absolute path.
    type: str
    required: true

author:
  - "Kenneth KOFFI (@theko2fi)"
'''

EXAMPLES = '''
- name: Copy a file into the VM
  theko2fi.multipass.multipass_vm_transfer_into:
    name: foo
    src: /home/user/data.txt
    dest: /home/ubuntu/input.txt

- name: Copy a content into the VM
  theko2fi.multipass.multipass_vm_transfer_into:
    name: foo
    content: "Hello World!"
    dest: /home/ubuntu/input.txt

- name: Copy a file into the VM (ignore errors)
  theko2fi.multipass.multipass_vm_transfer_into:
    name: foo
    src: /home/user/data.txt
    dest: /input.txt
  ignore_errors: true
'''